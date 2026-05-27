"""
Reminder Service — stuurt WhatsApp-herinneringen voor aankomende afspraken.
Wordt elk uur aangeroepen via APScheduler (zie main.py).
Stuurt een herinnering 24 uur voor de afspraak via de Twilio WhatsApp sandbox.
"""
from __future__ import annotations
import logging
from datetime import datetime, timedelta

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import AsyncSessionLocal
from app.models.conversation import Appointment, Conversation, Organization

settings = get_settings()
logger = logging.getLogger(__name__)

# Venster: 23h – 25h vanaf nu (zodat we elke uur runnen zonder dubbele reminders)
REMINDER_WINDOW_MIN_H = 23
REMINDER_WINDOW_MAX_H = 25

TWILIO_SMS_URL = (
    f"https://api.twilio.com/2010-04-01/Accounts/"
    f"{settings.twilio_account_sid}/Messages.json"
)


async def send_appointment_reminders() -> None:
    """
    Hoofdfunctie voor de APScheduler job.
    Maakt een nieuwe DB-sessie aan en verwerkt alle openstaande herinneringen.
    """
    async with AsyncSessionLocal() as db:
        try:
            await _process_reminders(db)
        except Exception as exc:
            logger.error("Fout in reminder job: %s", exc)


async def _process_reminders(db: AsyncSession) -> None:
    now = datetime.utcnow()
    window_start = now + timedelta(hours=REMINDER_WINDOW_MIN_H)
    window_end = now + timedelta(hours=REMINDER_WINDOW_MAX_H)

    # Haal alle ongestuurde bevestigde afspraken op binnen het venster
    result = await db.execute(
        select(Appointment)
        .where(
            Appointment.status == "confirmed",
            Appointment.reminder_sent == False,  # noqa: E712
            Appointment.start_at >= window_start,
            Appointment.start_at <= window_end,
        )
    )
    appointments = list(result.scalars().all())

    if not appointments:
        logger.debug("Reminder job: geen openstaande herinneringen in venster %s – %s.", window_start, window_end)
        return

    logger.info("Reminder job: %d herinneringen te versturen.", len(appointments))

    for appt in appointments:
        try:
            await _send_reminder(appt, db)
        except Exception as exc:
            logger.error("Herinnering mislukt voor afspraak %s: %s", appt.id, exc)


async def _send_reminder(appt: Appointment, db: AsyncSession) -> None:
    """Stuur een WhatsApp-herinnering voor één afspraak."""

    # Gesprek ophalen (bevat het telefoonnummer van de contactpersoon)
    conv_result = await db.execute(
        select(Conversation).where(Conversation.id == appt.conversation_id)
    )
    conversation = conv_result.scalar_one_or_none()
    if not conversation:
        logger.warning("Conversation niet gevonden voor afspraak %s — skip.", appt.id)
        return

    # Organisatie ophalen (voor bedrijfsnaam in het bericht)
    org_result = await db.execute(
        select(Organization).where(Organization.id == appt.org_id)
    )
    org = org_result.scalar_one_or_none()
    org_name = org.name if org else "uw afspraak"

    contact_phone = conversation.wa_contact_phone
    contact_name = conversation.wa_contact_name or "Beste klant"

    start_formatted = appt.start_at.strftime("%A %d %B om %H:%M")

    message = (
        f"📅 Herinnering van {org_name}\n\n"
        f"Goedendag {contact_name},\n\n"
        f"We herinneren u eraan dat u morgen een afspraak heeft:\n"
        f"*{appt.title}*\n"
        f"📆 {start_formatted}\n\n"
        f"Kan u niet aanwezig zijn? Stuur ons gerust een bericht om te verzetten."
    )

    # Stuur via Twilio WhatsApp
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            TWILIO_SMS_URL,
            auth=(settings.twilio_account_sid, settings.twilio_auth_token),
            data={
                "From": settings.twilio_whatsapp_from,
                "To": f"whatsapp:{contact_phone}",
                "Body": message,
            },
        )

    if resp.status_code in (200, 201):
        appt.reminder_sent = True
        await db.commit()
        logger.info(
            "Herinnering verstuurd: afspraak=%s | contact=%s | start=%s",
            appt.id,
            contact_phone,
            appt.start_at.isoformat(),
        )
    else:
        logger.error(
            "Twilio fout bij herinnering afspraak=%s: HTTP %s — %s",
            appt.id,
            resp.status_code,
            resp.text[:200],
        )
