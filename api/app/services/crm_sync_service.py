"""
CRM Sync Service — synchroniseert nieuwe leads naar:
  MVP:    Google Sheets
  Fase 2: HubSpot, Pipedrive
"""
import uuid
import httpx
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.conversation import Conversation, Organization, CrmSyncLog


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

        except Exception as e:
            # Log de mislukte sync maar blokkeer de flow niet
            log = CrmSyncLog(
                id=str(uuid.uuid4()),
                conversation_id=conversation.id,
                crm_type=org.crm_type,
                success=False,
                error_message=str(e),
            )
            self.db.add(log)
            await self.db.commit()
            print(f"CRM sync mislukt voor gesprek {conversation.id}: {e}")

    async def _sync_google_sheets(
        self, conversation: Conversation, org: Organization
    ) -> str:
        """
        Voeg een nieuwe rij toe aan het Google Sheet van de organisatie.
        Kolommen: Naam | Telefoon | Datum | Status | Eerste bericht
        """
        # TODO: Google Sheets API integratie implementeren
        # Vereist: google-auth service account of OAuth2 token
        # org.crm_sheet_id bevat het Sheet ID
        # org.crm_credentials_encrypted bevat het service account JSON (encrypted)
        print(f"[TODO] Google Sheets sync voor {conversation.wa_contact_phone} → Sheet {org.crm_sheet_id}")
        return f"sheets_row_{conversation.id[:8]}"

    async def _sync_hubspot(
        self, conversation: Conversation, org: Organization
    ) -> str:
        """
        Maak een contact aan in HubSpot.
        Fase 2 — nog niet geïmplementeerd in MVP.
        """
        # TODO: HubSpot API implementeren (fase 2)
        # POST https://api.hubapi.com/crm/v3/objects/contacts
        raise NotImplementedError("HubSpot integratie is gepland voor fase 2")

    async def _sync_pipedrive(
        self, conversation: Conversation, org: Organization
    ) -> str:
        """
        Maak een persoon + deal aan in Pipedrive.
        Fase 2 — nog niet geïmplementeerd in MVP.
        """
        # TODO: Pipedrive API implementeren (fase 2)
        # POST https://{domain}.pipedrive.com/api/v1/persons
        raise NotImplementedError("Pipedrive integratie is gepland voor fase 2")
