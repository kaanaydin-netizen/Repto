"""
WhatsApp webhook handler — ontvangt inkomende berichten van Twilio WhatsApp API
en triggert de AI-verwerking op de achtergrond.

Fix v2: background task maakt eigen DB-sessie aan (request-sessie is al gesloten
        tegen de tijd dat de background task runt).
"""
from __future__ import annotations
import logging
from fastapi import APIRouter, Request, BackgroundTasks
from app.database import AsyncSessionLocal
from app.services.whatsapp_service import WhatsAppService
from app.services.ai_service import AIService
from app.services.email_service import send_lead_notification

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhooks", tags=["webhooks"])



@router.post("/whatsapp")
async def receive_message(
    request: Request,
    background_tasks: BackgroundTasks,
):
    """
    Ontvangt inkomende WhatsApp-berichten via Twilio.
    Twilio stuurt form-data (application/x-www-form-urlencoded).
    """
    form = await request.form()

    # Twilio velden uitlezen
    from_phone   = str(form.get("From", "")).replace("whatsapp:", "")  # strip prefix
    to_phone     = str(form.get("To", ""))                             # Twilio sandbox nummer (incl. prefix)
    body         = str(form.get("Body", "")).strip()
    contact_name = form.get("ProfileName")
    message_sid  = form.get("MessageSid")

    # Lege berichten negeren
    if not from_phone or not body:
        return {"status": "ok"}

    # Verwerk asynchroon op de achtergrond (blokkeert Twilio niet)
    # ⚠️  Geen db-sessie meegeven — background task opent zijn eigen sessie
    background_tasks.add_task(
        process_incoming_message,
        from_phone=from_phone,
        to_phone=to_phone,
        body=body,
        contact_name=contact_name,
        message_sid=message_sid,
    )

    # Twilio verwacht een lege 200 OK (of TwiML) — wij sturen leeg terug
    return {}


CLOSING_TAG = "[GESPREK_AFGEROND]"


async def process_incoming_message(
    from_phone: str,
    to_phone: str,
    body: str,
    contact_name: str | None,
    message_sid: str | None,
) -> None:
    """
    Volledige verwerking van een inkomend WhatsApp-bericht:
    1. Eigen DB-sessie openen
    2. Gesprek ophalen of aanmaken
    3. Inkomend bericht opslaan
    4. AI-antwoord genereren
    5. Detecteer [GESPREK_AFGEROND] tag → gesprek afsluiten
    6. Antwoord versturen via Twilio (zonder de tag)
    7. Uitgaand bericht opslaan
    8. CRM synchroniseren naar Airtable
    """
    async with AsyncSessionLocal() as db:
        wa_service = WhatsAppService(db)
        ai_service = AIService(db)

        try:
            # Gesprek ophalen of aanmaken (org wordt opgezocht via to_phone)
            conversation = await wa_service.get_or_create_conversation(
                twilio_to_phone=to_phone,
                contact_phone=from_phone,
                contact_name=contact_name,
            )

            # Inkomend bericht opslaan
            await wa_service.save_message(
                conversation_id=conversation.id,
                direction="inbound",
                content=body,
                wa_message_id=message_sid,
            )

            # AI-antwoord genereren
            reply = await ai_service.generate_reply(
                conversation=conversation,
                incoming_message=body,
            )

            # Detecteer sluit-signaal van de AI
            conversation_closed = CLOSING_TAG in reply
            clean_reply = reply.replace(CLOSING_TAG, "").strip()

            # Gesprek afsluiten indien bevestigd → nieuwe lead bij volgend bericht
            if conversation_closed:
                conversation.status = "closed"
                await db.commit()
                await db.refresh(conversation)

                # E-mailnotificatie sturen naar agency (faalt stil als niet geconfigureerd)
                await send_lead_notification(conversation=conversation, db=db)

            # Antwoord versturen via Twilio (altijd zonder de interne tag)
            await wa_service.send_message(
                to_phone=from_phone,
                message=clean_reply,
            )

            # Uitgaand bericht opslaan (ook zonder tag)
            await wa_service.save_message(
                conversation_id=conversation.id,
                direction="outbound",
                content=clean_reply,
                ai_generated=True,
            )

            # CRM sync naar Airtable
            await wa_service.sync_to_crm(conversation=conversation)

        except Exception as e:
            logger.error("❌ Fout bij verwerking bericht van %s: %s", from_phone, e)
            raise
