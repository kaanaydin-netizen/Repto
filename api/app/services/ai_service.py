"""
AI Service — genereert antwoorden via Anthropic Claude.
Gebruikt prompt caching voor lagere kosten bij hoog berichtenvolume.
"""
from __future__ import annotations
import anthropic
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.config import get_settings
from app.models.conversation import Conversation, Message, Organization

settings = get_settings()


DEFAULT_SYSTEM_PROMPT = """Je bent een vriendelijke en professionele AI-receptionist voor {company_name}.

Sector: {sector}
Toon: {tone}

Jouw taken:
- Beantwoord klantvragen over onze diensten, prijzen en openingsuren
- Plan afspraken in als de klant dat vraagt
- Stuur een bevestiging na het inplannen van een afspraak
- Verwijs door naar een medewerker bij complexe of urgente vragen

Richtlijnen:
- Wees kort en bondig (max 3-4 zinnen per antwoord)
- Gebruik de taal van de klant (NL/FR/EN)
- Bij urgentie (lek, panne, nood): geef altijd het directe telefoonnummer mee
- Nooit beloften maken over prijzen die je niet zeker weet

Bedrijfsinformatie:
{company_info}
"""


class AIService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    async def generate_reply(self, conversation: Conversation, incoming_message: str) -> str:
        """
        Genereer een AI-antwoord op basis van het gesprek en het inkomende bericht.
        Gebruikt prompt caching voor de system prompt (1u cache TTL bij Anthropic).
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

        # System prompt samenstellen
        system_prompt = (org.ai_system_prompt or DEFAULT_SYSTEM_PROMPT).format(
            company_name=org.name,
            sector=org.sector or "algemeen",
            tone=org.ai_tone or "formeel",
            company_info="Neem contact op voor meer info.",
        )

        # Berichten omzetten naar Anthropic formaat
        messages = []
        for msg in history[:-1]:  # Vorige berichten (zonder het laatste inkomende)
            role = "user" if msg.direction == "inbound" else "assistant"
            messages.append({"role": role, "content": msg.content})

        # Huidig inkomend bericht toevoegen
        messages.append({"role": "user", "content": incoming_message})

        # Claude aanroepen met prompt caching op de system prompt
        response = await self.client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=500,
            system=[
                {
                    "type": "text",
                    "text": system_prompt,
                    "cache_control": {"type": "ephemeral"},  # Cache de system prompt (1u TTL)
                }
            ],
            messages=messages,
        )

        return response.content[0].text
