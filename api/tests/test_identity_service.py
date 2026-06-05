"""
Unit tests voor identity_service.py — kanaal-overschrijdende identiteit + lead-scoring.

Bevat de VERPLICHTE canonicalisatie-test: de drie vormen van hetzelfde Belgische nummer
(wa_id, E.164 met '+', nationaal met leidende 0) moeten naar dezelfde sleutel resolven,
zowel op normalize_phone-niveau als end-to-end via resolve_contact (één Contact).
"""
import json

import pytest
import pytest_asyncio

from app.services.identity_service import (
    normalize_email,
    normalize_phone,
    compute_lead_score,
    resolve_contact,
)


# ─── normalize_email ────────────────────────────────────────────────────────────

def test_normalize_email():
    assert normalize_email("  Jan@Voorbeeld.BE ") == "jan@voorbeeld.be"
    assert normalize_email("geen-email-hier") is None
    assert normalize_email(None) is None
    assert normalize_email("null") is None
    assert normalize_email("") is None


# ─── normalize_phone — VERPLICHTE canonicalisatie ───────────────────────────────

def test_normalize_phone_canonicalisatie():
    """De drie vormen van hetzelfde nummer reduceren tot exact dezelfde sleutel."""
    wa_id = normalize_phone("32470123456")
    e164 = normalize_phone("+32 470 12 34 56")
    nationaal = normalize_phone("0470 12 34 56")
    assert wa_id == e164 == nationaal == "32470123456"


def test_normalize_phone_edges():
    assert normalize_phone("0032470123456") == "32470123456"   # 00-prefix internationaal
    assert normalize_phone("+32 (470) 12-34-56") == "32470123456"
    assert normalize_phone(None) is None
    assert normalize_phone("   ") is None
    assert normalize_phone("geen cijfers") is None


# ─── compute_lead_score ─────────────────────────────────────────────────────────

def test_score_warm():
    score, reason = compute_lead_score(
        {"intentie": "Offerte", "urgentie": "Hoog", "gewenste_datum": None}
    )
    assert score == "warm"
    assert reason  # transparante reden aanwezig
    # koopintentie + concrete datum (zonder hoge urgentie) is ook warm
    score2, _ = compute_lead_score(
        {"intentie": "Afspraak", "urgentie": "Normaal", "gewenste_datum": "2026-06-10"}
    )
    assert score2 == "warm"


def test_score_koud():
    score, _ = compute_lead_score(
        {"intentie": "Info", "urgentie": "Laag", "gewenste_datum": None}
    )
    assert score == "koud"
    score2, _ = compute_lead_score(
        {"intentie": "Anders", "urgentie": None, "gewenste_datum": None}
    )
    assert score2 == "koud"


def test_score_lauw():
    # Koopintentie maar geen urgentie/datum → lauw (niet warm, niet koud).
    score, _ = compute_lead_score(
        {"intentie": "Offerte", "urgentie": "Normaal", "gewenste_datum": None}
    )
    assert score == "lauw"
    # Klacht valt niet onder warm/vaag → lauw.
    score2, _ = compute_lead_score(
        {"intentie": "Klacht", "urgentie": "Hoog", "gewenste_datum": None}
    )
    assert score2 == "lauw"


# ─── resolve_contact (DB-backed, in-memory SQLite) ──────────────────────────────

@pytest_asyncio.fixture
async def session():
    pytest.importorskip("aiosqlite")
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from sqlalchemy.pool import StaticPool
    from app.database import Base
    import app.models.conversation  # noqa: F401 — registreer modellen op Base.metadata

    # StaticPool + één gedeelde connectie: zonder dit krijgt elke connectie een eigen
    # lege in-memory DB en vindt de sessie de net-aangemaakte tabellen niet.
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as s:
        yield s
    await engine.dispose()


@pytest.mark.asyncio
async def test_resolve_contact_phone_dedup_drie_vormen(session):
    """End-to-end: de drie nummer-vormen koppelen aan één Contact."""
    c1 = await resolve_contact(session, "org-1", phone="32470123456", name="Jan", channel="whatsapp")
    c2 = await resolve_contact(session, "org-1", phone="0470 12 34 56", channel="whatsapp")
    c3 = await resolve_contact(session, "org-1", phone="+32 470 12 34 56", channel="email")
    assert c1.id == c2.id == c3.id
    channels = json.loads(c3.channels_json)
    assert "whatsapp" in channels and "email" in channels


@pytest.mark.asyncio
async def test_resolve_contact_email_match(session):
    """Ander nummer maar zelfde (genormaliseerde) e-mail → match op e-mail, geen duplicaat."""
    c1 = await resolve_contact(session, "org-1", phone="32470000001", email="kim@x.be", channel="whatsapp")
    c2 = await resolve_contact(session, "org-1", phone="32999999999", email="KIM@x.be", channel="email")
    assert c1.id == c2.id


@pytest.mark.asyncio
async def test_resolve_contact_no_match_creates_new(session):
    c1 = await resolve_contact(session, "org-1", phone="32470000010", channel="whatsapp")
    c2 = await resolve_contact(session, "org-1", phone="32470000011", channel="whatsapp")
    assert c1.id != c2.id


@pytest.mark.asyncio
async def test_resolve_contact_org_isolatie(session):
    """Zelfde nummer in een andere org mag NIET matchen (multi-tenant scheiding)."""
    c1 = await resolve_contact(session, "org-1", phone="32470000020", channel="whatsapp")
    c2 = await resolve_contact(session, "org-2", phone="32470000020", channel="whatsapp")
    assert c1.id != c2.id
