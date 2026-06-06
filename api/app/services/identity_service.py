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

from sqlalchemy import select, or_, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Contact, Conversation

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

    Botsingsgeval (increment 2): wanneer e-mail Contact B matcht terwijl telefoon
    Contact A matchte (A≠B, twee bestaande contacten), worden ze SAMENGEVOEGD i.p.v.
    willekeurig één te kiezen. Dit kan optreden zodra een tweede kanaal (web/e-mail)
    een persoon aanbrengt die al via WhatsApp bekend was. Zie _merge_contacts.
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
        matches = list(result.scalars().all())
        if len(matches) > 1:
            # e-mail en telefoon wijzen naar verschillende contacten → samenvoegen.
            contact = await _merge_contacts(db, matches)
        elif matches:
            contact = matches[0]

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


async def _merge_contacts(db: AsyncSession, matches: list) -> Contact:
    """
    Voeg meerdere Contacts (e-mail wees naar B, telefoon naar A) samen tot één.

    De WINNAAR is het oudste contact (eerst aangemaakt → langste historiek). Alle
    verliezers worden erin opgenomen:
      - channels_json wordt de UNIE van alle kanalen;
      - ontbrekende velden op de winnaar (email/phone/name/score/score_reason)
        worden aangevuld vanuit een verliezer;
      - alle conversations.contact_id van de verliezers worden HERKOPPELD naar de
        winnaar (Conversation.contact_id is de enige FK naar contacts.id);
      - de verliezer-rij wordt verwijderd.

    Geen commit hier — de aanroeper (resolve_contact) commit samen met de verdere
    verrijking, zodat de hele merge één transactie is.
    """
    # Oudste eerst (langste historiek). created_at kan vóór flush None zijn → die
    # contacten achteraan, tiebreak op id zodat de keuze deterministisch is.
    dated = [c for c in matches if c.created_at is not None]
    if dated:
        winner = min(dated, key=lambda c: (c.created_at, c.id))
    else:
        winner = min(matches, key=lambda c: c.id)

    channels = _load_channels(winner.channels_json)
    for loser in matches:
        if loser.id == winner.id:
            continue
        for ch in _load_channels(loser.channels_json):
            if ch not in channels:
                channels.append(ch)
        if not winner.email and loser.email:
            winner.email = loser.email
        if not winner.phone and loser.phone:
            winner.phone = loser.phone
        if not winner.name and loser.name:
            winner.name = loser.name
        if not winner.score and loser.score:
            winner.score = loser.score
            winner.score_reason = loser.score_reason
        # Herkoppel de gesprekken van de verliezer en verwijder de verliezer.
        await db.execute(
            update(Conversation)
            .where(Conversation.contact_id == loser.id)
            .values(contact_id=winner.id)
        )
        await db.delete(loser)

    winner.channels_json = json.dumps(channels)
    await db.flush()
    return winner


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
