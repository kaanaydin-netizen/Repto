"""
Tests voor de e-mail-intake (increment 2b, Resend Inbound):
- Svix-signatureverificatie (geldig/ongeldig/replay).
- org-routing uit het To-adres (plus-addressing).
- loop-/spam-guard (Auto-Submitted/List-*).
- end-to-end intake (body gemockt, Haiku gemockt) → lead + score + bericht.
- max ÉÉN opvolgmail bij ontbrekende velden.

In-memory SQLite; process_inbound_email opent zijn eigen sessie → we monkeypatchen
AsyncSessionLocal naar een SQLite-maker.
"""
import base64
import hashlib
import hmac
import time

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
import app.models.conversation  # noqa: F401
from app.models.conversation import Organization, Conversation, Contact, Message


# ─── Pure helpers ───────────────────────────────────────────────────────────────

def test_extract_org_id():
    from app.services.email_intake_service import extract_org_id
    dom = "inbound.repto.be"
    assert extract_org_id(["intake+org-123@inbound.repto.be"], dom) == "org-123"
    assert extract_org_id(['"Klant" <intake+abc@inbound.repto.be>'], dom) == "abc"
    assert extract_org_id(["intake+x@INBOUND.REPTO.BE"], dom) == "x"   # domein case-insensitief
    assert extract_org_id(["intake@inbound.repto.be"], dom) is None    # geen plus
    assert extract_org_id(["intake+x@ander.be"], dom) is None          # ander domein
    assert extract_org_id(["intake+x@inbound.repto.be"], None) is None  # geen domein geconfigureerd


def test_is_auto_or_list_mail():
    from app.services.email_intake_service import is_auto_or_list_mail
    assert is_auto_or_list_mail({"Auto-Submitted": "auto-replied"}) is True
    assert is_auto_or_list_mail({"auto-submitted": "no"}) is False
    assert is_auto_or_list_mail({"List-Unsubscribe": "<...>"}) is True
    assert is_auto_or_list_mail({"Precedence": "bulk"}) is True
    assert is_auto_or_list_mail({"From": "jan@x.be"}) is False
    assert is_auto_or_list_mail(None) is False


# ─── Svix-signatureverificatie ──────────────────────────────────────────────────

def _sign(secret_raw: bytes, svix_id: str, ts: str, body: bytes) -> str:
    signed = f"{svix_id}.{ts}.".encode() + body
    return base64.b64encode(hmac.new(secret_raw, signed, hashlib.sha256).digest()).decode()


def test_resend_signature_valid(monkeypatch):
    from app.routers import webhooks
    secret_raw = b"super-secret-key"
    whsec = "whsec_" + base64.b64encode(secret_raw).decode()
    monkeypatch.setattr(webhooks.settings, "resend_webhook_secret", whsec)

    body = b'{"type":"email.received"}'
    ts = str(int(time.time()))
    sig = _sign(secret_raw, "msg_1", ts, body)
    headers = {"svix-id": "msg_1", "svix-timestamp": ts, "svix-signature": f"v1,{sig}"}

    assert webhooks._resend_signature_valid(body, headers) is True
    # Verkeerde body → ongeldig.
    assert webhooks._resend_signature_valid(b'{"tampered":true}', headers) is False
    # Ontbrekende headers → ongeldig.
    assert webhooks._resend_signature_valid(body, {}) is False
    # Oude timestamp (replay) → ongeldig.
    old_ts = str(int(time.time()) - 4000)
    old_sig = _sign(secret_raw, "msg_1", old_ts, body)
    assert webhooks._resend_signature_valid(
        body, {"svix-id": "msg_1", "svix-timestamp": old_ts, "svix-signature": f"v1,{old_sig}"}
    ) is False


def test_resend_signature_disabled_when_no_secret(monkeypatch):
    from app.routers import webhooks
    monkeypatch.setattr(webhooks.settings, "resend_webhook_secret", None)
    assert webhooks._resend_signature_valid(b"{}", {}) is True  # verificatie uit (dev)


# ─── End-to-end intake ──────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def intake_maker(monkeypatch):
    """In-memory SQLite + gepatchte AsyncSessionLocal; seed één org (crm_type=none)."""
    pytest.importorskip("aiosqlite")
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False}, poolclass=StaticPool,
    )
    async with engine.begin() as c:
        await c.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as s:
        s.add(Organization(id="org-e", name="E", crm_type="none"))
        await s.commit()

    import app.services.email_intake_service as mod
    monkeypatch.setattr(mod, "AsyncSessionLocal", maker)
    monkeypatch.setattr(mod.settings, "email_intake_domain", "inbound.repto.be")
    yield maker
    await engine.dispose()


@pytest.mark.asyncio
async def test_inbound_email_creates_lead(intake_maker, monkeypatch):
    import app.services.email_intake_service as mod
    from app.services.crm_sync_service import CrmSyncService

    monkeypatch.setattr(mod, "_fetch_email_body", AsyncMock(return_value={
        "from": "Jan Janssen <jan@x.be>", "text": "Ik wil een offerte voor een keuring.",
        "html": None, "headers": {"from": "jan@x.be"},
    }))
    monkeypatch.setattr(CrmSyncService, "_extract_lead_data", AsyncMock(return_value={
        "naam": "Jan Janssen", "adres": None, "email": "jan@x.be", "type_werk": "keuring",
        "gewenste_datum": None, "urgentie": "Hoog", "intentie": "Offerte",
        "samenvatting": "keuring", "opvolging_nodig": False, "opvolg_reden": None, "opvolg_datum": None,
    }))
    followup = AsyncMock(return_value=True)
    monkeypatch.setattr(mod, "send_followup_email", followup)

    await mod.process_inbound_email(
        email_id="em-1", to_list=["intake+org-e@inbound.repto.be"],
        from_addr="Jan Janssen <jan@x.be>", subject="Offerte keuring",
    )

    async with intake_maker() as s:
        convs = (await s.execute(select(Conversation))).scalars().all()
        assert len(convs) == 1 and convs[0].channel == "email"
        contacts = (await s.execute(select(Contact))).scalars().all()
        assert len(contacts) == 1
        assert contacts[0].email == "jan@x.be"
        assert contacts[0].score == "warm"          # Offerte + Hoog
        msgs = (await s.execute(select(Message))).scalars().all()
        assert any(m.direction == "inbound" for m in msgs)
    # Lead compleet (naam + type werk) → geen opvolgmail.
    followup.assert_not_awaited()


@pytest.mark.asyncio
async def test_inbound_email_followup_once_when_fields_missing(intake_maker, monkeypatch):
    import app.services.email_intake_service as mod
    from app.services.crm_sync_service import CrmSyncService

    monkeypatch.setattr(mod, "_fetch_email_body", AsyncMock(return_value={
        "from": "anon@x.be", "text": "hallo", "html": None, "headers": {},
    }))
    # Ontbrekende naam + type_werk → opvolgmail verwacht.
    monkeypatch.setattr(CrmSyncService, "_extract_lead_data", AsyncMock(return_value={
        "naam": None, "adres": None, "email": None, "type_werk": None,
        "gewenste_datum": None, "urgentie": None, "intentie": "Info",
        "samenvatting": None, "opvolging_nodig": False, "opvolg_reden": None, "opvolg_datum": None,
    }))
    followup = AsyncMock(return_value=True)
    monkeypatch.setattr(mod, "send_followup_email", followup)

    kw = dict(email_id="em-2", to_list=["intake+org-e@inbound.repto.be"],
              from_addr="anon@x.be", subject="")
    await mod.process_inbound_email(**kw)
    await mod.process_inbound_email(**kw)   # tweede mail, zelfde gesprek

    # Precies ÉÉN opvolgmail over beide mails heen.
    assert followup.await_count == 1
    async with intake_maker() as s:
        out = await s.scalar(select(func.count(Message.id)).where(Message.direction == "outbound"))
        assert out == 1


@pytest.mark.asyncio
async def test_inbound_email_autoreply_ignored(intake_maker, monkeypatch):
    import app.services.email_intake_service as mod

    monkeypatch.setattr(mod, "_fetch_email_body", AsyncMock(return_value={
        "from": "jan@x.be", "text": "out of office", "html": None,
        "headers": {"Auto-Submitted": "auto-replied"},
    }))

    await mod.process_inbound_email(
        email_id="em-3", to_list=["intake+org-e@inbound.repto.be"],
        from_addr="jan@x.be", subject="Automatic reply",
    )
    async with intake_maker() as s:
        assert (await s.scalar(select(func.count(Conversation.id)))) == 0   # niets aangemaakt


@pytest.mark.asyncio
async def test_inbound_email_unknown_org_ignored(intake_maker, monkeypatch):
    import app.services.email_intake_service as mod
    fetch = AsyncMock(return_value={"from": "jan@x.be", "text": "hoi", "headers": {}})
    monkeypatch.setattr(mod, "_fetch_email_body", fetch)

    # Onbekende org in het To-adres → genegeerd, body wordt niet eens opgehaald.
    await mod.process_inbound_email(
        email_id="em-4", to_list=["intake+bestaat-niet@inbound.repto.be"],
        from_addr="jan@x.be", subject="hoi",
    )
    # extract_org_id geeft wel "bestaat-niet" terug; org-lookup faalt → genegeerd.
    async with intake_maker() as s:
        assert (await s.scalar(select(func.count(Conversation.id)))) == 0
