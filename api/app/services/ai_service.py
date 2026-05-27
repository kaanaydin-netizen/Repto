"""
AI Service — genereert antwoorden via Anthropic Claude.
Gebruikt sector-specifieke prompts + prompt caching voor lagere kosten.
v0.4: tool use → automatisch afspraken aanmaken in de DB
"""
from __future__ import annotations
import uuid
import json
import logging
from datetime import datetime
from typing import Optional

import anthropic
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.config import get_settings
from app.models.conversation import Conversation, Message, Organization, Appointment

settings = get_settings()
logger = logging.getLogger(__name__)

# ─── Sector-specifieke systeem-prompts ────────────────────────────────────────
# Placeholders: {company_name}, {tone}, {company_info}

SECTOR_PROMPTS: dict[str, str] = {
    "installateur": """\
Je bent de digitale receptionist van {company_name}, een installatiebedrijf.
Communiceer op een {tone} manier.

Bij elk nieuw gesprek verzamel je actief de volgende informatie:
1. **Naam** van de klant (als niet bekend via WhatsApp-profiel)
2. **Adres** van de interventie
3. **Type werk** (elektriciteit, sanitair, verwarming, zonnepanelen, ventilatie, …)
4. **Gewenste datum/tijdstip**
5. **Urgentie**: is het dringend? (ja / nee)

Stel één vraag tegelijk. Zodra je alle info hebt, bevestig je dat een medewerker \
contact opneemt en geef je een realistische verwachting (reactietijd, planning).
Zodra de klant een concrete datum EN tijdstip bevestigt, roep je de tool `create_appointment` aan.

{company_info}
""",

    "makelaar": """\
Je bent de digitale receptionist van {company_name}, een vastgoedkantoor.
Communiceer op een {tone} manier.

Bij elk nieuw gesprek verzamel je actief de volgende informatie:
1. **Naam** van de klant
2. **Type aanvraag**: koop, huur, verkoop of schatting
3. **Locatie/gemeente** van interesse
4. **Budget** of gewenste prijs
5. **Gewenste datum** voor bezichtiging of kennismaking

Stel één vraag tegelijk. Kwalificeer de lead (ernstige koper/huurder vs. oriënterend). \
Verwijs bij complexe vragen naar een makelaar.
Zodra de klant een concrete datum EN tijdstip bevestigt, roep je de tool `create_appointment` aan.

{company_info}
""",

    "kinesist": """\
Je bent de digitale receptionist van {company_name}, een kinesistenpraktijk.
Communiceer op een {tone} manier.

Bij elk nieuw gesprek verzamel je actief de volgende informatie:
1. **Naam** van de patiënt
2. **Type klacht of behandeling** (rugpijn, sportletsel, revalidatie, …)
3. **Gewenste dag en tijdstip**
4. **Dringend of chronisch**?
5. **Voorschrift** van de dokter aanwezig? (ja / nee / niet zeker)

Stel één vraag tegelijk. Wijs erop dat sommige sessies een voorschrift vereisen \
voor terugbetaling via mutualiteit.
Zodra de klant een concrete datum EN tijdstip bevestigt, roep je de tool `create_appointment` aan.

{company_info}
""",

    "freelancer": """\
Je bent de digitale assistent van {company_name}.
Communiceer op een {tone} manier.

Bij elk nieuw gesprek verzamel je actief de volgende informatie:
1. **Naam en bedrijf** van de klant
2. **Type project of opdracht** (website, logo, consultancy, fotografie, …)
3. **Deadline** of gewenste startdatum
4. **Geschat budget** (optioneel, maar handig)
5. **Hoe hoorde u van ons?**

Stel één vraag tegelijk. Geef aan dat een voorstel/offerte binnen enkele werkdagen \
wordt opgemaakt na het intakegesprek.
Zodra de klant een concrete datum EN tijdstip bevestigt, roep je de tool `create_appointment` aan.

{company_info}
""",

    "garage": """\
Je bent de digitale receptionist van {company_name}, een autogarage.
Communiceer op een {tone} manier.

Bij elk nieuw gesprek verzamel je actief de volgende informatie:
1. **Naam** van de klant
2. **Merk en model** van de wagen (+ bouwjaar indien relevant)
3. **Type werk**: onderhoud, herstelling, APK-keuring, banden, schade, …
4. **Gewenste datum/tijdstip** voor de afspraak
5. **Urgentie**: is de wagen rijveilig / kan het wachten?

Stel één vraag tegelijk. Bij urgente veiligheidsrisico's (remmen, banden, …) \
adviseer je direct contact op te nemen.
Zodra de klant een concrete datum EN tijdstip bevestigt, roep je de tool `create_appointment` aan.

{company_info}
""",

    "boekhouder": """\
Je bent de digitale assistent van {company_name}, een boekhoudkantoor.
Communiceer op een {tone} manier.

Bij elk nieuw gesprek verzamel je actief de volgende informatie:
1. **Naam en bedrijfsnaam** van de klant
2. **Type vraag**: BTW-aangifte, vennootschapsbelasting, loonadministratie, \
   opstart bedrijf, jaarrekening, …
3. **Dringendheid** of wettelijke deadline
4. **Beste moment** voor een afspraak of terugbelverzoek

Stel één vraag tegelijk. Verwijs bij dringende fiscale deadlines \
naar de kantoortelefoon.
Zodra de klant een concrete datum EN tijdstip bevestigt, roep je de tool `create_appointment` aan.

{company_info}
""",

    "bouw": """\
Je bent de digitale receptionist van {company_name}, een bouwbedrijf.
Communiceer op een {tone} manier.

Bij elk nieuw gesprek verzamel je actief de volgende informatie:
1. **Naam** van de klant
2. **Adres van de werf**
3. **Type werk**: nieuwbouw, renovatie, dakwerken, afbraak, ruwbouw, …
4. **Gewenste startdatum** of planningshorizon
5. **Vergunning** al aangevraagd/verkregen? (ja / nee / niet van toepassing)

Stel één vraag tegelijk. Geef aan dat een werfbezoek en offerte ingepland worden \
zodra de basisinfo volledig is.
Zodra de klant een concrete datum EN tijdstip bevestigt, roep je de tool `create_appointment` aan.

{company_info}
""",

    "algemeen": """\
Je bent de digitale receptionist van {company_name}.
Communiceer op een {tone} manier.

Begroet de klant vriendelijk en vraag waarmee je kan helpen.
Noteer actief:
1. **Naam** van de klant (als niet bekend)
2. **Contactreden** of vraag
3. **Gewenste vervolgstap** (afspraak, terugbelverzoek, offerte, …)

Stel één vraag tegelijk. Verwijs bij complexe vragen naar de juiste persoon.
Zodra de klant een concrete datum EN tijdstip bevestigt, roep je de tool `create_appointment` aan.

{company_info}
""",
}


CLOSING_INSTRUCTION = """\

---
BELANGRIJK — Gesprek afsluiten:
Zodra je ALLE benodigde informatie hebt verzameld EN de klant de samenvatting heeft \
bevestigd (bijv. "ja", "correct", "top", "ok"), voeg je op het absolute einde van \
je antwoord de tag [GESPREK_AFGEROND] toe. Geen spaties of tekst erna.
Voorbeeld van de laatste zin: "Een medewerker neemt spoedig contact met u op. [GESPREK_AFGEROND]"
Voeg deze tag NOOIT toe als de klant nog niet bevestigd heeft of als er nog vragen openstaan.
"""


# ─── Tool definitie voor afspraken ────────────────────────────────────────────

APPOINTMENT_TOOL: dict = {
    "name": "create_appointment",
    "description": (
        "Maak een afspraak aan in het systeem zodra de klant een concrete datum "
        "en tijdstip heeft bevestigd. Roep deze tool ALLEEN aan als de klant "
        "uitdrukkelijk akkoord gaat met een specifieke datum en tijd."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": (
                    "Korte omschrijving van de afspraak, bijv. "
                    "'Lekherstel badkamer – Thomas De Smedt' of 'Onderhoud VW Golf – Jan Peeters'."
                ),
            },
            "contact_name": {
                "type": "string",
                "description": "Naam van de klant zoals opgegeven in het gesprek.",
            },
            "start_at": {
                "type": "string",
                "description": (
                    "Startdatum en -tijd in ISO 8601 formaat (YYYY-MM-DDTHH:MM:SS). "
                    "Gebruik het huidige jaar als de klant alleen een dag/maand noemt."
                ),
            },
            "end_at": {
                "type": "string",
                "description": (
                    "Einddatum en -tijd in ISO 8601 formaat. "
                    "Standaard 1 uur na start_at als niet opgegeven."
                ),
            },
        },
        "required": ["title", "start_at", "end_at"],
    },
}


def build_system_prompt(org: Organization) -> str:
    """
    Bouw het systeem-bericht op basis van de organisatie-configuratie.
    Gebruikt org.sector om de juiste sector-prompt te selecteren.
    """
    sector = (org.sector or "algemeen").lower().strip()
    template = SECTOR_PROMPTS.get(sector, SECTOR_PROMPTS["algemeen"])

    base = template.format(
        company_name=org.name or "ons bedrijf",
        tone=org.ai_tone or "professioneel",
        company_info=org.ai_system_prompt or "",
    )
    return base + CLOSING_INSTRUCTION


class AIService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    async def generate_reply(
        self,
        conversation: Conversation,
        incoming_message: str,
    ) -> str:
        """
        Genereer een AI-antwoord op basis van het gesprek en het inkomende bericht.
        Gebruikt sector-specifieke prompt + prompt caching (1u cache TTL bij Anthropic).
        Ondersteunt tool use: als Claude `create_appointment` aanroept, wordt de
        afspraak direct aangemaakt in de DB en krijgt Claude een bevestiging terug.
        """
        # Organisatie ophalen voor context
        result = await self.db.execute(
            select(Organization).where(Organization.id == conversation.org_id)
        )
        org = result.scalar_one_or_none()
        if not org:
            return "Bedankt voor uw bericht! We nemen zo snel mogelijk contact met u op."

        # Gesprekshistoriek ophalen (laatste 10 berichten voor context)
        history_result = await self.db.execute(
            select(Message)
            .where(Message.conversation_id == conversation.id)
            .order_by(Message.sent_at.desc())
            .limit(10)
        )
        history = list(reversed(history_result.scalars().all()))

        # Sector-specifieke system prompt opbouwen
        system_prompt = build_system_prompt(org)

        # Berichten omzetten naar Anthropic formaat
        messages: list[dict] = []
        for msg in history[:-1]:  # Vorige berichten (zonder het laatste inkomende)
            role = "user" if msg.direction == "inbound" else "assistant"
            messages.append({"role": role, "content": msg.content})

        # Huidig inkomend bericht toevoegen
        messages.append({"role": "user", "content": incoming_message})

        # ── Eerste Claude-aanroep met tool definitie ───────────────────────────
        response = await self.client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=600,
            system=[
                {
                    "type": "text",
                    "text": system_prompt,
                    "cache_control": {"type": "ephemeral"},  # Cache de system prompt (1u TTL)
                }
            ],
            tools=[APPOINTMENT_TOOL],
            messages=messages,
        )

        # ── Tool-use loop ──────────────────────────────────────────────────────
        # Claude kan maximaal één tool (create_appointment) aanroepen.
        # Na de tool-result sturen we een tweede aanroep om de definitieve tekst te krijgen.
        while response.stop_reason == "tool_use":
            tool_use_block = next(
                (b for b in response.content if b.type == "tool_use"), None
            )
            if tool_use_block is None:
                break  # Geen tool block gevonden — onverwachte toestand, stop loop

            tool_name: str = tool_use_block.name
            tool_input: dict = tool_use_block.input  # type: ignore[assignment]
            tool_use_id: str = tool_use_block.id

            if tool_name == "create_appointment":
                tool_result_content = await self._handle_create_appointment(
                    tool_input=tool_input,
                    conversation=conversation,
                )
            else:
                tool_result_content = f"Onbekende tool: {tool_name}"

            # Voeg het assistant-antwoord + tool result toe aan de messages
            messages.append({"role": "assistant", "content": response.content})
            messages.append({
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_use_id,
                        "content": tool_result_content,
                    }
                ],
            })

            # Tweede aanroep: Claude genereert definitieve bevestigingstekst
            response = await self.client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=400,
                system=[
                    {
                        "type": "text",
                        "text": system_prompt,
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
                tools=[APPOINTMENT_TOOL],
                messages=messages,
            )

        # ── Tekst extractie ────────────────────────────────────────────────────
        text_block = next(
            (b for b in response.content if hasattr(b, "text")), None
        )
        return text_block.text if text_block else "Bedankt! We nemen zo snel mogelijk contact met u op."

    # ─── Tool handlers ────────────────────────────────────────────────────────

    async def _handle_create_appointment(
        self,
        tool_input: dict,
        conversation: Conversation,
    ) -> str:
        """
        Maak een Appointment record aan in de DB op basis van de tool input.
        Retourneert een bevestigingsstring voor Claude.
        """
        try:
            title: str = tool_input.get("title", "Afspraak")
            start_str: str = tool_input.get("start_at", "")
            end_str: str = tool_input.get("end_at", "")

            # Parse datums — accepteer ISO formaat
            start_dt = _parse_iso(start_str)
            end_dt = _parse_iso(end_str)

            if start_dt is None:
                return "Fout: ongeldige startdatum. Vraag de klant om een exacte datum en tijd."

            if end_dt is None:
                # Standaard 1 uur na start
                from datetime import timedelta
                end_dt = start_dt + timedelta(hours=1)

            appointment = Appointment(
                id=str(uuid.uuid4()),
                conversation_id=conversation.id,
                org_id=conversation.org_id,
                title=title,
                start_at=start_dt,
                end_at=end_dt,
                status="confirmed",
                reminder_sent=False,
            )
            self.db.add(appointment)

            # Gespreksstatus bijwerken
            conversation.status = "appointment_set"

            await self.db.commit()
            await self.db.refresh(appointment)

            logger.info(
                "Afspraak aangemaakt: %s | %s → %s | org=%s",
                title,
                start_dt.isoformat(),
                end_dt.isoformat(),
                conversation.org_id,
            )

            return (
                f"Afspraak succesvol aangemaakt: '{title}' op "
                f"{start_dt.strftime('%d/%m/%Y om %H:%M')} "
                f"t/m {end_dt.strftime('%H:%M')}. "
                f"ID: {appointment.id}"
            )

        except Exception as exc:
            logger.error("Fout bij aanmaken afspraak via tool use: %s", exc)
            return f"Fout bij opslaan afspraak: {exc}. Vraag de klant opnieuw te bevestigen."


# ─── Hulpfuncties ─────────────────────────────────────────────────────────────

def _parse_iso(dt_str: str) -> Optional[datetime]:
    """Parseer een ISO 8601 datum/tijdstring. Retourneert None bij fout."""
    if not dt_str:
        return None
    formats = [
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(dt_str.strip(), fmt)
        except ValueError:
            continue
    return None
