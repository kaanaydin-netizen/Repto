"""
Conversations API — voor het dashboard om gesprekken op te halen en te beheren.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.database import get_db
from app.models.conversation import Conversation, Message

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("/")
async def list_conversations(
    org_id: str,
    status: str | None = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """Haal alle gesprekken op voor een organisatie."""
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
    return conversations


@router.get("/{conversation_id}/messages")
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
