"""
E-mail-intake Service — inkomende e-mail → lead (increment 2b, Resend Inbound).

Flow (achtergrondtaak vanuit POST /webhooks/email):
  1. org bepalen uit het To-adres (plus-addressing intake+{org_id}@{domein}).
  2. body ophalen via de Resend Received-Emails API (de webhook bevat enkel metadata).
  3. loop-/spam-guard (Auto-Submitted/List-*/eigen afzender) → negeren.
  4. Contact + Conversation via de gedeelde helper (channel="email"), bericht opslaan.
  5. Haiku-extractie op onderwerp+body → score op het Contact → CRM-sync (direct, geen
     ≥3-gate) → agency-notificatie. Merge + orphan-cleanup komen mee via de plumbing.
  6. Ontbreken naam of type werk → exact ÉÉN opvolgmail met gerichte vragen.

Alles is niet-kritisch defensief: een fout in een niet-essentiële stap mag de lead-capture
niet ongedaan maken; we loggen en gaan door.
"""
from __future__ import annotations

import logging
import re
import uuid
from email.utils import getaddresses, parseaddr
from typing import Optional

import httpx
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import AsyncSessionLocal
from app.models.conversation import Organization, Conversation, Message, Contact, CrmSyncLog
from app.services.crm_sync_service import CrmSyncService
from app.services.email_service import send_followup_email, send_lead_notification
from app.services.identity_service import compute_lead_score, normalize_email
from app.services.lead_intake_service import create_or_update_conversation

settings = get_settings()
logger = logging.getLogger(__name__)

RESEND_RECEIVING_URL = "https://api.resend.com/emails/receiving"

# Verplichte velden vóór een lead "compleet" is; ontbreken ze → één opvolgmail.
_REQUIRED_FIELDS = ("naam", "type_werk")


def extract_org_id(to_list: list, domain: Optional[str]) -> Optional[str]:
    """
    Haal org_id uit een plus-geadresseerd intake-adres: intake+{org_id}@{domein}.
    Domein wordt case-insensitief vergeleken; de org_id-case blijft behouden.
    """
    if not domain:
        return None
    for _, addr in getaddresses([str(a) for a in to_list]):
        if "@" not in addr:
            continue
        local, _, dom = addr.partition("@")
        if dom.lower() != domain.lower():
            continue
        if "+" in local:
            org_id = local.split("+", 1)[1].strip()
            if org_id:
                return org_id
    return None


def is_auto_or_list_mail(headers: Optional[dict]) -> bool:
    """True voor autoreplies/mailinglijsten (Auto-Submitted/List-*/Precedence) → negeren,
    zodat onze opvolgmail geen lead/loop triggert."""
    if not headers:
        return False
    lower = {str(k).lower(): str(v or "") for k, v in headers.items()}
    auto = lower.get("auto-submitted", "").strip().lower()
    if auto and auto != "no":
        return True
    if any(k.startswith("list-") for k in lower):
        return True
    if lower.get("precedence", "").strip().lower() in ("bulk", "auto_reply", "junk", "list"):
        return True
    return False


def _html_to_text(html: str) -> str:
    if not html:
        return ""
    text = re.sub(r"(?is)<(script|style).*?</\1>", " ", html)
    text = re.sub(r"(?i)<br\s*/?>", "\n", text)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"[ \t]+", " ", text).strip()


def _has_value(val) -> bool:
    if val is None:
        return False
    s = str(val).strip()
    return bool(s) and s.lower() not in ("null", "none")


async def _fetch_email_body(email_id: str) -> Optional[dict]:
    """Haal de volledige inkomende e-mail op (de webhook levert enkel metadata)."""
    if not settings.resend_api_key:
        logger.warning("E-mail-intake: RESEND_API_KEY niet gezet — kan body niet ophalen.")
        return None
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{RESEND_RECEIVING_URL}/{email_id}",
                headers={"Authorization": f"Bearer {settings.resend_api_key}"},
            )
        if resp.status_code != 200:
            logger.warning("Resend receiving GET %s gaf %s: %s", email_id, resp.status_code, resp.text[:200])
            return None
        return resp.json()
    except Exception as e:
        logger.error("E-mail-intake: ophalen body %s faalde: %s", email_id, e)
        return None


async def process_inbound_email(*, email_id: str, to_list: list, from_addr: Optional[str], subject: str) -> None:
    """Volledige verwerking van één inkomende e-mail (zie module-docstring)."""
    org_id = extract_org_id(to_list, settings.email_intake_domain)
    if not org_id:
        logger.info("E-mail-intake: geen org_id in To=%s — genegeerd.", to_list)
        return

    # Goedkope loop-guard op de afzender uit de webhook, vóór we de body fetchen.
    intake_addr = parseaddr(settings.email_intake_from)[1].lower()
    if parseaddr(from_addr or "")[1].lower() == intake_addr and intake_addr:
        logger.info("E-mail-intake: eigen afzender — genegeerd (loop-guard).")
        return

    body = await _fetch_email_body(email_id)
    if not body:
        return
    if is_auto_or_list_mail(body.get("headers")):
        logger.info("E-mail-intake: auto/list-mail — genegeerd.")
        return

    sender_name, sender_email = parseaddr(body.get("from") or from_addr or "")
    sender_name = sender_name or None
    if not normalize_email(sender_email):
        logger.info("E-mail-intake: geen geldig afzenderadres — genegeerd.")
        return

    text = body.get("text") or _html_to_text(body.get("html") or "")
    content = f"{subject}\n\n{text}".strip() if subject else text

    async with AsyncSessionLocal() as db:
        try:
            org = (await db.execute(
                select(Organization).where(Organization.id == org_id)
            )).scalar_one_or_none()
            if not org:
                logger.info("E-mail-intake: onbekende org %s — genegeerd.", org_id)
                return

            merged_conv_ids: list = []
            conversation = await create_or_update_conversation(
                db, org, channel="email", name=sender_name, email=sender_email,
                merged_out=merged_conv_ids,
            )

            msg = Message(
                id=str(uuid.uuid4()), conversation_id=conversation.id,
                direction="inbound", content=content or "(lege e-mail)",
            )
            db.add(msg)
            await db.commit()

            crm = CrmSyncService(db)
            lead = await crm._extract_lead_data([msg])
            # Het kanaal kent de afzender met zekerheid — vul aan waar de extractie faalt.
            if not _has_value(lead.get("email")):
                lead["email"] = sender_email
            if not _has_value(lead.get("naam")) and sender_name:
                lead["naam"] = sender_name

            score, reason = compute_lead_score(lead)
            if conversation.contact_id:
                contact = (await db.execute(
                    select(Contact).where(Contact.id == conversation.contact_id)
                )).scalar_one_or_none()
                if contact:
                    contact.score = score
                    contact.score_reason = reason
                    await db.commit()

            if merged_conv_ids:
                await crm.cleanup_merged_records(conversation, merged_conv_ids)

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

            await send_lead_notification(conversation=conversation, db=db)
            await _maybe_send_followup(db, conversation, lead, sender_email)

        except Exception as e:
            logger.error("❌ E-mail-intake fout voor %s: %s", sender_email, e)
            raise


async def _maybe_send_followup(db: AsyncSession, conversation: Conversation, lead: dict, to_email: str) -> None:
    """
    Stuur EXACT één opvolgmail met gerichte vragen als naam of type werk ontbreekt.
    "Max één" wordt geteld via het aantal uitgaande berichten op dit gesprek (≥1 → niets).
    Deterministisch (geen extra LLM-call): de vragen volgen rechtstreeks uit wat ontbreekt.
    """
    missing = [f for f in _REQUIRED_FIELDS if not _has_value(lead.get(f))]
    if not missing:
        return

    out_count = await db.scalar(
        select(func.count(Message.id)).where(
            Message.conversation_id == conversation.id,
            Message.direction == "outbound",
        )
    )
    if out_count and out_count > 0:
        return  # er ging al een opvolgmail uit

    vragen = []
    if "naam" in missing:
        vragen.append("• Met wie hebben we het genoegen? (uw naam)")
    if "type_werk" in missing:
        vragen.append("• Waarmee kunnen we u precies helpen? (een korte omschrijving)")
    body = (
        "Bedankt voor uw bericht!\n\n"
        "Om u snel en goed verder te helpen, ontbreken nog enkele gegevens:\n\n"
        + "\n".join(vragen)
        + "\n\nU kunt gewoon op deze e-mail antwoorden.\n\nMet vriendelijke groeten"
    )

    sent = await send_followup_email(to_email, "We hebben nog enkele gegevens nodig", body)
    if sent:
        db.add(Message(
            id=str(uuid.uuid4()), conversation_id=conversation.id,
            direction="outbound", content=body, ai_generated=True,
        ))
        await db.commit()
