"""
Lead-intake Service — kanaal-agnostische tegenhanger van
whatsapp_service.get_or_create_conversation.

Increment 2: élk kanaal (whatsapp, web_form, email, web_chat) brengt een lead
binnen via dezelfde poort, zodat ze identiek door de bestaande pipeline lopen
(verrijking → score → notificatie → CRM). De spil is dat conversatie + contact op
één plek worden gekoppeld; het bewaren van het inkomende bericht blijft per kanaal
(WhatsApp heeft een wa_message_id, web/e-mail niet) en gaat via save_message.
"""
from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation, Organization
from app.services.identity_service import resolve_contact

_OPEN_STATUSES = ["new", "in_progress"]


async def create_or_update_conversation(
    db: AsyncSession,
    org: Organization,
    *,
    channel: str,
    name: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
) -> Conversation:
    """
    Koppel deze inkomende lead aan één Contact en één open Conversation binnen `org`.

    1. resolve_contact (match op genormaliseerde e-mail OF telefoon, incl. merge).
    2. Hergebruik het open gesprek van dit Contact op dit kanaal, of maak een nieuw.

    Keyt het open gesprek op (org, contact_id, channel) i.p.v. op het ruwe nummer:
    het Contact is de canonieke identiteit, en web-/e-mailleads hebben geen nummer.
    Voor WhatsApp is dit equivalent (zelfde persoon → zelfde contact → zelfde open
    gesprek). Bewaart het inkomende bericht NIET — dat doet de aanroeper via
    save_message (kanaal-specifieke velden zoals wa_message_id).
    """
    contact = await resolve_contact(
        db, org.id, email=email, phone=phone, name=name, channel=channel,
    )

    result = await db.execute(
        select(Conversation).where(
            Conversation.org_id == org.id,
            Conversation.contact_id == contact.id,
            Conversation.channel == channel,
            Conversation.status.in_(_OPEN_STATUSES),
        )
    )
    conversation = result.scalars().first()

    if conversation is None:
        conversation = Conversation(
            id=str(uuid.uuid4()),
            org_id=org.id,
            contact_id=contact.id,
            channel=channel,
            wa_contact_phone=phone,   # NULL voor web/e-mail (kolom is nullable sinds 004)
            wa_contact_name=name,
            status="new",
        )
        db.add(conversation)
        await db.commit()
        await db.refresh(conversation)

    return conversation
