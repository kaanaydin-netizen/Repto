"""
Database modellen voor Repto.
Gebruik van SQLAlchemy 2.0 Mapped-stijl, compatibel met Python 3.9.
GEEN from __future__ import annotations — dit botst met SQLAlchemy op Python 3.9.
"""
from typing import Optional, List
from sqlalchemy import String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.database import Base
import enum


class ConversationStatus(str, enum.Enum):
    new = "new"
    in_progress = "in_progress"
    appointment_set = "appointment_set"
    closed = "closed"


class CrmType(str, enum.Enum):
    airtable = "airtable"
    google_sheets = "google_sheets"  # legacy
    hubspot = "hubspot"
    pipedrive = "pipedrive"
    none = "none"


class Contact(Base):
    """
    Eén persoon = één lead, kanaal-overschrijdend (dossier §3.3, kerndifferentiator).
    Meerdere gesprekken (ook over meerdere kanalen) mappen op één Contact via match op
    genormaliseerde e-mail OF telefoon. email/phone worden GENORMALISEERD opgeslagen
    (zie identity_service.normalize_email / normalize_phone) zodat matching betrouwbaar is.
    """
    __tablename__ = "contacts"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    org_id: Mapped[str] = mapped_column(String, ForeignKey("organizations.id"), nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String)
    email: Mapped[Optional[str]] = mapped_column(String)          # genormaliseerd (lowercase/trim)
    phone: Mapped[Optional[str]] = mapped_column(String)          # genormaliseerd (wa_id-vorm: int. zonder '+')
    first_channel: Mapped[Optional[str]] = mapped_column(String)  # bv. "whatsapp"
    channels_json: Mapped[str] = mapped_column(Text, default="[]")  # JSON-lijst van kanalen
    score: Mapped[Optional[str]] = mapped_column(String)          # "warm" | "lauw" | "koud"
    score_reason: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    conversations: Mapped[List["Conversation"]] = relationship(back_populates="contact")


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    sector: Mapped[Optional[str]] = mapped_column(String)
    whatsapp_number: Mapped[Optional[str]] = mapped_column(String)
    whatsapp_phone_number_id: Mapped[Optional[str]] = mapped_column(String)
    # AI configuratie
    ai_system_prompt: Mapped[Optional[str]] = mapped_column(Text)
    ai_tone: Mapped[str] = mapped_column(String, default="formeel")
    # CRM
    crm_type: Mapped[str] = mapped_column(String, default="none")
    crm_credentials_encrypted: Mapped[Optional[str]] = mapped_column(Text)
    crm_sheet_id: Mapped[Optional[str]] = mapped_column(String)
    # Multi-tenant: koppeling met Clerk gebruiker
    clerk_user_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())

    conversations: Mapped[List["Conversation"]] = relationship(back_populates="organization")


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    org_id: Mapped[str] = mapped_column(String, ForeignKey("organizations.id"), nullable=False)
    contact_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey("contacts.id"), nullable=True)
    wa_contact_phone: Mapped[str] = mapped_column(String, nullable=False)
    wa_contact_name: Mapped[Optional[str]] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="new")
    crm_synced_at: Mapped[Optional[DateTime]] = mapped_column(DateTime)
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    organization: Mapped["Organization"] = relationship(back_populates="conversations")
    contact: Mapped[Optional["Contact"]] = relationship(back_populates="conversations")
    messages: Mapped[List["Message"]] = relationship(back_populates="conversation")
    appointments: Mapped[List["Appointment"]] = relationship(back_populates="conversation")
    followup_tasks: Mapped[List["FollowupTask"]] = relationship(back_populates="conversation")


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    conversation_id: Mapped[str] = mapped_column(String, ForeignKey("conversations.id"), nullable=False)
    direction: Mapped[str] = mapped_column(String, nullable=False)  # 'inbound' | 'outbound'
    content: Mapped[str] = mapped_column(Text, nullable=False)
    ai_generated: Mapped[bool] = mapped_column(Boolean, default=False)
    wa_message_id: Mapped[Optional[str]] = mapped_column(String)
    sent_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())

    conversation: Mapped["Conversation"] = relationship(back_populates="messages")


class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    conversation_id: Mapped[str] = mapped_column(String, ForeignKey("conversations.id"), nullable=False)
    org_id: Mapped[str] = mapped_column(String, ForeignKey("organizations.id"), nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    start_at: Mapped[DateTime] = mapped_column(DateTime, nullable=False)
    end_at: Mapped[DateTime] = mapped_column(DateTime, nullable=False)
    status: Mapped[str] = mapped_column(String, default="confirmed")
    reminder_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    google_event_id: Mapped[Optional[str]] = mapped_column(String)
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())

    conversation: Mapped["Conversation"] = relationship(back_populates="appointments")


class FollowupTask(Base):
    __tablename__ = "followup_tasks"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    conversation_id: Mapped[str] = mapped_column(String, ForeignKey("conversations.id"), nullable=False)
    send_at: Mapped[DateTime] = mapped_column(DateTime, nullable=False)
    message_template: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String, default="pending")

    conversation: Mapped["Conversation"] = relationship(back_populates="followup_tasks")


class CrmSyncLog(Base):
    __tablename__ = "crm_sync_log"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    conversation_id: Mapped[str] = mapped_column(String, ForeignKey("conversations.id"), nullable=False)
    crm_type: Mapped[str] = mapped_column(String, nullable=False)
    external_id: Mapped[Optional[str]] = mapped_column(String)
    synced_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
    success: Mapped[bool] = mapped_column(Boolean, default=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
