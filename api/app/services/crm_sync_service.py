"""
CRM Sync Service — synchroniseert leads naar Airtable (primair) of Google Sheets (legacy).
v0.4: Airtable als standaard CRM via httpx REST API
"""
from __future__ import annotations
import json
import logging
import uuid
from datetime import datetime

import anthropic
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import get_settings
from app.models.conversation import Conversation, Organization, CrmSyncLog, Message

settings = get_settings()
logger = logging.getLogger(__name__)

EXTRACTION_MODEL = "claude-haiku-4-5-20251001"
AIRTABLE_API_URL = "https://api.airtable.com/v0"


class CrmSyncService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.claude_client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    async def sync(
        self,
        conversation: Conversation,
        org: Organization,
        existing_record_id: str | None = None,
        existing_log_id: str | None = None,
    ) -> None:
        """
        Stuur de lead naar het juiste CRM op basis van org.crm_type.
        Als existing_record_id opgegeven is, wordt het bestaande record bijgewerkt (upsert).
        """
        try:
            if org.crm_type == "airtable":
                external_id = await self._sync_airtable(
                    conversation, org, record_id=existing_record_id
                )
            elif org.crm_type == "google_sheets":
                external_id = await self._sync_google_sheets_legacy(conversation, org)
            elif org.crm_type == "hubspot":
                raise NotImplementedError("HubSpot integratie is gepland voor fase 2")
            elif org.crm_type == "pipedrive":
                raise NotImplementedError("Pipedrive integratie is gepland voor fase 2")
            else:
                return

            if existing_log_id:
                # Bestaand log bijwerken
                log_result = await self.db.execute(
                    select(CrmSyncLog).where(CrmSyncLog.id == existing_log_id)
                )
                log = log_result.scalar_one_or_none()
                if log:
                    log.external_id = external_id
                    log.success = True
                    log.error_message = None
            else:
                log = CrmSyncLog(
                    id=str(uuid.uuid4()),
                    conversation_id=conversation.id,
                    crm_type=org.crm_type,
                    external_id=external_id,
                    success=True,
                )
                self.db.add(log)

            await self.db.commit()
            action = "bijgewerkt" if existing_record_id else "aangemaakt"
            logger.info(f"✅ CRM sync ({action}): {conversation.wa_contact_phone} → {org.crm_type} [{external_id}]")

        except Exception as e:
            if existing_log_id:
                log_result = await self.db.execute(
                    select(CrmSyncLog).where(CrmSyncLog.id == existing_log_id)
                )
                log = log_result.scalar_one_or_none()
                if log:
                    log.success = False
                    log.error_message = str(e)
            else:
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

    async def _sync_airtable(
        self, conversation: Conversation, org: Organization, record_id: str | None = None
    ) -> str:
        """
        Schrijf of update een lead-record in Airtable via de REST API.
        - record_id=None  → POST (nieuw record aanmaken)
        - record_id=recXX → PATCH (bestaand record bijwerken)
        crm_credentials_encrypted bevat: {"api_key": "pat...", "base_id": "app...", "table_name": "Leads"}
        """
        if not org.crm_credentials_encrypted:
            raise ValueError("crm_credentials_encrypted niet geconfigureerd")

        config = json.loads(org.crm_credentials_encrypted)
        api_key = config.get("api_key")
        base_id = config.get("base_id")
        table_name = config.get("table_name", "Leads")

        if not api_key or not base_id:
            raise ValueError("api_key en base_id zijn verplicht in crm_credentials_encrypted")

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

        # Map interne status naar Airtable singleSelect keuzes
        STATUS_MAP = {
            "new":              "Todo",
            "in_progress":      "In progress",
            "appointment_set":  "In progress",
            "closed":           "Done",
        }

        fields = {
            "Datum": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "Naam": lead.get("naam") or conversation.wa_contact_name or "Onbekend",
            "Telefoon": conversation.wa_contact_phone,
            "Adres": lead.get("adres") or "",
            "Type Werk": lead.get("type_werk") or "",
            "Gewenste Datum": lead.get("gewenste_datum") or "",
            "Urgentie": lead.get("urgentie") or "",
            "Status": STATUS_MAP.get(conversation.status, "Todo"),
            "Eerste Bericht": (first_inbound.content[:500] if first_inbound else ""),
        }

        base_url = f"{AIRTABLE_API_URL}/{base_id}/{table_name}"
        req_headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=15) as client:
            if record_id:
                # PATCH — bestaand record bijwerken
                resp = await client.patch(
                    f"{base_url}/{record_id}",
                    headers=req_headers,
                    json={"fields": fields},
                )
            else:
                # POST — nieuw record aanmaken
                resp = await client.post(base_url, headers=req_headers, json={"fields": fields})

        if resp.status_code not in (200, 201):
            raise ValueError(f"Airtable API fout {resp.status_code}: {resp.text[:300]}")

        returned_id = resp.json().get("id", "unknown")
        action = "bijgewerkt" if record_id else "aangemaakt"
        logger.info(
            f"📋 Airtable {action}: {fields['Naam']} | {fields['Type Werk']} | urgentie={fields['Urgentie']} → {returned_id}"
        )
        return returned_id

    async def _sync_google_sheets_legacy(
        self, conversation: Conversation, org: Organization
    ) -> str:
        """
        Legacy Google Sheets sync via service account.
        Bewaard voor bestaande organisaties met crm_type='google_sheets'.
        """
        import asyncio
        import base64
        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        SHEETS_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
        SHEET_TAB = "Repto Leads"

        if not org.crm_credentials_encrypted:
            raise ValueError("crm_credentials_encrypted niet geconfigureerd")

        config = json.loads(org.crm_credentials_encrypted)
        spreadsheet_id = config.get("spreadsheet_id")
        if not spreadsheet_id:
            raise ValueError("spreadsheet_id ontbreekt in crm_credentials_encrypted")

        creds_raw = settings.google_sheets_credentials_json or settings.google_sheets_credentials_b64
        if not creds_raw:
            raise ValueError("GOOGLE_SHEETS_CREDENTIALS_JSON env var niet ingesteld")
        stripped = creds_raw.strip()
        creds_json = json.loads(stripped) if stripped.startswith("{") else json.loads(base64.b64decode(stripped).decode())
        credentials = service_account.Credentials.from_service_account_info(creds_json, scopes=SHEETS_SCOPES)

        msgs_result = await self.db.execute(
            select(Message)
            .where(Message.conversation_id == conversation.id)
            .order_by(Message.sent_at.asc())
        )
        all_messages = list(msgs_result.scalars().all())
        first_inbound = next((m for m in all_messages if m.direction == "inbound"), None)
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

        def _append():
            service = build("sheets", "v4", credentials=credentials, cache_discovery=False)
            service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                range=f"{SHEET_TAB}!A:I",
                valueInputOption="USER_ENTERED",
                body={"values": [row]},
            ).execute()

        await asyncio.to_thread(_append)
        return f"sheets_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


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
