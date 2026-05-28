"""
WhatsApp Service — communicatie via de Meta WhatsApp Cloud API.
Berichten sturen, gesprekken beheren en CRM-sync triggeren.

Meta Cloud API: POST https://graph.facebook.com/{version}/{phone_number_id}/messages
met een Bearer access-token. Eén system-user token (agency-WABA) kan namens
meerdere telefoonnummers sturen; het afzendernummer wordt bepaald door phone_number_id.
"""
from __future__ import annotations
from typing import Optional, List
import logging
import httpx
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.config import get_settings
from app.models.conversation import Conversation, Message, Organization, CrmSyncLog
from app.services.crm_sync_service import CrmSyncService

settings = get_settings()
logger = logging.getLogger(__name__)


def graph_messages_url(phone_number_id: str) -> str:
    """Bouw de Cloud API messages-endpoint voor een specifiek afzendernummer."""
    return (
        f"https://graph.facebook.com/{settings.whatsapp_api_version}"
        f"/{phone_number_id}/messages"
    )


def _normalize_recipient(to_phone: str) -> str:
    """Meta verwacht het nummer in internationaal formaat zonder '+' (wa_id)."""
    return to_phone.lstrip("+").strip()


class WhatsAppService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.crm_sync = CrmSyncService(db)

    async def get_or_create_conversation(
        self,
        phone_number_id: str,
        contact_phone: str,
        contact_name: Optional[str],
    ) -> Conversation:
        """
        Haal een bestaand gesprek op of maak een nieuw aan.
        phone_number_id: het Meta Cloud API phone_number_id van het ontvangende
                         bedrijfsnummer (uit webhook metadata.phone_number_id).
        contact_phone:   het nummer van de klant (wa_id, internationaal zonder '+').
        """
        # Organisatie zoeken op basis van het Meta phone_number_id
        org_result = await self.db.execute(
            select(Organization).where(
                Organization.whatsapp_phone_number_id == phone_number_id
            )
        )
        org = org_result.scalar_one_or_none()
        if not org:
            raise ValueError(
                f"Geen organisatie gevonden voor phone_number_id: {phone_number_id}. "
                f"Koppel dit nummer aan een organisatie (zie seed_dev.py)."
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

    async def _post(self, phone_number_id: str, payload: dict) -> dict:
        """Verstuur één bericht-payload naar de Meta Cloud API."""
        url = graph_messages_url(phone_number_id)
        headers = {
            "Authorization": f"Bearer {settings.whatsapp_access_token}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(url, headers=headers, json=payload)
            if response.status_code >= 400:
                # Meta geeft gestructureerde foutinfo terug — log het volledig voor debugging
                logger.error(
                    "Meta Cloud API fout (HTTP %s) bij verzenden naar %s: %s",
                    response.status_code, payload.get("to"), response.text[:500],
                )
            response.raise_for_status()
            return response.json()

    async def send_message(
        self,
        to_phone: str,
        message: str,
        phone_number_id: Optional[str] = None,
    ) -> dict:
        """
        Stuur een vrij tekstbericht via de Meta Cloud API.
        Let op: vrije tekst mag enkel binnen het 24u-klantvenster — buiten dat
        venster gebruik je send_template_message.

        to_phone:        nummer van de ontvanger (internationaal, '+' optioneel).
        phone_number_id: afzendernummer; valt terug op de default uit settings.
        """
        sender = phone_number_id or settings.whatsapp_phone_number_id
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": _normalize_recipient(to_phone),
            "type": "text",
            "text": {"preview_url": False, "body": message},
        }
        return await self._post(sender, payload)

    async def send_template_message(
        self,
        to_phone: str,
        template_name: str,
        language_code: str,
        body_params: Optional[List[str]] = None,
        phone_number_id: Optional[str] = None,
    ) -> dict:
        """
        Stuur een vooraf goedgekeurde template (voor berichten buiten het 24u-venster,
        zoals afspraakherinneringen).

        body_params: waarden voor de {{1}}, {{2}}, … placeholders in de template-body,
                     in volgorde. De template moet vooraf goedgekeurd zijn in Meta.
        """
        sender = phone_number_id or settings.whatsapp_phone_number_id
        template: dict = {
            "name": template_name,
            "language": {"code": language_code},
        }
        if body_params:
            template["components"] = [
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": str(p)} for p in body_params
                    ],
                }
            ]
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": _normalize_recipient(to_phone),
            "type": "template",
            "template": template,
        }
        return await self._post(sender, payload)

    async def sync_to_crm(self, conversation: Conversation) -> None:
        """
        Synchroniseer het gesprek naar het geconfigureerde CRM.

        Logica:
        - Wacht tot er minstens 3 berichten zijn (zodat de AI al naam/adres/type werk
          heeft kunnen verzamelen) voordat de eerste sync plaatsvindt.
        - Bij elke volgende sync wordt het bestaande Airtable-record bijgewerkt (upsert),
          zodat de lead altijd up-to-date is terwijl het gesprek vordert.
        """
        org_result = await self.db.execute(
            select(Organization).where(Organization.id == conversation.org_id)
        )
        org = org_result.scalar_one_or_none()
        if not org or org.crm_type == "none":
            return

        # Tel het aantal berichten — wacht op minstens 3 (≈ 2 inbound + 1 outbound)
        msg_result = await self.db.execute(
            select(Message).where(Message.conversation_id == conversation.id)
        )
        msg_count = len(msg_result.scalars().all())
        if msg_count < 3:
            return  # Nog te weinig info om te synchroniseren

        # Controleer of er al een sync-log bestaat (voor upsert)
        sync_result = await self.db.execute(
            select(CrmSyncLog).where(CrmSyncLog.conversation_id == conversation.id)
        )
        existing_log = sync_result.scalar_one_or_none()

        # Alleen een Airtable record ID (begint met "rec") gebruiken voor PATCH.
        # Google Sheets IDs (bijv. "sheets_...") zijn geen geldig Airtable ID.
        existing_record_id = None
        existing_log_id = None
        if existing_log:
            existing_log_id = existing_log.id
            ext_id = existing_log.external_id or ""
            if ext_id.startswith("rec"):
                existing_record_id = ext_id

        await self.crm_sync.sync(
            conversation=conversation,
            org=org,
            existing_record_id=existing_record_id,
            existing_log_id=existing_log_id,
        )
