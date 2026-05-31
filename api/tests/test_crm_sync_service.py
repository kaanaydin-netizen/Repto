"""
Unit tests voor crm_sync_service.py
Tests: pijplijn-status mapping, intentie/urgentie/afspraak-status normalisatie,
en de Airtable native-upsert payload (gemockte httpx-client).
"""
import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock


# ─── _pipeline_status ──────────────────────────────────────────────────────────

def test_pipeline_status_afspraak_wint_altijd():
    from app.services.crm_sync_service import _pipeline_status

    conv = SimpleNamespace(status="closed")
    # Een afspraak weegt zwaarder dan een gesloten gesprek.
    assert _pipeline_status(conv, has_appointment=True, lead={}) == "Afspraak gepland"

    conv2 = SimpleNamespace(status="appointment_set")
    assert _pipeline_status(conv2, has_appointment=False, lead={}) == "Afspraak gepland"


def test_pipeline_status_closed_varianten():
    from app.services.crm_sync_service import _pipeline_status

    conv = SimpleNamespace(status="closed")
    assert _pipeline_status(conv, False, {"opvolging_nodig": True}) == "Op te volgen"
    assert _pipeline_status(conv, False, {"intentie": "Offerte"}) == "Offerte verstuurd"
    assert _pipeline_status(conv, False, {}) == "Gewonnen"


def test_pipeline_status_open_gesprek():
    from app.services.crm_sync_service import _pipeline_status

    assert _pipeline_status(SimpleNamespace(status="in_progress"), False, {}) == "In gesprek"
    assert _pipeline_status(SimpleNamespace(status="new"), False, {}) == "Nieuw"


# ─── _appointment_status ────────────────────────────────────────────────────────

def test_appointment_status_mapping():
    from app.services.crm_sync_service import _appointment_status

    assert _appointment_status("confirmed") == "Bevestigd"
    assert _appointment_status("CANCELLED") == "Geannuleerd"
    assert _appointment_status("completed") == "Afgerond"
    assert _appointment_status("pending") == "Voorlopig"
    assert _appointment_status(None) == "Bevestigd"
    assert _appointment_status("onbekend") == "Bevestigd"


# ─── _normalize_intentie / _normalize_urgentie ──────────────────────────────────

def test_normalize_intentie():
    from app.services.crm_sync_service import _normalize_intentie

    assert _normalize_intentie("Offerte") == "Offerte"
    assert _normalize_intentie("afspraak") == "Afspraak"
    assert _normalize_intentie(None) == "Anders"
    assert _normalize_intentie("iets raars") == "Anders"


def test_normalize_urgentie():
    from app.services.crm_sync_service import _normalize_urgentie

    assert _normalize_urgentie("ja") == "ja"
    assert _normalize_urgentie("dringend") == "ja"
    assert _normalize_urgentie("nee") == "nee"
    assert _normalize_urgentie("normaal") == "nee"
    assert _normalize_urgentie("misschien") is None
    assert _normalize_urgentie(None) is None


# ─── _airtable_upsert payload ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_airtable_upsert_builds_native_upsert_payload():
    from app.services.crm_sync_service import CrmSyncService, AIRTABLE_API_URL

    svc = CrmSyncService.__new__(CrmSyncService)  # geen DB/anthropic nodig

    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {"records": [{"id": "rec123ABC456DEF78"}]}
    client = MagicMock()
    client.patch = AsyncMock(return_value=resp)

    record_id = await svc._airtable_upsert(
        client, "appXXXXXXXXXXXXXX", "patKEY", "Afspraken",
        merge_on=["Bron ID"], fields={"Titel": "Werfbezoek", "Bron ID": "appt-1"},
    )

    assert record_id == "rec123ABC456DEF78"
    args, kwargs = client.patch.call_args
    # URL = base + table
    assert args[0] == f"{AIRTABLE_API_URL}/appXXXXXXXXXXXXXX/Afspraken"
    body = kwargs["json"]
    assert body["performUpsert"]["fieldsToMergeOn"] == ["Bron ID"]
    assert body["typecast"] is True
    assert body["records"][0]["fields"]["Titel"] == "Werfbezoek"


@pytest.mark.asyncio
async def test_airtable_upsert_raises_on_error_status():
    from app.services.crm_sync_service import CrmSyncService

    svc = CrmSyncService.__new__(CrmSyncService)
    resp = MagicMock()
    resp.status_code = 422
    resp.text = "Invalid field"
    client = MagicMock()
    client.patch = AsyncMock(return_value=resp)

    with pytest.raises(ValueError, match="Airtable upsert"):
        await svc._airtable_upsert(
            client, "appXXXXXXXXXXXXXX", "patKEY", "Leads",
            merge_on=["Bron ID"], fields={"Naam": "X"},
        )
