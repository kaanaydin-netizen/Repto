"""
WhatsApp Service — communicatie met Meta Cloud API.
Berichten sturen, gesprekken beheren en CRM-sync triggeren.
"""
import httpx
import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.config import get_settings
from app.models.conversation import Conversation, Message, Organization, CrmSyncLog
from app.services.crm_sync_service import CrmSyncService

settings = get_settings()

WHATSAPP_API_URL = "https://graph.facebook.com/v21.0"


class WhatsAppService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.crm_sync = CrmSyncService(db)

    async def get_or_create_conversation(
        self,
        phone_number_id: str,
        contact_phone: str,
        contact_name: str | None,
    ) -> Conversation:
        """Haal een bestaand gesprek op of maak een nieuw aan."""
        # Organisatie zoeken op basis van WhatsApp phone_number_id
        org_result = await self.db.execute(
            select(Organization).where(
                Organization.whatsapp_phone_number_id == phone_number_id
            )
        )
        org = org_result.scalar_one_or_none()
        if not org:
            raise ValueError(f"Geen organisatie gevonden voor phone_number_id: {phone_number_id}")

        # Bestaand gesprek zoeken
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
        wa_message_id: str | None = None,
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
        phone_number_id: str,
        to_phone: str,
        message: str,
    ) -> dict:
        """Stuur een tekstbericht via de Meta Cloud API."""
        url = f"{WHATSAPP_API_URL}/{phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {settings.whatsapp_access_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to_phone,
            "type": "text",
            "text": {"body": message},
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()

    async def sync_to_crm(self, conversation: Conversation) -> None:
        """Synchroniseer het gesprek naar het geconfigureerde CRM."""
        # Organisatie ophalen voor CRM-type
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

        # CRM sync uitvoeren
        await self.crm_sync.sync(conversation=conversation, org=org)
