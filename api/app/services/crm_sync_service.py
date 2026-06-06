"""
CRM Sync Service — synchroniseert leads naar Airtable (primair) of Google Sheets (legacy).
v0.4: Airtable als standaard CRM via httpx REST API
"""
from __future__ import annotations
import json
import logging
import uuid
from datetime import datetime
from urllib.parse import quote

import anthropic
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import get_settings
from app.models.conversation import Conversation, Organization, CrmSyncLog, Message, Appointment, Contact
from app.services.ai_service import _NL_DAGEN, _NL_MAANDEN
from app.services.identity_service import compute_lead_score

settings = get_settings()
logger = logging.getLogger(__name__)

EXTRACTION_MODEL = "claude-haiku-4-5-20251001"
AIRTABLE_API_URL = "https://api.airtable.com/v0"


def _today_nl() -> str:
    """Huidige datum als NL-string, voor relatieve datum-resolutie in de extractie."""
    now = datetime.now()
    return f"{_NL_DAGEN[now.weekday()]} {now.day} {_NL_MAANDEN[now.month - 1]} {now.year}"


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
        lead: dict | None = None,
    ) -> None:
        """
        Stuur de lead naar het juiste CRM op basis van org.crm_type.
        Als existing_record_id opgegeven is, wordt het bestaande record bijgewerkt (upsert).
        lead: een reeds geëxtraheerde lead-dict (hergebruik) of None (zelf extraheren).
        """
        try:
            if org.crm_type == "airtable":
                external_id = await self._sync_airtable(conversation, org, lead=lead)
            elif org.crm_type == "google_sheets":
                external_id = await self._sync_google_sheets_legacy(conversation, org, lead=lead)
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
            who = conversation.wa_contact_phone or conversation.contact_id or conversation.id
            logger.info(f"✅ CRM sync ({action}): {who} → {org.crm_type} [{external_id}]")

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
                max_tokens=500,
                system=(
                    "Je bent een data-extractie-assistent voor een klantgesprek via WhatsApp. "
                    f"Vandaag is het {_today_nl()}. Gebruik deze datum om relatieve verwijzingen "
                    "('volgende week', 'over 3 dagen') om te zetten naar een concrete datum in de toekomst. "
                    "Analyseer het gesprek en geef UITSLUITEND een geldig JSON-object terug met exact deze "
                    "sleutels (gebruik null bij onbekend), geen extra tekst:\n"
                    "- naam: naam van de klant (string of null)\n"
                    "- adres: adres/locatie van de interventie of het bezoek (string of null)\n"
                    "- email: e-mailadres van de klant (string of null)\n"
                    "- type_werk: type werk, dienst of vraag (string of null)\n"
                    "- gewenste_datum: door de klant gewenste datum of tijdstip (string of null)\n"
                    "- urgentie: hoe dringend? Gebruik exact 'Laag', 'Normaal', 'Hoog', 'Spoed', of null\n"
                    "- intentie: één van 'Offerte', 'Afspraak', 'Info', 'Klacht', 'Anders'\n"
                    "- samenvatting: korte samenvatting van het gesprek in 1 à 2 zinnen (string)\n"
                    "- opvolging_nodig: true als de klant later opnieuw gecontacteerd moet worden "
                    "(bijv. offerte verstuurd maar nog geen afspraak), anders false (boolean)\n"
                    "- opvolg_reden: korte reden voor de opvolging (string of null)\n"
                    "- opvolg_datum: ISO-datum (YYYY-MM-DD) wanneer opgevolgd moet worden, of null"
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
                "email": _str_or_none(data.get("email")),
                "type_werk": _str_or_none(data.get("type_werk")),
                "gewenste_datum": _str_or_none(data.get("gewenste_datum")),
                "urgentie": _normalize_urgentie(data.get("urgentie")),
                "intentie": _normalize_intentie(data.get("intentie")),
                "samenvatting": _str_or_none(data.get("samenvatting")),
                "opvolging_nodig": bool(data.get("opvolging_nodig")),
                "opvolg_reden": _str_or_none(data.get("opvolg_reden")),
                "opvolg_datum": _str_or_none(data.get("opvolg_datum")),
            }

        except Exception as e:
            logger.error(f"_extract_lead_data fout: {e}")
            return _empty_lead()

    async def _airtable_upsert(
        self,
        client: httpx.AsyncClient,
        base_id: str,
        api_key: str,
        table: str,
        merge_on: list[str],
        fields: dict,
    ) -> str:
        """
        Upsert één record via Airtable's native performUpsert (merge op merge_on).
        typecast=true zodat ontbrekende single-select-opties automatisch worden aangemaakt.
        Retourneert het Airtable record-ID.
        """
        url = f"{AIRTABLE_API_URL}/{base_id}/{quote(table)}"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        body = {
            "performUpsert": {"fieldsToMergeOn": merge_on},
            "typecast": True,
            "records": [{"fields": fields}],
        }
        resp = await client.patch(url, headers=headers, json=body)
        if resp.status_code not in (200, 201):
            raise ValueError(f"Airtable upsert '{table}' fout {resp.status_code}: {resp.text[:300]}")
        records = resp.json().get("records", [])
        return records[0].get("id", "unknown") if records else "unknown"

    async def _sync_airtable(
        self, conversation: Conversation, org: Organization, lead: dict | None = None
    ) -> str:
        """
        Synchroniseer het gesprek naar Airtable als relationeel mini-CRM.
        - Leads: verrijkte tabel (status-pijplijn, intentie, samenvatting).
        - Afspraken: één record per DB-afspraak, gekoppeld aan de Lead.
        - Opvolgingen: één record wanneer de AI opvolging nodig acht.
        crm_credentials_encrypted bevat: {"api_key": "pat...", "base_id": "app...",
          "table_name": "Leads", "appointments_table": "Afspraken", "followups_table": "Opvolgingen"}
        """
        if not org.crm_credentials_encrypted:
            raise ValueError("crm_credentials_encrypted niet geconfigureerd")

        config = json.loads(org.crm_credentials_encrypted)
        api_key = config.get("api_key")
        base_id = config.get("base_id")
        leads_table = config.get("table_name", "Leads")
        appointments_table = config.get("appointments_table", "Afspraken")
        followups_table = config.get("followups_table", "Opvolgingen")
        if not api_key or not base_id:
            raise ValueError("api_key en base_id zijn verplicht in crm_credentials_encrypted")

        # Lead-data: hergebruik de reeds geëxtraheerde dict indien meegegeven (coherente
        # score), anders zelf extraheren via Claude Haiku (standalone-pad).
        if lead is None:
            msgs_result = await self.db.execute(
                select(Message)
                .where(Message.conversation_id == conversation.id)
                .order_by(Message.sent_at.asc())
            )
            all_messages = list(msgs_result.scalars().all())
            lead = await self._extract_lead_data(all_messages)

        # Afspraken van dit gesprek bepalen mee de pijplijn-status én worden zelf gesynct.
        appt_result = await self.db.execute(
            select(Appointment).where(Appointment.conversation_id == conversation.id)
        )
        appointments = list(appt_result.scalars().all())
        has_appointment = len(appointments) > 0

        # Eén Airtable-record per PERSOON (Contact), niet per gesprek: meerdere gesprekken/
        # kanalen van dezelfde persoon mergen op contact.id. Identiteitsvelden komen van het
        # Contact (kanaal-overschrijdend, genormaliseerd) en vallen terug op de kanaal-specifieke
        # conversation.wa_contact_* — die NULL kan zijn voor web-/e-mailleads.
        contact = None
        if conversation.contact_id:
            contact_result = await self.db.execute(
                select(Contact).where(Contact.id == conversation.contact_id)
            )
            contact = contact_result.scalar_one_or_none()
        # Defensief: zonder Contact (mag niet voorkomen na migratie 003) valt de merge-key
        # terug op conversation.id — log het, want het duidt op een ontkoppelde rij.
        bron_id = contact.id if contact else conversation.id
        if not contact:
            logger.warning(
                "Airtable-sync zonder Contact voor gesprek %s — merge-key valt terug op conversation.id",
                conversation.id,
            )

        first_contact = conversation.created_at or datetime.now()
        # Type werk + samenvatting samengevoegd in één veld (formaat "Type werk — samenvatting").
        samenvatting = _combine_type_en_samenvatting(lead.get("type_werk"), lead.get("samenvatting"))
        # Deterministische warm/lauw/koud-score uit dezelfde lead-dict (zelfde resultaat als de
        # contact-verrijking) — Airtable single-select verwacht hoofdletter (Warm/Lauw/Koud).
        score, score_reason = compute_lead_score(lead)
        lead_fields = {
            "Bron ID": bron_id,
            "Naam": lead.get("naam") or (contact.name if contact else None) or conversation.wa_contact_name or "Onbekend",
            "Telefoon": (contact.phone if contact else None) or conversation.wa_contact_phone or "",
            "Adres": lead.get("adres") or "",
            "E-mail": lead.get("email") or (contact.email if contact else None) or "",
            "Gewenste Datum": lead.get("gewenste_datum") or "",
            "Status": _pipeline_status(conversation, has_appointment, lead),
            "Intentie": lead.get("intentie") or "Anders",
            "Urgentie": lead.get("urgentie") or "",
            "Score": score.capitalize(),
            "Score Reden": score_reason,
            "Samenvatting": samenvatting,
            "Eerste contact": first_contact.isoformat(),
            "Laatste update": datetime.now().isoformat(),
        }

        async with httpx.AsyncClient(timeout=15) as client:
            lead_record_id = await self._airtable_upsert(
                client, base_id, api_key, leads_table, ["Bron ID"], lead_fields
            )

            # Afspraken syncen — de Lead-link vult automatisch het omgekeerde
            # "Afspraken"-veld op het Lead-record (bidirectionele link).
            appt_count = 0
            for appt in appointments:
                appt_fields = {
                    "Titel": appt.title or "Afspraak",
                    "Bron ID": appt.id,
                    "Lead": [lead_record_id],
                    "Start": appt.start_at.isoformat() if appt.start_at else None,
                    "Einde": appt.end_at.isoformat() if appt.end_at else None,
                    "Status": _appointment_status(appt.status),
                }
                appt_fields = {k: v for k, v in appt_fields.items() if v is not None}
                await self._airtable_upsert(
                    client, base_id, api_key, appointments_table, ["Bron ID"], appt_fields
                )
                appt_count += 1

            # Opvolging syncen (één per gesprek) wanneer de AI dit nodig acht.
            followup_synced = False
            if lead.get("opvolging_nodig"):
                followup_fields = {
                    "Reden": lead.get("opvolg_reden") or "Opvolging nodig",
                    "Bron ID": conversation.id,
                    "Lead": [lead_record_id],
                    "Opvolgdatum": lead.get("opvolg_datum"),
                }
                followup_fields = {k: v for k, v in followup_fields.items() if v is not None}
                await self._airtable_upsert(
                    client, base_id, api_key, followups_table, ["Bron ID"], followup_fields
                )
                followup_synced = True

        logger.info(
            f"📋 Airtable Lead upsert: {lead_fields['Naam']} | status={lead_fields['Status']} | "
            f"intentie={lead_fields['Intentie']} | afspraken={appt_count} | "
            f"opvolging={'ja' if followup_synced else 'nee'} → {lead_record_id}"
        )
        return lead_record_id

    async def _sync_google_sheets_legacy(
        self, conversation: Conversation, org: Organization, lead: dict | None = None
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
        if lead is None:
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
    return {
        "naam": None, "adres": None, "email": None, "type_werk": None,
        "gewenste_datum": None, "urgentie": None,
        "intentie": "Anders", "samenvatting": None,
        "opvolging_nodig": False, "opvolg_reden": None, "opvolg_datum": None,
    }


_INTENTIES = {"offerte": "Offerte", "afspraak": "Afspraak", "info": "Info",
              "klacht": "Klacht", "anders": "Anders"}

_APPOINTMENT_STATUS = {"confirmed": "Bevestigd", "cancelled": "Geannuleerd",
                       "completed": "Voltooid", "pending": "Bevestigd"}


def _appointment_status(val) -> str:
    """Map de interne afspraak-status naar een NL single-select-keuze in Airtable."""
    if val is None:
        return "Bevestigd"
    return _APPOINTMENT_STATUS.get(str(val).strip().lower(), "Bevestigd")


def _normalize_intentie(val) -> str:
    """Map de AI-intentie naar exact één van de toegestane Airtable-keuzes."""
    if val is None:
        return "Anders"
    return _INTENTIES.get(str(val).strip().lower(), "Anders")


def _pipeline_status(conversation: Conversation, has_appointment: bool, lead: dict) -> str:
    """
    Map de interne gespreksstatus + context naar de Airtable-pijplijn (single select).
    Fases: Nieuw · In behandeling · Afspraak gepland · Offerte verstuurd · Op te volgen ·
    Gewonnen · Verloren.
    """
    status = conversation.status

    # Een afspraak weegt het zwaarst — los van of het gesprek al gesloten is.
    if has_appointment or status == "appointment_set":
        return "Afspraak gepland"

    if status == "closed":
        # Geen afspraak: onderscheid offerte/opvolging vs. afgehandeld.
        if lead.get("opvolging_nodig"):
            return "Op te volgen"
        if lead.get("intentie") == "Offerte":
            return "Offerte verstuurd"
        return "Gewonnen"

    if status == "in_progress":
        return "In behandeling"

    return "Nieuw"


def _str_or_none(val) -> str | None:
    if val is None:
        return None
    s = str(val).strip()
    return s if s and s.lower() not in ("null", "none", "") else None


def _combine_type_en_samenvatting(type_werk, samenvatting) -> str:
    """Voeg type werk en samenvatting samen tot één veld: 'Type werk — samenvatting'.
    Valt terug op wat beschikbaar is als er maar één van beide is."""
    t = _str_or_none(type_werk)
    s = _str_or_none(samenvatting)
    if t and s:
        return f"{t} — {s}"
    return t or s or ""


def _normalize_urgentie(val) -> str | None:
    """Map de urgentie naar exact één van Laag/Normaal/Hoog/Spoed (of None).
    Accepteert ook de oude 'ja'/'nee'-waarden voor terugwaartse compatibiliteit."""
    if val is None:
        return None
    s = str(val).strip().lower()
    mapping = {
        "laag": "Laag", "low": "Laag",
        "normaal": "Normaal", "normal": "Normaal", "niet dringend": "Normaal",
        "nee": "Normaal", "no": "Normaal", "false": "Normaal",
        "hoog": "Hoog", "high": "Hoog", "dringend": "Hoog",
        "ja": "Hoog", "yes": "Hoog", "true": "Hoog",
        "spoed": "Spoed", "urgent": "Spoed",
    }
    return mapping.get(s)
