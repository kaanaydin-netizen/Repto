"""
Reminder Service — stuurt WhatsApp-herinneringen voor aankomende afspraken.
Wordt elk uur aangeroepen via APScheduler (zie main.py).

Een herinnering valt doorgaans buiten het 24u-klantvenster van WhatsApp en wordt
daarom verstuurd via een vooraf goedgekeurde Meta message-template
(zie settings.whatsapp_reminder_template). De template moet 3 body-placeholders
hebben, in volgorde: {{1}} contactnaam, {{2}} bedrijfsnaam, {{3}} datum/tijd.
"""
from __future__ import annotations
import logging
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import AsyncSessionLocal
from app.models.conversation import Appointment, Conversation, Organization
from app.services.whatsapp_service import WhatsAppService

settings = get_settings()
logger = logging.getLogger(__name__)

# Venster: 23h – 25h vanaf nu (zodat we elke uur runnen zonder dubbele reminders)
REMINDER_WINDOW_MIN_H = 23
REMINDER_WINDOW_MAX_H = 25


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

    # Afzendernummer van de organisatie; valt anders terug op de default uit settings
    sender_phone_number_id = org.whatsapp_phone_number_id if org else None
    if not sender_phone_number_id:
        logger.warning(
            "Org %s heeft geen whatsapp_phone_number_id — gebruik default afzender.",
            appt.org_id,
        )

    # Buiten het 24u-venster → via goedgekeurde Meta-template.
    # Body-placeholders in volgorde: {{1}} naam, {{2}} bedrijf, {{3}} datum/tijd.
    wa = WhatsAppService(db)
    try:
        await wa.send_template_message(
            to_phone=contact_phone,
            template_name=settings.whatsapp_reminder_template,
            language_code=settings.whatsapp_reminder_template_lang,
            body_params=[contact_name, org_name, start_formatted],
            phone_number_id=sender_phone_number_id,
        )
    except Exception as exc:
        # Niet als verstuurd markeren → volgende run probeert opnieuw
        # (typisch tot de template in Meta is goedgekeurd).
        logger.error(
            "Meta template-herinnering mislukt voor afspraak=%s: %s", appt.id, exc
        )
        return

    appt.reminder_sent = True
    await db.commit()
    logger.info(
        "Herinnering verstuurd: afspraak=%s | contact=%s | start=%s",
        appt.id,
        contact_phone,
        appt.start_at.isoformat(),
    )
