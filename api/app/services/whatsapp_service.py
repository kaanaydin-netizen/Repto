"""
WhatsApp Service — communicatie via Twilio WhatsApp API.
Berichten sturen, gesprekken beheren en CRM-sync triggeren.
"""
from __future__ import annotations
from typing import Optional
import httpx
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.config import get_settings
from app.models.conversation import Conversation, Message, Organization, CrmSyncLog
from app.services.crm_sync_service import CrmSyncService

settings = get_settings()

TWILIO_MESSAGES_URL = (
    f"https://api.twilio.com/2010-04-01/Accounts"
    f"/{settings.twilio_account_sid}/Messages.json"
)


class WhatsAppService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.crm_sync = CrmSyncService(db)

    async def get_or_create_conversation(
        self,
        twilio_to_phone: str,
        contact_phone: str,
        contact_name: Optional[str],
    ) -> Conversation:
        """
        Haal een bestaand gesprek op of maak een nieuw aan.
        twilio_to_phone: het Twilio sandbox nummer (bijv. 'whatsapp:+14155238886')
        contact_phone:   het nummer van de klant (zonder 'whatsapp:' prefix)
        """
        # Organisatie zoeken op basis van het Twilio WhatsApp-nummer
        org_result = await self.db.execute(
            select(Organization).where(
                Organization.whatsapp_phone_number_id == twilio_to_phone
            )
        )
        org = org_result.scalar_one_or_none()
        if not org:
            raise ValueError(
                f"Geen organisatie gevonden voor Twilio nummer: {twilio_to_phone}. "
                f"Voer seed_dev.py uit om een test-organisatie aan te maken."
            )

        # Bestaand open gesprek zoeken
        conv_result = await self.db.execute(
            select(Conversation).where(
                Conversation.org_id == org.id,
                Conversation.wa_contact_phone == contact_phone,
                Conversation.status.in_(["new", "in_progress"]),
            )
        )
        conversation = conv_result.scalar_one_or_none()

        if not conversation:
            # Nieuw gesprek aanmaken
            conversation = Conversation(
                id=str(uuid.uuid4()),
                org_id=org.id,
                wa_contact_phone=contact_phone,
                wa_contact_name=contact_name,
                status="new",
            )
            self.db.add(conversation)
            await self.db.commit()
            await self.db.refresh(conversation)

        return conversation

    async def save_message(
        self,
        conversation_id: str,
        direction: str,
        content: str,
        ai_generated: bool = False,
        wa_message_id: Optional[str] = None,
    ) -> Message:
        """Sla een bericht op in de database."""
        message = Message(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            direction=direction,
            content=content,
            ai_generated=ai_generated,
            wa_message_id=wa_message_id,
        )
        self.db.add(message)
        await self.db.commit()
        return message

    async def send_message(
        self,
        to_phone: str,
        message: str,
    ) -> dict:
        """
        Stuur een tekstbericht via de Twilio WhatsApp API.
        to_phone: telefoonnummer van de ontvanger (zonder 'whatsapp:' prefix)
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                TWILIO_MESSAGES_URL,
                auth=(settings.twilio_account_sid, settings.twilio_auth_token),
                data={
                    "From": settings.twilio_whatsapp_from,
                    "To": f"whatsapp:{to_phone}",
                    "Body": message,
                },
            )
            response.raise_for_status()
            return response.json()

    async def sync_to_crm(self, conversation: Conversation) -> None:
        """Synchroniseer het gesprek naar het geconfigureerde CRM."""
        org_result = await self.db.execute(
            select(Organization).where(Organization.id == conversation.org_id)
        )
        org = org_result.scalar_one_or_none()
        if not org or org.crm_type == "none":
            return

        # Al eerder gesynchroniseerd?
        sync_result = await self.db.execute(
            select(CrmSyncLog).where(CrmSyncLog.conversation_id == conversation.id)
        )
        if sync_result.scalar_one_or_none():
            return  # Niet dubbel synchroniseren

        await self.crm_sync.sync(conversation=conversation, org=org)
