"""
Tests voor de web-form intake (increment 2, slice 2a) + het kanaal-overschrijdende
profiel (DoD §3) inclusief opruiming van verweesde Airtable-records na een merge.

In-memory SQLite; geen extern verkeer. De Airtable-client wordt gemockt waar nodig.
"""
import datetime as dt
import json

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock

from fastapi import HTTPException

from app.models.conversation import (
    Organization, Conversation, Contact, Message, CrmSyncLog,
)
from app.routers.intake import WebFormIn, web_form_intake


# ─── Fixtures ────────────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def session():
    """Schone in-memory SQLite-sessie (modellen via create_all)."""
    from sqlalchemy import select  # noqa: F401 (gemak voor tests)
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from sqlalchemy.pool import StaticPool
    from app.database import Base
    import app.models.conversation  # noqa: F401

    pytest.importorskip("aiosqlite")
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as c:
        await c.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as s:
        yield s
    await engine.dispose()


class _FakeAirtable:
    """Mockt crm_sync_service.httpx.AsyncClient: vangt patches (upserts) + deletes."""
    patches: list = []
    deletes: list = []
    _counter = [0]

    def __init__(self, *a, **k):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    async def patch(self, url, headers=None, json=None):
        _FakeAirtable.patches.append({"url": url, "json": json})
        _FakeAirtable._counter[0] += 1
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {"records": [{"id": f"rec{_FakeAirtable._counter[0]:03d}"}]}
        return resp

    async def delete(self, url, headers=None):
        _FakeAirtable.deletes.append(url)
        resp = MagicMock()
        resp.status_code = 200
        return resp


# ─── Web-form intake (basis) ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_web_form_intake_creates_lead(session):
    """Een web-form-POST maakt één Contact + Conversation(web_form) en zet de score."""
    session.add(Organization(id="org-x", name="X", crm_type="none"))
    await session.commit()

    out = await web_form_intake(
        WebFormIn(org_id="org-x", name="Jan", email="  JAN@x.be ", message="Ik wil een demo"),
        db=session,
    )

    assert out.ok is True
    assert out.score in ("warm", "lauw", "koud")
    conv = await session.get(Conversation, out.conversation_id)
    assert conv.channel == "web_form"
    assert conv.wa_contact_phone is None          # web-lead heeft geen nummer
    contact = await session.get(Contact, out.contact_id)
    assert contact.email == "jan@x.be"            # genormaliseerd
    assert contact.score == out.score
    assert "web_form" in json.loads(contact.channels_json)


@pytest.mark.asyncio
async def test_web_form_unknown_org_404(session):
    """Onbekende org_id → 404 (géén org raden)."""
    with pytest.raises(HTTPException) as ei:
        await web_form_intake(
            WebFormIn(org_id="bestaat-niet", name="X", email="x@y.be"), db=session
        )
    assert ei.value.status_code == 404


@pytest.mark.asyncio
async def test_web_form_invalid_email_422(session):
    session.add(Organization(id="org-x", name="X", crm_type="none"))
    await session.commit()
    with pytest.raises(HTTPException) as ei:
        await web_form_intake(
            WebFormIn(org_id="org-x", name="X", email="geen-email"), db=session
        )
    assert ei.value.status_code == 422


# ─── Kanaal-overschrijdend profiel + orphan-cleanup (DoD §3) ────────────────────

@pytest.mark.asyncio
async def test_cross_channel_merge_cleans_orphan(session, monkeypatch):
    """
    DoD §3 + orphan-cleanup. B = web-form-contact (ouder, al gesynct → recWEB).
    A = WhatsApp-contact (jonger, al gesynct → recWA). Een WhatsApp-bericht onthult
    dezelfde e-mail → de twee contacten worden ONE profiel (B wint, oudste). De
    verliezer A was al gesynct → diens Airtable-record is verweesd en wordt verwijderd,
    diens CrmSyncLog gereset. B's record (winnaar) blijft.
    """
    from sqlalchemy import select
    from app.services import crm_sync_service as crmmod
    from app.services.whatsapp_service import WhatsAppService

    monkeypatch.setattr(crmmod.httpx, "AsyncClient", _FakeAirtable)
    _FakeAirtable.patches, _FakeAirtable.deletes = [], []

    session.add(Organization(
        id="org-y", name="Y", crm_type="airtable",
        whatsapp_phone_number_id="pnid-y",
        crm_credentials_encrypted=json.dumps(
            {"api_key": "pat", "base_id": "app", "table_name": "Leads"}
        ),
    ))
    # B ouder dan A → B wint de merge.
    t0, t1 = dt.datetime(2026, 1, 1, 10, 0, 0), dt.datetime(2026, 1, 2, 10, 0, 0)
    session.add_all([
        Contact(id="ct-b", org_id="org-y", email="jan@x.be",
                channels_json='["web_form"]', created_at=t0),
        Contact(id="ct-a", org_id="org-y", phone="32470111222",
                channels_json='["whatsapp"]', created_at=t1),
        Conversation(id="cv-web", org_id="org-y", contact_id="ct-b", channel="web_form"),
        Conversation(id="cv-wa", org_id="org-y", contact_id="ct-a", channel="whatsapp",
                     wa_contact_phone="32470111222"),
        # Beide kanalen waren al gesynct naar Airtable.
        CrmSyncLog(id="log-web", conversation_id="cv-web", crm_type="airtable",
                   external_id="recWEB", success=True),
        CrmSyncLog(id="log-wa", conversation_id="cv-wa", crm_type="airtable",
                   external_id="recWA", success=True),
    ])
    for i in range(3):  # verrijkingsdrempel ≥3 berichten
        session.add(Message(id=f"m{i}", conversation_id="cv-wa",
                            direction="inbound", content=f"bericht {i}"))
    await session.commit()

    wa = WhatsAppService(db=session)
    wa.crm_sync._extract_lead_data = AsyncMock(return_value={
        "intentie": "Offerte", "urgentie": "Hoog", "gewenste_datum": None, "email": "jan@x.be",
    })

    lead = await wa.extract_and_enrich(await session.get(Conversation, "cv-wa"))
    assert lead is not None

    # Eén profiel: enkel B over, beide gesprekken hangen aan B.
    session.expire_all()
    contacts = (await session.execute(
        select(Contact).where(Contact.org_id == "org-y")
    )).scalars().all()
    assert [c.id for c in contacts] == ["ct-b"]
    cvs = (await session.execute(
        select(Conversation).where(Conversation.org_id == "org-y")
        .execution_options(populate_existing=True)
    )).scalars().all()
    assert {c.id for c in cvs} == {"cv-web", "cv-wa"}
    assert all(c.contact_id == "ct-b" for c in cvs)

    # Verliezer A's record verweesd → verwijderd + log gereset; winnaar B's record blijft.
    assert any("recWA" in d for d in _FakeAirtable.deletes)
    assert not any("recWEB" in d for d in _FakeAirtable.deletes)
    assert (await session.get(CrmSyncLog, "log-wa")).external_id is None
    assert (await session.get(CrmSyncLog, "log-web")).external_id == "recWEB"
