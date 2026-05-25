"""
CRM Sync Service — synchroniseert leads rechtstreeks naar Google Sheets
via de Google Sheets API (service account). Geen webhook, geen redirect.
v0.3: Lead-extractie via Claude Haiku + 9-kolommen directe API write
"""
from __future__ import annotations
import asyncio
import base64
import json
import logging
import uuid
from datetime import datetime

import anthropic
from google.oauth2 import service_account
from googleapiclient.discovery import build
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import get_settings
from app.models.conversation import Conversation, Organization, CrmSyncLog, Message

settings = get_settings()
logger = logging.getLogger(__name__)

EXTRACTION_MODEL = "claude-haiku-4-5-20251001"
SHEETS_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SHEET_TAB = "Repto Leads"


def _get_sheets_service():
    """Bouw een Google Sheets API service op via de service account credentials."""
    creds_b64 = settings.google_sheets_credentials_b64
    if not creds_b64:
        raise ValueError("GOOGLE_SHEETS_CREDENTIALS_B64 env var niet ingesteld")

    creds_json = json.loads(base64.b64decode(creds_b64).decode())
    credentials = service_account.Credentials.from_service_account_info(
        creds_json, scopes=SHEETS_SCOPES
    )
    return build("sheets", "v4", credentials=credentials, cache_discovery=False)


class CrmSyncService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.claude_client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

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

            log = CrmSyncLog(
                id=str(uuid.uuid4()),
                conversation_id=conversation.id,
                crm_type=org.crm_type,
                external_id=external_id,
                success=True,
            )
            self.db.add(log)
            await self.db.commit()
            logger.info(f"✅ CRM sync: {conversation.wa_contact_phone} → {org.crm_type}")

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
            logger.error(f"❌ CRM sync mislukt voor gesprek {conversation.id}: {e}")

    async def _extract_lead_data(self, messages: list[Message]) -> dict:
        """
        Tweede Claude-aanroep (Haiku) om gestructureerde lead-data
        te extraheren uit de conversatiehistoriek.
        """
        conversation_text = "\n".join(
            f"{m.direction}: {m.content}"
            for m in messages
            if m.content
        )

        if not conversation_text.strip():
            return _empty_lead()

        try:
            response = await self.claude_client.messages.create(
                model=EXTRACTION_MODEL,
                max_tokens=300,
                system=(
                    "Je bent een data-extractie-assistent. "
                    "Analyseer het klantgesprek en extraheer de volgende velden als JSON-object. "
                    "Gebruik exact deze sleutels. Gebruik null voor onbekende of niet-vermelde velden.\n\n"
                    "Velden:\n"
                    "- naam: naam van de klant (string of null)\n"
                    "- adres: adres/locatie van de interventie of het bezoek (string of null)\n"
                    "- type_werk: type werk, dienst of vraag (string of null)\n"
                    "- gewenste_datum: gewenste datum of tijdstip (string of null)\n"
                    "- urgentie: is het dringend? Gebruik exact 'ja', 'nee', of null\n\n"
                    "Antwoord UITSLUITEND met een geldig JSON-object, geen extra tekst."
                ),
                messages=[{"role": "user", "content": conversation_text}],
            )

            raw = response.content[0].text.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            data = json.loads(raw)

            return {
                "naam": _str_or_none(data.get("naam")),
                "adres": _str_or_none(data.get("adres")),
                "type_werk": _str_or_none(data.get("type_werk")),
                "gewenste_datum": _str_or_none(data.get("gewenste_datum")),
                "urgentie": _normalize_urgentie(data.get("urgentie")),
            }

        except Exception as e:
            logger.error(f"_extract_lead_data fout: {e}")
            return _empty_lead()

    async def _sync_google_sheets(
        self, conversation: Conversation, org: Organization
    ) -> str:
        """
        Schrijf een nieuwe lead-rij rechtstreeks naar Google Sheets
        via de Sheets API (service account). Geen webhook nodig.
        9 kolommen: Datum | Naam | Telefoon | Adres | Type Werk |
                    Gewenste Datum | Urgentie | Status | Eerste Bericht
        """
        if not org.crm_credentials_encrypted:
            raise ValueError("crm_credentials_encrypted niet geconfigureerd")

        config = json.loads(org.crm_credentials_encrypted)
        spreadsheet_id = config.get("spreadsheet_id")
        if not spreadsheet_id:
            raise ValueError("spreadsheet_id ontbreekt in crm_credentials_encrypted")

        # Alle berichten ophalen
        msgs_result = await self.db.execute(
            select(Message)
            .where(Message.conversation_id == conversation.id)
            .order_by(Message.sent_at.asc())
        )
        all_messages = list(msgs_result.scalars().all())
        first_inbound = next((m for m in all_messages if m.direction == "inbound"), None)

        # Lead-data extraheren via Claude Haiku
        lead = await self._extract_lead_data(all_messages)

        row = [
            datetime.now().strftime("%d/%m/%Y %H:%M"),
            lead.get("naam") or conversation.wa_contact_name or "Onbekend",
            conversation.wa_contact_phone,
            lead.get("adres") or "",
            lead.get("type_werk") or "",
            lead.get("gewenste_datum") or "",
            lead.get("urgentie") or "",
            conversation.status,
            (first_inbound.content[:300] if first_inbound else ""),
        ]

        # Schrijf naar Sheets in een thread (synchrone API)
        await asyncio.to_thread(
            _append_row_to_sheet,
            spreadsheet_id=spreadsheet_id,
            tab_name=SHEET_TAB,
            row=row,
        )

        logger.info(
            f"📊 Sheets: {row[1]} | {lead.get('type_werk')} | urgentie={lead.get('urgentie')}"
        )
        return f"sheets_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    async def _sync_hubspot(self, conversation: Conversation, org: Organization) -> str:
        raise NotImplementedError("HubSpot integratie is gepland voor fase 2")

    async def _sync_pipedrive(self, conversation: Conversation, org: Organization) -> str:
        raise NotImplementedError("Pipedrive integratie is gepland voor fase 2")


def _append_row_to_sheet(spreadsheet_id: str, tab_name: str, row: list) -> None:
    """Synchrone helper — voer uit in thread via asyncio.to_thread()."""
    service = _get_sheets_service()
    service.spreadsheets().values().append(
        spreadsheetId=spreadsheet_id,
        range=f"{tab_name}!A:I",
        valueInputOption="USER_ENTERED",
        body={"values": [row]},
    ).execute()


# ─── Hulpfuncties ─────────────────────────────────────────────────────────────

def _empty_lead() -> dict:
    return {"naam": None, "adres": None, "type_werk": None,
            "gewenste_datum": None, "urgentie": None}


def _str_or_none(val) -> str | None:
    if val is None:
        return None
    s = str(val).strip()
    return s if s and s.lower() not in ("null", "none", "") else None


def _normalize_urgentie(val) -> str | None:
    if val is None:
        return None
    s = str(val).strip().lower()
    if s in ("ja", "yes", "dringend", "urgent", "true"):
        return "ja"
    if s in ("nee", "no", "niet dringend", "normaal", "false"):
        return "nee"
    return None
