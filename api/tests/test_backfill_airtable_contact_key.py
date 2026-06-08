"""
Tests voor backfill_airtable_contact_key.backfill_org — de productie-aanrakende migratie
die Airtable-records herkeyt van conversation.id naar contact.id (increment 2, stap C).

In-memory SQLite + een gemockte Airtable-client (geen extern verkeer). Bewijst de
grouping/collapse-logica, de dry-run (raakt niets aan), idempotentie en de post-deploy-
veiligheid (een al-correct record blijft de survivor — geen duplicaat).
"""
import json

import pytest
import pytest_asyncio

import backfill_airtable_contact_key as bf
from app.models.conversation import Organization, Conversation


# ─── Fixtures + fake Airtable ──────────────────────────────────────────────────

@pytest_asyncio.fixture
async def session():
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


class _Resp:
    def __init__(self, status_code=200, payload=None, text=""):
        self.status_code = status_code
        self._payload = payload or {}
        self.text = text

    def json(self):
        return self._payload


class _FakeAirtable:
    """Eén pagina records; vangt patches (id→nieuwe Bron ID) en deletes (record-id)."""
    def __init__(self, records):
        self._records = records
        self.patches: dict = {}
        self.deletes: list = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    async def get(self, url, headers=None, params=None):
        return _Resp(payload={"records": self._records})  # geen offset → één pagina

    async def patch(self, url, headers=None, json=None):
        rec_id = url.rsplit("/", 1)[-1]
        self.patches[rec_id] = json["fields"]["Bron ID"]
        return _Resp(payload={"id": rec_id})

    async def delete(self, url, headers=None):
        self.deletes.append(url.rsplit("/", 1)[-1])
        return _Resp()


def _install(monkeypatch, records):
    """Maak de fake en zet 'm als httpx.AsyncClient in de backfill-module; throttle uit."""
    fake = _FakeAirtable(records)
    monkeypatch.setattr(bf, "_THROTTLE_SECONDS", 0)
    monkeypatch.setattr(bf.httpx, "AsyncClient", lambda *a, **k: fake)
    return fake


def _rec(rec_id, bron):
    return {"id": rec_id, "fields": {"Bron ID": bron}}


async def _org_with_convs(session, conv_to_contact: dict) -> Organization:
    org = Organization(
        id="org-y", name="Y", crm_type="airtable",
        crm_credentials_encrypted=json.dumps(
            {"api_key": "pat", "base_id": "appX", "table_name": "Leads"}
        ),
    )
    session.add(org)
    for conv_id, contact_id in conv_to_contact.items():
        session.add(Conversation(id=conv_id, org_id="org-y", contact_id=contact_id,
                                 channel="whatsapp"))
    await session.commit()
    return org


# ─── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_dry_run_touches_nothing(session, monkeypatch):
    """Dry-run mag nooit een PATCH of DELETE doen, ook niet als er werk klaarligt."""
    org = await _org_with_convs(session, {"cv1": "ct-1"})
    fake = _install(monkeypatch, [_rec("rec1", "cv1")])
    await bf.backfill_org(session, org, apply=False)
    assert fake.patches == {} and fake.deletes == []


@pytest.mark.asyncio
async def test_apply_rewrites_and_collapses(session, monkeypatch):
    """
    Realistische prod-run (alles nog op conversation.id):
    - ct-1 heeft twee gesprekken → twee records → collaberen tot één (survivor herschreven
      naar ct-1, de andere verwijderd);
    - ct-2 heeft één gesprek → herschrijven, niets verwijderen;
    - een record met onbekende Bron ID → met rust gelaten.
    """
    org = await _org_with_convs(session, {"cv1": "ct-1", "cv2": "ct-1", "cv3": "ct-2"})
    fake = _install(monkeypatch, [
        _rec("recA", "cv1"), _rec("recB", "cv2"),   # beide → ct-1
        _rec("recC", "cv3"),                          # → ct-2
        _rec("recZ", "cv-onbekend"),                  # onresolvebaar
    ])
    await bf.backfill_org(session, org, apply=True)

    # ct-1: één survivor herschreven, de andere verwijderd. ct-2: herschreven, geen delete.
    assert fake.patches.get("recC") == "ct-2"
    ct1_patched = {r: v for r, v in fake.patches.items() if v == "ct-1"}
    assert len(ct1_patched) == 1                       # precies één survivor voor ct-1
    survivor_id = next(iter(ct1_patched))
    other = "recB" if survivor_id == "recA" else "recA"
    assert fake.deletes == [other]                     # enkel de niet-survivor van ct-1
    assert "recZ" not in fake.patches and "recZ" not in fake.deletes  # onaangeroerd


@pytest.mark.asyncio
async def test_idempotent_when_already_on_contact_id(session, monkeypatch):
    """Tweede run (alles al op contact.id, één per persoon) → geen enkele wijziging."""
    org = await _org_with_convs(session, {"cv1": "ct-1", "cv2": "ct-2"})
    fake = _install(monkeypatch, [_rec("recA", "ct-1"), _rec("recB", "ct-2")])
    await bf.backfill_org(session, org, apply=True)
    assert fake.patches == {} and fake.deletes == []


@pytest.mark.asyncio
async def test_post_deploy_safety_keeps_correct_record(session, monkeypatch):
    """
    Veiligheid als het script ooit ná de code-deploy draait: voor ct-1 bestaat al een
    correct record (Bron ID=ct-1) NAAST een oud, op conversation.id gekeyd record. Het
    correcte record blijft de survivor (geen PATCH), het oude wordt verwijderd — zo
    ontstaat géén tweede record op ct-1.
    """
    org = await _org_with_convs(session, {"cv1": "ct-1"})
    fake = _install(monkeypatch, [_rec("recOK", "ct-1"), _rec("recOld", "cv1")])
    await bf.backfill_org(session, org, apply=True)
    assert fake.patches == {}                           # correcte survivor → geen herschrijving
    assert fake.deletes == ["recOld"]                   # enkel het oude record weg


@pytest.mark.asyncio
async def test_failed_patch_preserves_duplicates(session, monkeypatch):
    """Mislukt de survivor-PATCH, dan worden de duplicaten van die groep NIET verwijderd
    (anders verlies je data zonder bevestigde survivor)."""
    org = await _org_with_convs(session, {"cv1": "ct-1", "cv2": "ct-1"})
    fake = _install(monkeypatch, [_rec("recA", "cv1"), _rec("recB", "cv2")])

    async def failing_patch(url, headers=None, json=None):
        return _Resp(status_code=422, text="boom")
    fake.patch = failing_patch

    await bf.backfill_org(session, org, apply=True)
    assert fake.deletes == []                           # survivor niet bevestigd → niets verwijderd
