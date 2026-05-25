"""
Conversations API — voor het dashboard om gesprekken op te halen en te beheren.
"""
from __future__ import annotations
from typing import Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from app.database import get_db
from app.models.conversation import Conversation, Message

router = APIRouter(prefix="/conversations", tags=["conversations"])


# ─── Response schemas ─────────────────────────────────────────────────────────

class ConversationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    org_id: str
    wa_contact_phone: str
    wa_contact_name: Optional[str]
    status: str
    crm_synced_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    last_message: Optional[str] = None


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    conversation_id: str
    direction: str
    content: str
    ai_generated: bool
    sent_at: datetime


class StatsOut(BaseModel):
    total_conversations: int
    new_leads: int
    closed_today: int
    crm_synced: int


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/stats", response_model=StatsOut)
async def get_stats(
    org_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Dashboard statistieken voor een organisatie."""

    # Totaal gesprekken
    total = await db.scalar(
        select(func.count(Conversation.id)).where(Conversation.org_id == org_id)
    )

    # Nieuwe leads (status = 'new')
    new_leads = await db.scalar(
        select(func.count(Conversation.id))
        .where(Conversation.org_id == org_id, Conversation.status == "new")
    )

    # Gesloten vandaag
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    closed_today = await db.scalar(
        select(func.count(Conversation.id))
        .where(
            Conversation.org_id == org_id,
            Conversation.status == "closed",
            Conversation.updated_at >= today_start,
        )
    )

    # CRM gesynchroniseerd
    crm_synced = await db.scalar(
        select(func.count(Conversation.id))
        .where(Conversation.org_id == org_id, Conversation.crm_synced_at.isnot(None))
    )

    return StatsOut(
        total_conversations=total or 0,
        new_leads=new_leads or 0,
        closed_today=closed_today or 0,
        crm_synced=crm_synced or 0,
    )


@router.get("/", response_model=list[ConversationOut])
async def list_conversations(
    org_id: str,
    status: Optional[str] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """Haal alle gesprekken op voor een organisatie, inclusief het laatste bericht."""

    query = (
        select(Conversation)
        .where(Conversation.org_id == org_id)
        .order_by(desc(Conversation.updated_at))
        .limit(limit)
    )
    if status:
        query = query.where(Conversation.status == status)

    result = await db.execute(query)
    conversations = result.scalars().all()

    if not conversations:
        return []

    # Last message per gesprek in één query
    conv_ids = [c.id for c in conversations]
    max_sent_subq = (
        select(Message.conversation_id, func.max(Message.sent_at).label("max_sent"))
        .where(Message.conversation_id.in_(conv_ids))
        .group_by(Message.conversation_id)
        .subquery()
    )
    last_msgs_result = await db.execute(
        select(Message).join(
            max_sent_subq,
            (Message.conversation_id == max_sent_subq.c.conversation_id)
            & (Message.sent_at == max_sent_subq.c.max_sent),
        )
    )
    last_msgs: dict[str, str] = {
        m.conversation_id: m.content for m in last_msgs_result.scalars().all()
    }

    # Response opbouwen
    out = []
    for conv in conversations:
        data = ConversationOut.model_validate(conv)
        data.last_message = last_msgs.get(conv.id)
        out.append(data)
    return out


@router.get("/{conversation_id}", response_model=ConversationOut)
async def get_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Haal één gesprek op."""
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Gesprek niet gevonden")
    return conv


@router.get("/{conversation_id}/messages", response_model=list[MessageOut])
async def get_messages(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Haal alle berichten op voor een gesprek."""
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.sent_at)
    )
    return result.scalars().all()


@router.patch("/{conversation_id}/status")
async def update_status(
    conversation_id: str,
    status: str,
    db: AsyncSession = Depends(get_db),
):
    """Pas de status van een gesprek aan."""
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=404, detail="Gesprek niet gevonden")

    valid_statuses = ["new", "in_progress", "appointment_set", "closed"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Geldige statussen: {valid_statuses}")

    conversation.status = status
    await db.commit()
    return {"success": True, "status": status}
