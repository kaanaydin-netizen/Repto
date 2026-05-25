"""
CRM Sync Service — synchroniseert nieuwe leads naar:
  MVP:    Google Sheets via Apps Script webhook (9 kolommen)
  Fase 2: HubSpot, Pipedrive
v0.3: Lead-extractie via Claude Haiku + 9-kolommen sync
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

    async def _extract_lead_data(self, messages: list[Message]) -> dict:
        """
        Tweede Claude-aanroep (Haiku) om gestructureerde lead-data
        te extraheren uit de conversatiehistoriek.
        Retourneert: {naam, adres, type_werk, gewenste_datum, urgentie}
        """
        conversation_text = "\n".join(
            f"{m.direction}: {m.content}"
            for m in messages
            if m.content
        )

        if not conversation_text.strip():
            logger.warning("_extract_lead_data: leeg gesprek")
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

        except json.JSONDecodeError as e:
            logger.error(f"_extract_lead_data: JSON parse fout: {e}")
            return _empty_lead()
        except Exception as e:
            logger.error(f"_extract_lead_data: fout: {e}")
            return _empty_lead()

    async def _sync_google_sheets(
        self, conversation: Conversation, org: Organization
    ) -> str:
        """
        Voeg een nieuwe lead toe aan Google Sheets via Apps Script webhook.
        9 kolommen: datum, naam, telefoon, adres, type_werk, gewenste_datum,
                    urgentie, status, eerste_bericht
        """
        if not org.crm_credentials_encrypted:
            raise ValueError("Google Sheets webhook URL niet geconfigureerd")

        config = json.loads(org.crm_credentials_encrypted)
        webhook_url = config.get("webhook_url")
        if not webhook_url:
            raise ValueError("webhook_url ontbreekt in crm_credentials_encrypted")

        # Alle berichten ophalen voor extractie
        msgs_result = await self.db.execute(
            select(Message)
            .where(Message.conversation_id == conversation.id)
            .order_by(Message.sent_at.asc())
        )
        all_messages = msgs_result.scalars().all()

        # Eerste inkomend bericht
        first_message = next(
            (m for m in all_messages if m.direction == "inbound"), None
        )

        # Lead-data extraheren via Claude Haiku
        lead = await self._extract_lead_data(list(all_messages))

        payload = {
            "datum": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "naam": lead.get("naam") or conversation.wa_contact_name or "Onbekend",
            "telefoon": conversation.wa_contact_phone,
            "adres": lead.get("adres") or "",
            "type_werk": lead.get("type_werk") or "",
            "gewenste_datum": lead.get("gewenste_datum") or "",
            "urgentie": lead.get("urgentie") or "",
            "status": conversation.status,
            "eerste_bericht": (first_message.content[:300] if first_message else ""),
        }

        # POST naar de Apps Script webhook
        # Google Apps Script stuurt 302 redirect → httpx converteert POST→GET (correct gedrag)
        async with httpx.AsyncClient(follow_redirects=True, timeout=15.0) as client:
            response = await client.post(
                webhook_url,
                content=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()

        print(f"📊 Sheets sync: {payload['naam']} | urgentie={payload['urgentie']} | werk={payload['type_werk']}")
        return f"sheets_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    async def _sync_hubspot(self, conversation: Conversation, org: Organization) -> str:
        raise NotImplementedError("HubSpot integratie is gepland voor fase 2")

    async def _sync_pipedrive(self, conversation: Conversation, org: Organization) -> str:
        raise NotImplementedError("Pipedrive integratie is gepland voor fase 2")


# ─── Hulpfuncties ─────────────────────────────────────────────────────────────

def _empty_lead() -> dict:
    return {
        "naam": None,
        "adres": None,
        "type_werk": None,
        "gewenste_datum": None,
        "urgentie": None,
    }


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
