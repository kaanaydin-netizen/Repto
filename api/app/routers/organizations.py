"""
Organizations API — aanmaken en beheren van klant-organisaties.
"""
from __future__ import annotations
import json
import uuid
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.conversation import Organization
from app.auth import get_current_user_id, require_org_access, auth_is_active

router = APIRouter(prefix="/organizations", tags=["organizations"])


# ─── Schemas ──────────────────────────────────────────────────────────────────

class AirtableCredentials(BaseModel):
    api_key: str
    base_id: str
    table_name: str = "Leads"


class OrganizationCreate(BaseModel):
    name: str
    sector: str = "algemeen"
    ai_tone: str = "formeel"
    ai_system_prompt: Optional[str] = None
    whatsapp_number: Optional[str] = None
    whatsapp_phone_number_id: Optional[str] = None
    crm_type: str = "none"
    airtable: Optional[AirtableCredentials] = None
    clerk_user_id: Optional[str] = None  # multi-tenant: koppeling met Clerk gebruiker


class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    sector: Optional[str] = None
    ai_tone: Optional[str] = None
    ai_system_prompt: Optional[str] = None
    whatsapp_number: Optional[str] = None
    whatsapp_phone_number_id: Optional[str] = None
    crm_type: Optional[str] = None
    airtable: Optional[AirtableCredentials] = None


class OrganizationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    sector: Optional[str]
    ai_tone: str
    ai_system_prompt: Optional[str]
    whatsapp_number: Optional[str]
    whatsapp_phone_number_id: Optional[str]
    crm_type: str
    clerk_user_id: Optional[str] = None  # nodig zodat de frontend ongeclaimde orgs herkent
    created_at: Optional[datetime] = None


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _serialize_crm(crm_type: str, airtable: Optional[AirtableCredentials]) -> Optional[str]:
    if crm_type == "airtable" and airtable:
        return json.dumps({
            "api_key":    airtable.api_key,
            "base_id":    airtable.base_id,
            "table_name": airtable.table_name,
        })
    return None


def _resolve_crm_credentials(
    current: Optional[str],
    crm_type: str,
    airtable: Optional[AirtableCredentials],
) -> Optional[str]:
    """
    Bepaal crm_credentials_encrypted bij een organisatie-update.

    - Een ander CRM-type dan airtable (bv. 'none') → credentials wissen.
    - Airtable mét nieuwe credentials → overschrijven.
    - Airtable zónder nieuwe credentials → bestaande behouden (de UI laat het
      tokenveld bewust leeg = "niet wijzigen"). Voorheen werden ze hier gewist.
    """
    if crm_type != "airtable":
        return None
    if airtable:
        return _serialize_crm("airtable", airtable)
    return current


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/", response_model=list[OrganizationOut])
async def list_organizations(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Haal organisaties op voor de ingelogde gebruiker.
    Auth aan: strikt gefilterd op clerk_user_id uit het token.
    Auth uit (legacy): alle organisaties.
    """
    query = select(Organization).order_by(Organization.name)
    if auth_is_active():
        query = query.where(Organization.clerk_user_id == user_id)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/", response_model=OrganizationOut, status_code=201)
async def create_organization(
    data: OrganizationCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Maak een nieuwe klant-organisatie aan.
    De eigenaar (clerk_user_id) komt uit het geverifieerde token — NIET uit de
    request body (anders kan een aanvaller een org op andermans naam zetten).
    """
    owner = user_id if auth_is_active() else data.clerk_user_id
    org = Organization(
        id=str(uuid.uuid4()),
        name=data.name,
        sector=data.sector,
        ai_tone=data.ai_tone,
        ai_system_prompt=data.ai_system_prompt,
        whatsapp_number=data.whatsapp_number,
        whatsapp_phone_number_id=data.whatsapp_phone_number_id,
        crm_type=data.crm_type,
        crm_credentials_encrypted=_serialize_crm(data.crm_type, data.airtable),
        clerk_user_id=owner,
    )
    db.add(org)
    await db.commit()
    await db.refresh(org)
    return org


@router.post("/{org_id}/claim", response_model=OrganizationOut)
async def claim_organization(
    org_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Eenmalige claim: koppel een nog-ongeclaimde org aan de ingelogde gebruiker.
    Alleen toegestaan als clerk_user_id nog NULL is — zo kan de bestaande
    geseede org één keer aan de eerste eigenaar gehangen worden zonder DB-werk.
    """
    result = await db.execute(select(Organization).where(Organization.id == org_id))
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Organisatie niet gevonden")
    if org.clerk_user_id and org.clerk_user_id != user_id:
        raise HTTPException(status_code=403, detail="Deze organisatie is al geclaimd")
    if auth_is_active():
        org.clerk_user_id = user_id
        await db.commit()
        await db.refresh(org)
    return org


@router.get("/{org_id}", response_model=OrganizationOut)
async def get_organization(
    org_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Haal één organisatie op (alleen eigen org bij auth aan)."""
    return await require_org_access(org_id, user_id, db)


@router.patch("/{org_id}", response_model=OrganizationOut)
async def update_organization(
    org_id: str,
    data: OrganizationUpdate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Pas een bestaande organisatie aan (alleen eigen org bij auth aan)."""
    org = await require_org_access(org_id, user_id, db)

    if data.name is not None:
        org.name = data.name
    if data.sector is not None:
        org.sector = data.sector
    if data.ai_tone is not None:
        org.ai_tone = data.ai_tone
    if data.ai_system_prompt is not None:
        org.ai_system_prompt = data.ai_system_prompt
    if data.whatsapp_number is not None:
        org.whatsapp_number = data.whatsapp_number
    if data.whatsapp_phone_number_id is not None:
        org.whatsapp_phone_number_id = data.whatsapp_phone_number_id
    if data.crm_type is not None:
        org.crm_credentials_encrypted = _resolve_crm_credentials(
            org.crm_credentials_encrypted, data.crm_type, data.airtable
        )
        org.crm_type = data.crm_type

    await db.commit()
    await db.refresh(org)
    return org
