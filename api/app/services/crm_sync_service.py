"""
CRM Sync Service — synchroniseert nieuwe leads naar:
  MVP:    Google Sheets (via Apps Script webhook)
  Fase 2: HubSpot, Pipedrive
"""
from __future__ import annotations
import json
import uuid
from datetime import datetime
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.conversation import Conversation, Organization, CrmSyncLog, Message


class CrmSyncService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def sync(self, conversation: Conversation, org: Organization) -> None:
        """Stuur de lead naar het juiste CRM op basis van org.crm_type."""
        try:
            if org.crm_type == "google_sheets":
                external_id = await self._sync_google_sheets(conversation, org)
            elif org.crm_type == "hubspot":
                external_id = await self._sync_hubspot(conversation, org)
            elif org.crm_type == "pipedrive":
                external_id = await self._sync_pipedrive(conversation, org)
            else:
                return

            # Log de succesvolle sync
            log = CrmSyncLog(
                id=str(uuid.uuid4()),
                conversation_id=conversation.id,
                crm_type=org.crm_type,
                external_id=external_id,
                success=True,
            )
            self.db.add(log)
            await self.db.commit()
            print(f"✅ CRM sync geslaagd: {conversation.wa_contact_phone} → {org.crm_type}")

        except Exception as e:
            log = CrmSyncLog(
                id=str(uuid.uuid4()),
                conversation_id=conversation.id,
                crm_type=org.crm_type,
                success=False,
                error_message=str(e),
            )
            self.db.add(log)
            await self.db.commit()
            print(f"❌ CRM sync mislukt voor gesprek {conversation.id}: {e}")

    async def _sync_google_sheets(
        self, conversation: Conversation, org: Organization
    ) -> str:
        """
        Voeg een nieuwe lead toe aan Google Sheets via Apps Script webhook.
        org.crm_credentials_encrypted bevat JSON: {"webhook_url": "https://script.google.com/..."}
        """
        if not org.crm_credentials_encrypted:
            raise ValueError("Google Sheets webhook URL niet geconfigureerd")

        config = json.loads(org.crm_credentials_encrypted)
        webhook_url = config.get("webhook_url")
        if not webhook_url:
            raise ValueError("webhook_url ontbreekt in crm_credentials_encrypted")

        # Eerste inkomende bericht ophalen
        msgs_result = await self.db.execute(
            select(Message)
            .where(
                Message.conversation_id == conversation.id,
                Message.direction == "inbound",
            )
            .order_by(Message.sent_at.asc())
            .limit(1)
        )
        first_message = msgs_result.scalar_one_or_none()

        payload = {
            "datum": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "naam": conversation.wa_contact_name or "Onbekend",
            "telefoon": conversation.wa_contact_phone,
            "status": conversation.status,
            "eerste_bericht": (first_message.content[:200] if first_message else ""),
        }

        # POST naar de Apps Script webhook (follow_redirects=True voor Google redirect)
        async with httpx.AsyncClient(follow_redirects=True, timeout=15.0) as client:
            response = await client.post(webhook_url, json=payload)
            response.raise_for_status()

        return f"sheets_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    async def _sync_hubspot(self, conversation: Conversation, org: Organization) -> str:
        raise NotImplementedError("HubSpot integratie is gepland voor fase 2")

    async def _sync_pipedrive(self, conversation: Conversation, org: Organization) -> str:
        raise NotImplementedError("Pipedrive integratie is gepland voor fase 2")
