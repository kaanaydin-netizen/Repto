"""
WhatsApp webhook handler — Meta WhatsApp Cloud API.

- GET  /webhooks/whatsapp : verificatie-handshake (hub.challenge) bij het koppelen
                            van de webhook in het Meta App-dashboard.
- POST /webhooks/whatsapp : ontvangt inkomende berichten (en statusupdates) als
                            geneste JSON en triggert de AI-verwerking op de achtergrond.

De inkomende DB-sessie wordt niet doorgegeven aan de background task; die opent een
eigen sessie (de request-sessie is al gesloten tegen de tijd dat de task draait).
"""
from __future__ import annotations
import hashlib
import hmac
import json
import logging

from fastapi import APIRouter, Request, BackgroundTasks, HTTPException
from fastapi.responses import PlainTextResponse

from app.config import get_settings
from app.database import AsyncSessionLocal
from app.services.whatsapp_service import WhatsAppService
from app.services.ai_service import AIService
from app.services.email_service import send_lead_notification

settings = get_settings()
logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhooks", tags=["webhooks"])

CLOSING_TAG = "[GESPREK_AFGEROND]"


# ─── GET: verificatie-handshake ────────────────────────────────────────────────

@router.get("/whatsapp")
async def verify_webhook(request: Request):
    """
    Meta roept dit endpoint één keer aan bij het instellen van de webhook.
    Bij een geldige hub.verify_token moeten we hub.challenge platte tekst teruggeven.
    """
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == settings.whatsapp_verify_token:
        logger.info("WhatsApp webhook-verificatie geslaagd.")
        return PlainTextResponse(content=challenge or "")

    logger.warning("WhatsApp webhook-verificatie mislukt (mode=%s).", mode)
    raise HTTPException(status_code=403, detail="Verificatie mislukt")


# ─── Signature-verificatie (optioneel) ─────────────────────────────────────────

def _signature_valid(raw_body: bytes, signature_header: str | None) -> bool:
    """
    Controleer de X-Hub-Signature-256 header tegen het app-secret.
    Alleen actief als WHATSAPP_APP_SECRET is geconfigureerd.
    """
    if not settings.whatsapp_app_secret:
        return True  # verificatie uitgeschakeld
    if not signature_header or not signature_header.startswith("sha256="):
        return False
    expected = hmac.new(
        settings.whatsapp_app_secret.encode(),
        raw_body,
        hashlib.sha256,
    ).hexdigest()
    received = signature_header.split("=", 1)[1]
    return hmac.compare_digest(expected, received)


# ─── POST: inkomende berichten ─────────────────────────────────────────────────

@router.post("/whatsapp")
async def receive_message(request: Request, background_tasks: BackgroundTasks):
    """
    Ontvangt de geneste JSON-payload van de Meta Cloud API. We bevestigen altijd
    snel met 200 OK (Meta verwacht dit binnen enkele seconden) en verwerken de
    eigenlijke berichten op de achtergrond.
    """
    raw_body = await request.body()

    # Optionele integriteitscontrole
    if not _signature_valid(raw_body, request.headers.get("X-Hub-Signature-256")):
        logger.warning("Ongeldige X-Hub-Signature-256 — payload geweigerd.")
        raise HTTPException(status_code=403, detail="Ongeldige signature")

    try:
        data = json.loads(raw_body or b"{}")
    except json.JSONDecodeError:
        logger.warning("Webhook-payload is geen geldige JSON.")
        return {"status": "ignored"}

    if data.get("object") != "whatsapp_business_account":
        return {"status": "ignored"}

    queued = 0
    for entry in data.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {}) or {}
            metadata = value.get("metadata", {}) or {}
            phone_number_id = metadata.get("phone_number_id")

            # Statusupdates (delivered/read/sent) bevatten geen "messages" → negeren
            messages = value.get("messages") or []
            if not messages or not phone_number_id:
                continue

            # Profielnaam staat los van de berichten, in contacts[]
            contacts = value.get("contacts") or []
            contact_name = None
            if contacts:
                contact_name = (contacts[0].get("profile") or {}).get("name")

            for msg in messages:
                from_phone = msg.get("from")
                msg_id = msg.get("id")
                msg_type = msg.get("type")

                # Alleen tekst verwerken; andere types (image/audio/…) loggen we
                if msg_type != "text":
                    logger.info(
                        "Niet-tekst bericht (%s) van %s genegeerd.", msg_type, from_phone
                    )
                    continue

                body = (msg.get("text") or {}).get("body", "").strip()
                if not from_phone or not body:
                    continue

                background_tasks.add_task(
                    process_incoming_message,
                    phone_number_id=phone_number_id,
                    from_phone=from_phone,
                    body=body,
                    contact_name=contact_name,
                    message_id=msg_id,
                )
                queued += 1

    return {"status": "ok", "queued": queued}


async def process_incoming_message(
    phone_number_id: str,
    from_phone: str,
    body: str,
    contact_name: str | None,
    message_id: str | None,
) -> None:
    """
    Volledige verwerking van een inkomend WhatsApp-bericht:
    1. Eigen DB-sessie openen
    2. Gesprek ophalen of aanmaken (org wordt opgezocht via phone_number_id)
    3. Inkomend bericht opslaan
    4. AI-antwoord genereren
    5. Detecteer [GESPREK_AFGEROND] tag → gesprek afsluiten + e-mailnotificatie
    6. Antwoord versturen via Meta (zonder de tag), vanaf hetzelfde afzendernummer
    7. Uitgaand bericht opslaan
    8. CRM synchroniseren naar Airtable
    """
    async with AsyncSessionLocal() as db:
        wa_service = WhatsAppService(db)
        ai_service = AIService(db)

        try:
            conversation = await wa_service.get_or_create_conversation(
                phone_number_id=phone_number_id,
                contact_phone=from_phone,
                contact_name=contact_name,
            )

            await wa_service.save_message(
                conversation_id=conversation.id,
                direction="inbound",
                content=body,
                wa_message_id=message_id,
            )

            reply = await ai_service.generate_reply(
                conversation=conversation,
                incoming_message=body,
            )

            conversation_closed = CLOSING_TAG in reply
            clean_reply = reply.replace(CLOSING_TAG, "").strip()

            if conversation_closed:
                conversation.status = "closed"
                await db.commit()
                await db.refresh(conversation)
                # E-mailnotificatie naar agency (faalt stil als niet geconfigureerd)
                await send_lead_notification(conversation=conversation, db=db)

            # Antwoord versturen via Meta, vanaf het nummer waarop het binnenkwam
            await wa_service.send_message(
                to_phone=from_phone,
                message=clean_reply,
                phone_number_id=phone_number_id,
            )

            await wa_service.save_message(
                conversation_id=conversation.id,
                direction="outbound",
                content=clean_reply,
                ai_generated=True,
            )

            await wa_service.sync_to_crm(conversation=conversation)

        except Exception as e:
            logger.error("❌ Fout bij verwerking bericht van %s: %s", from_phone, e)
            raise
