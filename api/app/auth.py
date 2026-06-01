"""
Clerk JWT-verificatie voor multi-tenant beveiliging.

De frontend (browser én Next.js server) stuurt een Clerk session-token mee als
`Authorization: Bearer <jwt>`. Hier verifiëren we dat token tegen de publieke
JWKS van de Clerk-instance en leiden we de gebruiker (`sub` = clerk_user_id) af.

Schakelaar: zolang `settings.clerk_jwks_url` niet is ingesteld, blijft auth UIT
(legacy gedrag, zodat lokaal/CI en de eerste deploy niets breken). Zet de
CLERK_JWKS_URL env-var op Railway om enforcement aan te zetten.
"""
from __future__ import annotations

import time
from typing import Optional

import httpx
from fastapi import Depends, Header, HTTPException
from jose import jwt
from jose.exceptions import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models.conversation import Organization

settings = get_settings()

# In-memory JWKS-cache (de sleutels roteren zelden; 1u TTL volstaat).
_jwks_cache: dict[str, object] = {"keys": None, "fetched_at": 0.0}
_JWKS_TTL = 3600.0


async def _get_jwks() -> dict:
    now = time.time()
    if _jwks_cache["keys"] is not None and now - float(_jwks_cache["fetched_at"]) < _JWKS_TTL:
        return _jwks_cache["keys"]  # type: ignore[return-value]
    async with httpx.AsyncClient(timeout=10) as client:
        res = await client.get(settings.clerk_jwks_url)  # type: ignore[arg-type]
        res.raise_for_status()
        jwks = res.json()
    _jwks_cache["keys"] = jwks
    _jwks_cache["fetched_at"] = now
    return jwks


def _extract_bearer(authorization: Optional[str]) -> Optional[str]:
    if not authorization:
        return None
    parts = authorization.split(" ", 1)
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1].strip()
    return None


async def get_current_user_id(
    authorization: Optional[str] = Header(default=None),
) -> str:
    """
    Verifieer het Clerk-token en geef de clerk_user_id (`sub`) terug.

    Auth uit (geen JWKS geconfigureerd): geef een sentinel terug zodat routes
    blijven werken zoals voorheen. Auth aan: 401 bij ontbrekend/ongeldig token.
    """
    if not settings.auth_enabled:
        # Legacy modus — geen verificatie. De org-filters vallen terug op het
        # oude gedrag (zie require_org_access / list-filters).
        return "__auth_disabled__"

    token = _extract_bearer(authorization)
    if not token:
        raise HTTPException(status_code=401, detail="Geen geldig auth-token")

    try:
        jwks = await _get_jwks()
        # Clerk JWT's gebruiken RS256; aud wordt niet gezet, dus niet verplicht checken.
        claims = jwt.decode(
            token,
            jwks,
            algorithms=["RS256"],
            issuer=settings.clerk_issuer if settings.clerk_issuer else None,
            options={
                "verify_aud": False,
                "verify_iss": bool(settings.clerk_issuer),
            },
        )
    except JWTError:
        raise HTTPException(status_code=401, detail="Token verificatie mislukt")

    sub = claims.get("sub")
    if not sub:
        raise HTTPException(status_code=401, detail="Token mist sub-claim")
    return sub


def auth_is_active() -> bool:
    return settings.auth_enabled


async def require_org_access(
    org_id: str,
    user_id: str,
    db: AsyncSession,
) -> Organization:
    """
    Haal de org op en verifieer dat hij bij de gebruiker hoort.

    - Auth uit: alleen bestaan controleren (legacy).
    - Auth aan: 404 als de org niet bestaat OF niet van deze gebruiker is
      (404 i.p.v. 403 om het bestaan van andermans orgs niet te lekken).
    """
    result = await db.execute(select(Organization).where(Organization.id == org_id))
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Organisatie niet gevonden")
    if settings.auth_enabled and org.clerk_user_id != user_id:
        raise HTTPException(status_code=404, detail="Organisatie niet gevonden")
    return org
