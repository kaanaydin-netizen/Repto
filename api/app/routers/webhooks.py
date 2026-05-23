"""
WhatsApp webhook handler — ontvangt inkomende berichten van Meta Cloud API
en triggert de AI-verwerking.
"""
from fastapi import APIRouter, Request, HTTPException, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import get_settings
from app.database import get_db
from app.services.whatsapp_service import WhatsAppService
from app.services.ai_service import AIService

router = APIRouter(prefix="/webhooks", tags=["webhooks"])
settings = get_settings()


@router.get("/whatsapp")
async def verify_webhook(
    hub_mode: str | None = None,
    hub_verify_token: str | None = None,
    hub_challenge: str | None = None,
):
    """
    Meta stuurt een GET-verzoek om de webhook te verifiëren.
    Geef de challenge terug als het verify_token klopt.
    """
    if hub_mode == "subscribe" and hub_verify_token == settings.whatsapp_verify_token:
        return int(hub_challenge)
    raise HTTPException(status_code=403, detail="Verificatie mislukt")


@router.post("/whatsapp")
async def receive_message(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Ontvangt inkomende WhatsApp-berichten van Meta.
    Verwerkt het bericht asynchroon op de achtergrond.
    """
    payload = await request.json()

    # Verwerk elk inkomend bericht
    try:
        for entry in payload.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                messages = value.get("messages", [])

                for message in messages:
                    # Verwerk bericht op de achtergrond (niet de webhook blokkeren)
                    background_tasks.add_task(
                        process_incoming_message,
                        message=message,
                        metadata=value.get("metadata", {}),
                        contacts=value.get("contacts", []),
                        db=db,
                    )
    except Exception as e:
        # Log de fout maar geef altijd 200 terug aan Meta
        print(f"Fout bij verwerking webhook: {e}")

    return {"status": "ok"}


async def process_incoming_message(
    message: dict,
    metadata: dict,
    contacts: list,
    db: AsyncSession,
):
    """
    Verwerkt een inkomend WhatsApp-bericht:
    1. Gesprek ophalen of aanmaken
    2. Bericht opslaan
    3. AI-antwoord genereren
    4. Antwoord versturen via WhatsApp
    5. CRM synchroniseren (Google Sheets)
    """
    wa_service = WhatsAppService(db)
    ai_service = AIService(db)

    phone_number_id = metadata.get("phone_number_id")
    from_phone = message.get("from")
    contact_name = contacts[0].get("profile", {}).get("name") if contacts else None
    message_text = message.get("text", {}).get("body", "") if message.get("type") == "text" else ""

    if not from_phone or not message_text:
        return

    # Gesprek ophalen of aanmaken
    conversation = await wa_service.get_or_create_conversation(
        phone_number_id=phone_number_id,
        contact_phone=from_phone,
        contact_name=contact_name,
    )

    # Inkomend bericht opslaan
    await wa_service.save_message(
        conversation_id=conversation.id,
        direction="inbound",
        content=message_text,
        wa_message_id=message.get("id"),
    )

    # AI-antwoord genereren
    reply = await ai_service.generate_reply(
        conversation=conversation,
        incoming_message=message_text,
    )

    # Antwoord versturen
    await wa_service.send_message(
        phone_number_id=phone_number_id,
        to_phone=from_phone,
        message=reply,
    )

    # Antwoord opslaan
    await wa_service.save_message(
        conversation_id=conversation.id,
        direction="outbound",
        content=reply,
        ai_generated=True,
    )

    # CRM sync (Google Sheets voor MVP)
    await wa_service.sync_to_crm(conversation=conversation)
