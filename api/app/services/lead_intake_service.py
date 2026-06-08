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
    merged_out: Optional[list] = None,
    reuse_any_status: bool = False,
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

    merged_out: optionele lijst die bij een contact-merge de herkoppelde conversation-ids
    krijgt (voor CRM-cleanup van verweesde records). Zie resolve_contact.
    """
    contact = await resolve_contact(
        db, org.id, email=email, phone=phone, name=name, channel=channel,
        merged_out=merged_out,
    )

    # Standaard hergebruiken we enkel een OPEN gesprek. Voor eenmalige kanalen (web-form)
    # mag het gesprek meteen 'closed' staan; reuse_any_status=True laat een herinzending dan
    # tóch hetzelfde gesprek hergebruiken (geen rij-proliferatie per resubmit).
    conditions = [
        Conversation.org_id == org.id,
        Conversation.contact_id == contact.id,
        Conversation.channel == channel,
    ]
    if not reuse_any_status:
        conditions.append(Conversation.status.in_(_OPEN_STATUSES))
    result = await db.execute(
        select(Conversation).where(*conditions).order_by(Conversation.created_at.desc())
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


# Stabiele namespace voor deterministische web-chat-gesprek-id's uit een sessie-id.
_WEBCHAT_NS = uuid.uuid5(uuid.NAMESPACE_URL, "repto-webchat")


async def get_or_create_web_chat_conversation(
    db: AsyncSession,
    org: Organization,
    *,
    session_id: str,
    name: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    merged_out: Optional[list] = None,
) -> Conversation:
    """
    Web-chat is SESSIE-gekeyd, niet identiteit-gekeyd: een bezoeker kan anoniem starten
    (nog geen e-mail/telefoon) en de chat moet over meerdere berichten hetzelfde gesprek
    + geheugen behouden. We leiden daarom een DETERMINISTISCHE gesprek-id af uit
    (org, session_id) — zo vindt elke vervolg-POST exact hetzelfde gesprek terug.

    Bij creatie koppelen we een Contact via resolve_contact (met e-mail/telefoon indien
    al bekend; anders een vers anoniem Contact). Wordt later in de chat een e-mail ontdekt,
    dan voegt extract_and_enrich dat alsnog samen met een bestaand profiel.
    """
    conv_id = str(uuid.uuid5(_WEBCHAT_NS, f"{org.id}:{session_id}"))
    conversation = await db.get(Conversation, conv_id)
    if conversation is not None:
        return conversation

    contact = await resolve_contact(
        db, org.id, email=email, phone=phone, name=name, channel="web_chat",
        merged_out=merged_out,
    )
    conversation = Conversation(
        id=conv_id,
        org_id=org.id,
        contact_id=contact.id,
        channel="web_chat",
        wa_contact_phone=phone,
        wa_contact_name=name,
        status="new",
    )
    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)
    return conversation
