"""
Intake API — kanaal-agnostische lead-intake voor niet-WhatsApp-kanalen (increment 2).

2a: POST /intake/web-form. Een publiek (niet-geauthenticeerd) endpoint waar een
website-formulier een lead naartoe stuurt. De organisatie wordt bepaald via een
expliciete `org_id` in de body (gevalideerd tegen de DB → 404; géén org raden).
Alle persoonsgegevens in de POST-body, nooit in de URL (dossier §7.4).

De lead loopt door exact dezelfde pipeline als WhatsApp: gedeelde intake-helper
(Contact + Conversation) → deterministische score op het Contact → CRM-sync (Airtable)
→ agency-notificatie. Een web-form is één gestructureerde inzending (geen ≥3-berichten-
gesprek), dus we scoren/synchroniseren direct i.p.v. de WhatsApp-verrijkingsgate te volgen.
"""
from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.conversation import Organization, Conversation, Message, Contact, CrmSyncLog
from app.services.lead_intake_service import (
    create_or_update_conversation,
    get_or_create_web_chat_conversation,
)
from app.services.crm_sync_service import CrmSyncService
from app.services.identity_service import compute_lead_score, normalize_email
from app.services.email_service import send_lead_notification
from app.services.ai_service import AIService, CLOSING_TAG
from app.services.whatsapp_service import WhatsAppService

router = APIRouter(prefix="/intake", tags=["intake"])


class WebFormIn(BaseModel):
    """Velden van een website-lead. naam/e-mail + org_id verplicht; de rest optioneel.
    intentie/urgentie/gewenste_datum mogen door rijkere sectorformulieren meegestuurd
    worden en voeden de deterministische score; ontbreken ze, dan gelden de defaults."""
    org_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    email: str = Field(..., min_length=1)
    phone: Optional[str] = None
    company: Optional[str] = None
    sector: Optional[str] = None
    message: Optional[str] = None
    intentie: Optional[str] = None
    urgentie: Optional[str] = None
    gewenste_datum: Optional[str] = None


class WebFormOut(BaseModel):
    ok: bool
    conversation_id: str
    contact_id: Optional[str]
    score: Optional[str]


def _build_lead(form: WebFormIn) -> dict:
    """Zet de formuliervelden om in de lead-dict die de score + CRM-sync verwachten.
    Default-intentie 'Afspraak' (wie een webformulier invult, wil contact) → zonder
    urgentie/datum levert dat 'lauw' op; rijkere formulieren kunnen het overschrijven."""
    samenvatting_parts = [p for p in (form.message, f"Bedrijf: {form.company}" if form.company else None) if p]
    return {
        "naam": form.name,
        "adres": None,
        "email": form.email,
        "type_werk": form.message or form.sector or None,
        "gewenste_datum": form.gewenste_datum,
        "urgentie": form.urgentie,
        "intentie": form.intentie or "Afspraak",
        "samenvatting": " — ".join(samenvatting_parts) or f"Webformulier-aanvraag ({form.sector or 'algemeen'})",
        # Een web-formulier is een eenmalige inzending die de agency moet opvolgen (terugbellen/
        # mailen). Met het gesprek op 'closed' levert dit Airtable-status 'Op te volgen' op
        # (zie _pipeline_status) i.p.v. eeuwig 'Nieuw'.
        "opvolging_nodig": True,
        "opvolg_reden": "Web-formulier-aanvraag — opvolgen door agency.",
        "opvolg_datum": None,
    }


def _message_content(form: WebFormIn) -> str:
    parts = []
    if form.message:
        parts.append(form.message)
    if form.company:
        parts.append(f"Bedrijf: {form.company}")
    if form.sector:
        parts.append(f"Sector: {form.sector}")
    return "\n".join(parts) or "Aanvraag via webformulier"


@router.post("/web-form", response_model=WebFormOut)
async def web_form_intake(form: WebFormIn, db: AsyncSession = Depends(get_db)):
    """Verwerk een website-formulier-lead end-to-end (zie module-docstring)."""
    # Org expliciet bepalen — nooit raden. Onbekende org_id → 404.
    org = (await db.execute(
        select(Organization).where(Organization.id == form.org_id)
    )).scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Onbekende organisatie.")

    # E-mail server-side valideren (we gebruiken geen EmailStr om geen extra dependency
    # toe te voegen; normalize_email dekt lowercase/trim + basischeck op '@').
    if normalize_email(form.email) is None:
        raise HTTPException(status_code=422, detail="Ongeldig e-mailadres.")

    # 1. Contact + Conversation via de gedeelde helper (kanaal-overschrijdende identiteit,
    #    incl. eventuele merge wanneer telefoon én e-mail naar verschillende contacten wijzen).
    merged_conv_ids: list = []
    conversation = await create_or_update_conversation(
        db, org,
        channel="web_form", name=form.name, email=str(form.email), phone=form.phone,
        merged_out=merged_conv_ids, reuse_any_status=True,
    )
    # Eenmalige, volledige inzending → geen lopend gesprek. Meteen afsluiten: telt niet als
    # actief gesprek en levert (met opvolging_nodig in _build_lead) Airtable-status
    # 'Op te volgen' op i.p.v. eeuwig 'Nieuw'. Een herinzending hergebruikt dit gesprek
    # (reuse_any_status) en upsert hetzelfde Airtable-record (Bron ID=contact.id).
    conversation.status = "closed"

    # 2. Inkomend bericht bewaren (voedt dashboard + notificatie-preview).
    db.add(Message(
        id=str(uuid.uuid4()),
        conversation_id=conversation.id,
        direction="inbound",
        content=_message_content(form),
    ))
    await db.commit()

    # 3. Deterministische score op het Contact (de notificatie leest 'm daar).
    lead = _build_lead(form)
    score, reason = compute_lead_score(lead)
    contact = None
    if conversation.contact_id:
        contact = (await db.execute(
            select(Contact).where(Contact.id == conversation.contact_id)
        )).scalar_one_or_none()
        if contact:
            contact.score = score
            contact.score_reason = reason
            await db.commit()

    crm = CrmSyncService(db)

    # 4. Verweesde Airtable-records opruimen als er een merge plaatsvond.
    if merged_conv_ids:
        await crm.cleanup_merged_records(conversation, merged_conv_ids)

    # 5. CRM-sync DIRECT (geen ≥3-berichten-gate; upsert op Bron ID=contact.id → idempotent).
    #    Bestaand log opzoeken voor upsert (één record per gesprek).
    existing_log = (await db.execute(
        select(CrmSyncLog).where(CrmSyncLog.conversation_id == conversation.id)
    )).scalar_one_or_none()
    existing_record_id = None
    existing_log_id = None
    if existing_log:
        existing_log_id = existing_log.id
        if (existing_log.external_id or "").startswith("rec"):
            existing_record_id = existing_log.external_id
    await crm.sync(
        conversation=conversation, org=org,
        existing_record_id=existing_record_id, existing_log_id=existing_log_id, lead=lead,
    )

    # 6. Agency-notificatie (faalt stil als Resend niet geconfigureerd is).
    await send_lead_notification(conversation=conversation, db=db)

    return WebFormOut(
        ok=True,
        conversation_id=conversation.id,
        contact_id=conversation.contact_id,
        score=score,
    )


# ─── Web-chat (2c) ──────────────────────────────────────────────────────────────

class WebChatIn(BaseModel):
    """Eén beurt in een web-chatsessie. session_id houdt het gesprek + geheugen vast;
    name/email optioneel (de bezoeker mag anoniem starten)."""
    org_id: str = Field(..., min_length=1)
    session_id: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    name: Optional[str] = None
    email: Optional[str] = None


class WebChatOut(BaseModel):
    reply: str
    closed: bool
    session_id: str


@router.post("/web-chat", response_model=WebChatOut)
async def web_chat_intake(form: WebChatIn, db: AsyncSession = Depends(get_db)):
    """
    Conversationele web-chat: dezelfde AI-lus (tool-use + afspraken) als WhatsApp, maar
    sessie-gekeyd en SYNCHROON antwoordend (de client wacht op de reply i.p.v. push).
    Spiegelt process_incoming_message: bericht opslaan → AI-antwoord → verrijking/score →
    bij [GESPREK_AFGEROND] afsluiten + notificatie → CRM-sync (≥3-gate, zoals WhatsApp).
    """
    org = (await db.execute(
        select(Organization).where(Organization.id == form.org_id)
    )).scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Onbekende organisatie.")
    if form.email and normalize_email(form.email) is None:
        raise HTTPException(status_code=422, detail="Ongeldig e-mailadres.")

    conversation = await get_or_create_web_chat_conversation(
        db, org, session_id=form.session_id, name=form.name, email=form.email,
    )

    wa = WhatsAppService(db)
    ai = AIService(db)

    await wa.save_message(conversation.id, "inbound", form.message)
    reply = await ai.generate_reply(conversation=conversation, incoming_message=form.message)

    closed = CLOSING_TAG in reply
    clean_reply = reply.replace(CLOSING_TAG, "").strip()
    await wa.save_message(conversation.id, "outbound", clean_reply, ai_generated=True)

    # Verrijking/scoring + CRM-sync gaten op ≥3 berichten (zoals WhatsApp) — None = nog te vroeg.
    lead = await wa.extract_and_enrich(conversation)
    if closed:
        conversation.status = "closed"
        await db.commit()
        await db.refresh(conversation)
        await send_lead_notification(conversation=conversation, db=db)
    await wa.sync_to_crm(conversation=conversation, lead=lead)

    return WebChatOut(reply=clean_reply, closed=closed, session_id=form.session_id)
