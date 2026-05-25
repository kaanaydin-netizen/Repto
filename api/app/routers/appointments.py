"""
Appointments API — beheer van afspraken ingepland via de AI-receptionist.
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.conversation import Appointment

router = APIRouter(prefix="/appointments", tags=["appointments"])


# ─── Schemas ──────────────────────────────────────────────────────────────────

class AppointmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    conversation_id: str
    org_id: str
    title: str
    start_at: datetime
    end_at: datetime
    status: str
    reminder_sent: bool
    google_event_id: Optional[str] = None
    created_at: Optional[datetime] = None


class AppointmentCreate(BaseModel):
    conversation_id: str
    org_id: str
    title: str
    start_at: datetime
    end_at: datetime
    status: str = "confirmed"


class AppointmentUpdate(BaseModel):
    title: Optional[str] = None
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    status: Optional[str] = None


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/", response_model=list[AppointmentOut])
async def list_appointments(
    org_id: str,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Haal alle afspraken op voor een organisatie.
    Optioneel filteren op status (confirmed / cancelled).
    Gesorteerd op start_at oplopend.
    """
    query = select(Appointment).where(Appointment.org_id == org_id)
    if status:
        query = query.where(Appointment.status == status)
    query = query.order_by(Appointment.start_at.asc())
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{appointment_id}", response_model=AppointmentOut)
async def get_appointment(
    appointment_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Haal één afspraak op."""
    result = await db.execute(
        select(Appointment).where(Appointment.id == appointment_id)
    )
    appt = result.scalar_one_or_none()
    if not appt:
        raise HTTPException(status_code=404, detail="Afspraak niet gevonden")
    return appt


@router.patch("/{appointment_id}", response_model=AppointmentOut)
async def update_appointment(
    appointment_id: str,
    data: AppointmentUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Pas een afspraak aan (bijv. annuleren of verzetten)."""
    result = await db.execute(
        select(Appointment).where(Appointment.id == appointment_id)
    )
    appt = result.scalar_one_or_none()
    if not appt:
        raise HTTPException(status_code=404, detail="Afspraak niet gevonden")

    if data.title is not None:
        appt.title = data.title
    if data.start_at is not None:
        appt.start_at = data.start_at
    if data.end_at is not None:
        appt.end_at = data.end_at
    if data.status is not None:
        appt.status = data.status

    await db.commit()
    await db.refresh(appt)
    return appt
