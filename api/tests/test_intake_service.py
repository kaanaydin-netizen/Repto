"""
Tests voor de web-form intake (increment 2, slice 2a) + het kanaal-overschrijdende
profiel (DoD §3) inclusief opruiming van verweesde Airtable-records na een merge.

In-memory SQLite; geen extern verkeer. De Airtable-client wordt gemockt waar nodig.
"""
import datetime as dt
import json

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import HTTPException

from sqlalchemy import select, func

from app.models.conversation import (
    Organization, Conversation, Contact, Message, CrmSyncLog, Appointment,
)
from app.routers.intake import WebFormIn, web_form_intake, WebChatIn, web_chat_intake


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


@pytest.mark.asyncio
async def test_web_form_closes_and_reuses_on_resubmit(session):
    """
    Een web-form is een eenmalige, volledige inzending: het gesprek wordt meteen 'closed'
    (telt niet als actief gesprek; levert met opvolging_nodig Airtable-status 'Op te volgen').
    Een herinzending door dezelfde persoon hergebruikt hetzelfde gesprek — geen rij-proliferatie.
    """
    from app.routers.intake import _build_lead
    from app.services.crm_sync_service import _pipeline_status

    session.add(Organization(id="org-x", name="X", crm_type="none"))
    await session.commit()

    out1 = await web_form_intake(
        WebFormIn(org_id="org-x", name="Jan", email="jan@x.be", message="Demo graag"), db=session)
    conv1 = await session.get(Conversation, out1.conversation_id)
    assert conv1.status == "closed"

    # Eenmalige inzending → Airtable-pijplijn 'Op te volgen' (closed + opvolging_nodig).
    lead = _build_lead(WebFormIn(org_id="org-x", name="Jan", email="jan@x.be", message="Demo graag"))
    assert lead["opvolging_nodig"] is True
    assert _pipeline_status(conv1, has_appointment=False, lead=lead) == "Op te volgen"

    # Herinzending zelfde persoon → zelfde gesprek hergebruikt, geen tweede rij.
    out2 = await web_form_intake(
        WebFormIn(org_id="org-x", name="Jan", email="jan@x.be", message="Nog een vraag"), db=session)
    assert out2.conversation_id == out1.conversation_id
    convs = (await session.execute(
        select(Conversation).where(Conversation.org_id == "org-x",
                                   Conversation.channel == "web_form")
    )).scalars().all()
    assert len(convs) == 1


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


# ─── Web-chat intake (slice 2c) ────────────────────────────────────────────────


def _stub_ai(monkeypatch, reply: str):
    """Vervang de Anthropic-call (generate_reply) door een vaste reply, zodat de
    endpoint-orchestratie getest wordt zonder extern AI-verkeer."""
    from app.services.ai_service import AIService
    monkeypatch.setattr(AIService, "generate_reply", AsyncMock(return_value=reply))


def _stub_extract(monkeypatch, lead: dict):
    """Vervang de lead-extractie (Haiku) door een vaste dict — extract_and_enrich draait
    pas vanaf ≥3 berichten, dus dit moet gezet zijn zodra een tweede beurt wordt gepost."""
    from app.services.crm_sync_service import CrmSyncService
    monkeypatch.setattr(CrmSyncService, "_extract_lead_data", AsyncMock(return_value=lead))


@pytest.mark.asyncio
async def test_web_chat_multi_turn_continuity(session, monkeypatch):
    """
    HET kenmerk van web-chat t.o.v. web-form: een sessie loopt over meerdere beurten.
    Twee POSTs met hetzelfde session_id moeten exact HETZELFDE Conversation-record
    treffen (deterministische uuid5-contract) en de berichtgeschiedenis moet groeien
    (2 berichten per beurt: inbound + outbound).
    """
    _stub_ai(monkeypatch, reply="Hoi! Waarmee kan ik helpen?")
    _stub_extract(monkeypatch, {"intentie": None, "urgentie": None,
                                "gewenste_datum": None, "email": None})
    session.add(Organization(id="org-c", name="C", crm_type="none"))
    await session.commit()

    out1 = await web_chat_intake(
        WebChatIn(org_id="org-c", session_id="sess-1", message="Hallo"), db=session,
    )
    out2 = await web_chat_intake(
        WebChatIn(org_id="org-c", session_id="sess-1", message="Ik zoek een afspraak"),
        db=session,
    )

    # Zelfde gesprek over beide beurten.
    assert out1.session_id == out2.session_id == "sess-1"
    convs = (await session.execute(
        select(Conversation).where(Conversation.org_id == "org-c")
    )).scalars().all()
    assert len(convs) == 1
    assert convs[0].channel == "web_chat"
    # 2 beurten × (inbound + outbound) = 4 berichten in één gesprek.
    msg_count = (await session.execute(
        select(func.count()).select_from(Message)
        .where(Message.conversation_id == convs[0].id)
    )).scalar_one()
    assert msg_count == 4


@pytest.mark.asyncio
async def test_web_chat_closing_tag_closes_and_notifies(session, monkeypatch):
    """[GESPREK_AFGEROND] in de reply → status='closed', tag uit de reply gestript,
    en de agency-notificatie precies één keer verstuurd."""
    _stub_ai(monkeypatch, reply="Top, tot dan! [GESPREK_AFGEROND]")
    _stub_extract(monkeypatch, {"intentie": None, "urgentie": None,
                                "gewenste_datum": None, "email": None})
    notify = AsyncMock()
    monkeypatch.setattr("app.routers.intake.send_lead_notification", notify)
    session.add(Organization(id="org-c", name="C", crm_type="none"))
    await session.commit()

    out = await web_chat_intake(
        WebChatIn(org_id="org-c", session_id="sess-x", message="Bedankt!"), db=session,
    )

    assert out.closed is True
    assert "[GESPREK_AFGEROND]" not in out.reply
    assert out.reply == "Top, tot dan!"
    conv = (await session.execute(
        select(Conversation).where(Conversation.org_id == "org-c")
    )).scalar_one()
    assert conv.status == "closed"
    notify.assert_awaited_once()


@pytest.mark.asyncio
async def test_web_chat_open_turn_does_not_notify(session, monkeypatch):
    """Een gewone (niet-afgeronde) beurt verstuurt GEEN notificatie."""
    _stub_ai(monkeypatch, reply="Kunt u meer vertellen?")
    notify = AsyncMock()
    monkeypatch.setattr("app.routers.intake.send_lead_notification", notify)
    session.add(Organization(id="org-c", name="C", crm_type="none"))
    await session.commit()

    out = await web_chat_intake(
        WebChatIn(org_id="org-c", session_id="sess-o", message="Hoi"), db=session,
    )
    assert out.closed is False
    notify.assert_not_awaited()


@pytest.mark.asyncio
async def test_web_chat_crm_gate_below_three_messages(session, monkeypatch):
    """CRM-sync wacht — net als WhatsApp — op ≥3 berichten. Eén beurt (2 berichten)
    mag nog niet naar Airtable schrijven."""
    from app.services import crm_sync_service as crmmod
    monkeypatch.setattr(crmmod.httpx, "AsyncClient", _FakeAirtable)
    _FakeAirtable.patches, _FakeAirtable.deletes = [], []
    _stub_ai(monkeypatch, reply="Welkom!")
    session.add(Organization(
        id="org-c", name="C", crm_type="airtable",
        crm_credentials_encrypted=json.dumps(
            {"api_key": "pat", "base_id": "app", "table_name": "Leads"}
        ),
    ))
    await session.commit()

    await web_chat_intake(
        WebChatIn(org_id="org-c", session_id="sess-g", message="Hoi"), db=session,
    )
    assert _FakeAirtable.patches == []  # te vroeg om te syncen


@pytest.mark.asyncio
async def test_web_chat_email_revealed_merges_into_existing_contact(session, monkeypatch):
    """
    DoD §3 voor web-chat: een bezoeker start ANONIEM (geen e-mail), noemt later z'n
    e-mail in de chat. Bestaat er al een Contact met die e-mail (via web-form), dan
    worden ze ÉÉN profiel — geen tweede contact met dezelfde e-mail. Bewijst dat het
    web_chat-kanaal door dezelfde merge-poort (extract_and_enrich → resolve_contact) loopt.
    """
    _stub_ai(monkeypatch, reply="Genoteerd!")
    _stub_extract(monkeypatch, {"intentie": "Offerte", "urgentie": "Hoog",
                                "gewenste_datum": None, "email": "jan@x.be"})
    session.add(Organization(id="org-c", name="C", crm_type="none"))
    # Bestaand web-form-contact met dezelfde e-mail (ouder → wint de merge).
    session.add(Contact(id="ct-web", org_id="org-c", email="jan@x.be",
                        channels_json='["web_form"]',
                        created_at=dt.datetime(2026, 1, 1, 10, 0, 0)))
    await session.commit()

    # Twee beurten → 4 berichten ≥ 3 → extract_and_enrich vuurt op beurt 2 en onthult de e-mail.
    await web_chat_intake(
        WebChatIn(org_id="org-c", session_id="sess-m", message="Hoi"), db=session,
    )
    await web_chat_intake(
        WebChatIn(org_id="org-c", session_id="sess-m", message="mijn mail is jan@x.be"),
        db=session,
    )

    # Eén profiel: enkel het web-form-contact over; het web_chat-gesprek hangt eraan.
    session.expire_all()
    contacts = (await session.execute(
        select(Contact).where(Contact.org_id == "org-c")
    )).scalars().all()
    assert [c.id for c in contacts] == ["ct-web"]
    conv = (await session.execute(
        select(Conversation).where(Conversation.org_id == "org-c")
        .execution_options(populate_existing=True)
    )).scalar_one()
    assert conv.channel == "web_chat"
    assert conv.contact_id == "ct-web"
    assert "web_chat" in json.loads(
        (await session.get(Contact, "ct-web")).channels_json
    )


@pytest.mark.asyncio
async def test_web_chat_synced_anonymous_then_email_no_orphan_record(session, monkeypatch):
    """
    DoD §3 — het gevaarlijke geval. Een anonieme web-chat synct al naar Airtable (≥3
    berichten, nog zonder e-mail) → record op de anonieme contact-key. Daarna onthult de
    bezoeker z'n e-mail en herkoppelt het gesprek naar een bestaand contact. Het oude
    (anonieme) record mag NIET als duplicaat blijven hangen: het wordt verwijderd en het
    gesprek hersynct onder de winnaar-key. Mist de fix het record (alleen het contact), dan
    vangt deze test het.
    """
    from app.services import crm_sync_service as crmmod
    monkeypatch.setattr(crmmod.httpx, "AsyncClient", _FakeAirtable)
    _FakeAirtable.patches, _FakeAirtable.deletes = [], []
    _stub_ai(monkeypatch, reply="Genoteerd!")
    # Eerste extractie (anoniem, nog geen e-mail); na de onthulling levert de stub de e-mail.
    _stub_extract(monkeypatch, {"intentie": "Offerte", "urgentie": "Hoog",
                                "gewenste_datum": None, "email": None})
    session.add(Organization(
        id="org-c", name="C", crm_type="airtable",
        crm_credentials_encrypted=json.dumps(
            {"api_key": "pat", "base_id": "app", "table_name": "Leads"}
        ),
    ))
    session.add(Contact(id="ct-web", org_id="org-c", email="jan@x.be",
                        channels_json='["web_form"]',
                        created_at=dt.datetime(2026, 1, 1, 10, 0, 0)))
    await session.commit()

    # Twee anonieme beurten → 4 berichten → sync naar Airtable onder de anonieme key.
    await web_chat_intake(WebChatIn(org_id="org-c", session_id="sess-s", message="Hoi"), db=session)
    await web_chat_intake(WebChatIn(org_id="org-c", session_id="sess-s", message="nog iets"), db=session)
    assert _FakeAirtable.patches, "anonieme chat had al moeten syncen (≥3 berichten)"
    # Het record-id van die anonieme sync zit in de CrmSyncLog van het chat-gesprek.
    anon_record = (await session.execute(
        select(CrmSyncLog.external_id).join(
            Conversation, Conversation.id == CrmSyncLog.conversation_id
        ).where(Conversation.channel == "web_chat")
    )).scalar_one()
    assert anon_record and anon_record.startswith("rec")

    # Derde beurt onthult de e-mail → merge in ct-web + opruiming van het anonieme record.
    _stub_extract(monkeypatch, {"intentie": "Offerte", "urgentie": "Hoog",
                                "gewenste_datum": None, "email": "jan@x.be"})
    await web_chat_intake(
        WebChatIn(org_id="org-c", session_id="sess-s", message="mijn mail is jan@x.be"),
        db=session,
    )

    # Eén profiel; geen verweesd anoniem contact.
    session.expire_all()
    contacts = (await session.execute(
        select(Contact).where(Contact.org_id == "org-c")
    )).scalars().all()
    assert [c.id for c in contacts] == ["ct-web"]
    # Het anonieme Airtable-record is verwijderd (cleanup), niet blijven hangen.
    assert any(anon_record in d for d in _FakeAirtable.deletes)


@pytest.mark.asyncio
async def test_web_chat_books_appointment_end_to_end(session, monkeypatch):
    """
    DoD-2c end-to-end: een web-chatbeurt waarin de AI de create_appointment-tool aanroept,
    maakt daadwerkelijk een Appointment aan, gekoppeld aan het web_chat-gesprek. De ÉCHTE
    AI-lus draait (tool_use → tool_result → bevestigingstekst); alleen de Anthropic-call
    zelf is gemockt, zodat de tool-use → afspraak-flow over het web-kanaal bewezen wordt.
    """
    monkeypatch.setattr("app.routers.intake.send_lead_notification", AsyncMock())
    session.add(Organization(id="org-c", name="Vastgoed C", sector="vastgoed",
                             ai_tone="vriendelijk", crm_type="none"))
    await session.commit()

    # 1e Anthropic-call → tool_use(create_appointment); 2e → bevestiging + afsluit-tag.
    tool_block = MagicMock(type="tool_use", id="toolu_1")
    tool_block.name = "create_appointment"  # MagicMock(name=...) is gereserveerd → apart zetten
    tool_block.input = {"title": "Bezichtiging", "start_at": "2026-06-10T14:00:00",
                        "end_at": "2026-06-10T15:00:00"}
    resp_tool = MagicMock(stop_reason="tool_use", content=[tool_block])
    text_block = MagicMock(type="text")
    text_block.text = "Je bezichtiging staat genoteerd! [GESPREK_AFGEROND]"
    resp_text = MagicMock(stop_reason="end_turn", content=[text_block])

    with patch("app.services.ai_service.anthropic.AsyncAnthropic") as cls:
        client = AsyncMock()
        cls.return_value = client
        client.messages.create = AsyncMock(side_effect=[resp_tool, resp_text])
        out = await web_chat_intake(
            WebChatIn(org_id="org-c", session_id="sess-appt",
                      message="Ik wil graag een bezichtiging op 10 juni om 14u"),
            db=session,
        )

    # De afspraak is echt aangemaakt en hangt aan het web_chat-gesprek.
    appts = (await session.execute(
        select(Appointment).where(Appointment.org_id == "org-c")
    )).scalars().all()
    assert len(appts) == 1
    assert appts[0].title == "Bezichtiging"
    conv = (await session.execute(
        select(Conversation).where(Conversation.org_id == "org-c")
    )).scalar_one()
    assert conv.channel == "web_chat"
    assert appts[0].conversation_id == conv.id
    # De tool-tag is uit de reply gestript en het gesprek is afgerond.
    assert "[GESPREK_AFGEROND]" not in out.reply
    assert out.closed is True


@pytest.mark.asyncio
async def test_web_chat_unknown_org_404(session):
    with pytest.raises(HTTPException) as ei:
        await web_chat_intake(
            WebChatIn(org_id="bestaat-niet", session_id="s", message="hoi"), db=session
        )
    assert ei.value.status_code == 404


@pytest.mark.asyncio
async def test_web_chat_invalid_email_422(session):
    session.add(Organization(id="org-c", name="C", crm_type="none"))
    await session.commit()
    with pytest.raises(HTTPException) as ei:
        await web_chat_intake(
            WebChatIn(org_id="org-c", session_id="s", message="hoi", email="geen-email"),
            db=session,
        )
    assert ei.value.status_code == 422
