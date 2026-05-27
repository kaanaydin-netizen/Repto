"""
Google Calendar Service — maakt Calendar events aan voor afspraken.
Gebruikt een Google Service Account (zelfde credentials als Google Sheets).
Faalt altijd stil: errors worden gelogd maar crashen de applicatie nooit.
"""
from __future__ import annotations

import asyncio
import base64
import json
import logging
from typing import Optional

from app.config import get_settings
from app.models.conversation import Appointment, Organization

settings = get_settings()
logger = logging.getLogger(__name__)

BRUSSELS_TZ = "Europe/Brussels"


class GoogleCalendarService:
    """Service voor Google Calendar integratie via Service Account."""

    def is_configured(self) -> bool:
        """Retourneert True als Google credentials beschikbaar zijn."""
        return bool(settings.google_sheets_credentials_json)

    def _build_service(self):
        """
        Bouw een Google Calendar API service object op basis van de Service Account credentials.
        Retourneert None als de credentials ontbreken of ongeldig zijn.
        """
        try:
            from google.oauth2 import service_account
            from googleapiclient.discovery import build

            creds_raw = settings.google_sheets_credentials_json
            if not creds_raw:
                return None

            # Probeer base64-decode; als dat mislukt, neem het als plain JSON
            try:
                creds_json = base64.b64decode(creds_raw).decode("utf-8")
            except Exception:
                creds_json = creds_raw

            creds_dict = json.loads(creds_json)

            credentials = service_account.Credentials.from_service_account_info(
                creds_dict,
                scopes=["https://www.googleapis.com/auth/calendar"],
            )
            service = build("calendar", "v3", credentials=credentials, cache_discovery=False)
            return service
        except Exception as exc:
            logger.warning("Google Calendar: kon service niet opbouwen: %s", exc)
            return None

    def _create_event_sync(
        self,
        appointment: Appointment,
        org: Organization,
    ) -> Optional[str]:
        """
        Synchrone helper die het Calendar event aanmaakt.
        Bedoeld om via asyncio.to_thread te draaien.
        Retourneert de event ID bij succes, None bij fout.
        """
        try:
            service = self._build_service()
            if service is None:
                return None

            # Gebruik crm_sheet_id als calendar ID indien beschikbaar, anders 'primary'
            calendar_id = org.crm_sheet_id or "primary"

            # Datumtijden opmaken met timezone
            start_iso = appointment.start_at.isoformat()
            end_iso = appointment.end_at.isoformat()

            event_body = {
                "summary": appointment.title,
                "description": (
                    f"Afspraak ingepland via Repto AI-receptionist. "
                    f"Organisatie: {org.name}"
                ),
                "start": {
                    "dateTime": start_iso,
                    "timeZone": BRUSSELS_TZ,
                },
                "end": {
                    "dateTime": end_iso,
                    "timeZone": BRUSSELS_TZ,
                },
            }

            created = (
                service.events()
                .insert(calendarId=calendar_id, body=event_body)
                .execute()
            )
            event_id: str = created.get("id", "")
            logger.info(
                "Google Calendar event aangemaakt: %s (calendar=%s)",
                event_id,
                calendar_id,
            )
            return event_id or None

        except Exception as exc:
            logger.warning("Google Calendar: event aanmaken mislukt: %s", exc)
            return None

    async def create_event(
        self,
        appointment: Appointment,
        org: Organization,
    ) -> Optional[str]:
        """
        Maakt een Google Calendar event aan voor de gegeven afspraak.
        Gebruikt asyncio.to_thread omdat de Google API client synchroon is.
        Retourneert de event ID bij succes, None bij fout.
        """
        return await asyncio.to_thread(self._create_event_sync, appointment, org)

    def _delete_event_sync(self, event_id: str, calendar_id: str) -> None:
        """Synchrone helper om een Calendar event te verwijderen."""
        try:
            service = self._build_service()
            if service is None:
                return
            service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
            logger.info(
                "Google Calendar event verwijderd: %s (calendar=%s)",
                event_id,
                calendar_id,
            )
        except Exception as exc:
            logger.warning("Google Calendar: event verwijderen mislukt: %s", exc)

    async def delete_event(
        self,
        event_id: str,
        calendar_id: str = "primary",
    ) -> None:
        """
        Verwijdert een Google Calendar event.
        Faalt stil: errors worden gelogd maar niet opgegooid.
        """
        await asyncio.to_thread(self._delete_event_sync, event_id, calendar_id)
