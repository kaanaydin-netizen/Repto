"""
Identity Service — kanaal-overschrijdende contact-identiteit + lead-scoring.

Kern van de differentiator (dossier §3.3 + §3.4): één persoon = één lead, herkend over
kanalen heen via een GENORMALISEERDE e-mail OF telefoonsleutel. De normalisatie moet de
drie WhatsApp-/invoervormen van hetzelfde nummer naar dezelfde sleutel reduceren —
faalt dat, dan ontstaan duplicaten en valt de hele differentiator om.

Scoring is bewust DETERMINISTISCH en transparant (dossier §3.4: configureerbaar, geen extra
LLM-call), zodat de klant kan zien waaróm een lead warm/lauw/koud is.
"""
from __future__ import annotations
import json
import re
import uuid
from typing import Optional, Tuple

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Contact

# Standaard landcode voor nationale nummers zonder landcode (KMO-markt = België).
_DEFAULT_COUNTRY_CODE = "32"


def normalize_email(raw) -> Optional[str]:
    """Lowercase + trim; basisvalidatie (bevat '@'). Geeft None bij leeg/ongeldig."""
    if raw is None:
        return None
    s = str(raw).strip().lower()
    if not s or s in ("null", "none") or "@" not in s:
        return None
    return s


def normalize_phone(raw) -> Optional[str]:
    """
    Reduceer een telefoonnummer tot één canonieke sleutel: internationaal, enkel cijfers,
    zónder '+' (dezelfde vorm als Meta's wa_id, bv. '32470123456').

    Moet de drie vormen van hetzelfde Belgische nummer samenvallen:
      - '32470123456'      (wa_id, zoals Meta het levert)
      - '+32 470 12 34 56' (E.164 met '+', spaties)
      - '0470 12 34 56'    (nationaal, leidende 0)
    """
    if raw is None:
        return None
    s = str(raw).strip()
    if not s:
        return None
    has_plus = s.startswith("+")
    digits = re.sub(r"\D", "", s)
    if not digits:
        return None
    if digits.startswith("00"):
        # internationaal met 00-prefix (bv. 0032...) → landcode
        digits = digits[2:]
    elif not has_plus and digits.startswith("0"):
        # nationaal nummer met leidende 0 → vervang door landcode
        digits = _DEFAULT_COUNTRY_CODE + digits[1:]
    return digits or None


async def resolve_contact(
    db: AsyncSession,
    org_id: str,
    *,
    email=None,
    phone=None,
    name=None,
    channel: str,
) -> Contact:
    """
    Vind-één-of-maak het Contact voor deze persoon binnen org_id.

    Match op genormaliseerde e-mail OF telefoon (dossier §3.3). Bij een match worden
    ontbrekende velden aangevuld en het kanaal toegevoegd. Geen match → nieuw Contact.

    Scope-grens increment 1 (bewust): het geval waarin e-mail Contact B matcht terwijl
    telefoon Contact A matchte (= twee bestaande contacten samenvoegen) wordt NIET
    afgehandeld — dat kan pas optreden zodra er een tweede kanaal (e-mail) bestaat en is
    uitgesteld naar de multi-channel increment.
    """
    norm_email = normalize_email(email)
    norm_phone = normalize_phone(phone)

    contact: Optional[Contact] = None
    if norm_email or norm_phone:
        conditions = []
        if norm_email:
            conditions.append(Contact.email == norm_email)
        if norm_phone:
            conditions.append(Contact.phone == norm_phone)
        result = await db.execute(
            select(Contact).where(Contact.org_id == org_id, or_(*conditions))
        )
        contact = result.scalars().first()

    if contact:
        changed = False
        if norm_email and not contact.email:
            contact.email = norm_email
            changed = True
        if norm_phone and not contact.phone:
            contact.phone = norm_phone
            changed = True
        if name and not contact.name:
            contact.name = name
            changed = True
        channels = _load_channels(contact.channels_json)
        if channel and channel not in channels:
            channels.append(channel)
            contact.channels_json = json.dumps(channels)
            changed = True
        if changed:
            await db.commit()
            await db.refresh(contact)
        return contact

    contact = Contact(
        id=str(uuid.uuid4()),
        org_id=org_id,
        name=name,
        email=norm_email,
        phone=norm_phone,
        first_channel=channel,
        channels_json=json.dumps([channel]) if channel else "[]",
    )
    db.add(contact)
    await db.commit()
    await db.refresh(contact)
    return contact


def _load_channels(raw: Optional[str]) -> list:
    if not raw:
        return []
    try:
        val = json.loads(raw)
        return val if isinstance(val, list) else []
    except (ValueError, TypeError):
        return []


# ─── Lead-scoring (warm / lauw / koud) ──────────────────────────────────────────

_WARME_INTENTIES = {"Offerte", "Afspraak"}
_VAGE_INTENTIES = {"Info", "Anders"}
_HOGE_URGENTIE = {"Hoog", "Spoed"}


def compute_lead_score(lead: dict) -> Tuple[str, str]:
    """
    Deterministische warm/lauw/koud-score met transparante reden (dossier §3.4).

    Input = de reeds geëxtraheerde lead-velden (intentie, urgentie, gewenste_datum, …).
    Regels (baseline; later per sector uitbreidbaar):
      - warm: koopintentie (Offerte/Afspraak) ÉN een dringend-signaal (hoge urgentie of
        een concrete gewenste datum).
      - koud: vage intentie (Info/Anders) ZONDER datum en zonder hoge urgentie.
      - lauw: al de rest.

    Geeft (score, reden) terug. score ∈ {"warm","lauw","koud"} (lowercase).
    """
    intentie = (lead.get("intentie") or "Anders").strip()
    urgentie = lead.get("urgentie")
    heeft_datum = _has_value(lead.get("gewenste_datum"))
    hoge_urgentie = (urgentie in _HOGE_URGENTIE)

    if intentie in _WARME_INTENTIES and (hoge_urgentie or heeft_datum):
        redenen = [f"koopintentie '{intentie}'"]
        if hoge_urgentie:
            redenen.append(f"urgentie '{urgentie}'")
        if heeft_datum:
            redenen.append("concrete datum")
        return "warm", "Warm — " + ", ".join(redenen) + "."

    if intentie in _VAGE_INTENTIES and not heeft_datum and not hoge_urgentie:
        return "koud", f"Koud — vage intentie '{intentie}', geen datum of hoge urgentie."

    redenen = [f"intentie '{intentie}'"]
    if heeft_datum:
        redenen.append("wel een datum")
    if hoge_urgentie:
        redenen.append(f"urgentie '{urgentie}'")
    return "lauw", "Lauw — " + ", ".join(redenen) + "."


def _has_value(val) -> bool:
    if val is None:
        return False
    s = str(val).strip()
    return bool(s) and s.lower() not in ("null", "none")
