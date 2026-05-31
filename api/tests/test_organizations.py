"""
Unit tests voor organizations.py
Focus: _resolve_crm_credentials — voorkomt dat bestaande Airtable-credentials
gewist worden bij een instellingen-update zonder nieuwe credentials.
"""
import json


def _creds():
    from app.routers.organizations import AirtableCredentials
    return AirtableCredentials(api_key="patABC", base_id="appXYZ", table_name="Leads")


# ─── _resolve_crm_credentials ───────────────────────────────────────────────────

def test_resolve_keeps_existing_when_airtable_without_new_creds():
    """De kernbug: crm_type=airtable + geen nieuwe creds → behoud bestaande."""
    from app.routers.organizations import _resolve_crm_credentials

    existing = json.dumps({"api_key": "patOLD", "base_id": "appOLD", "table_name": "Leads"})
    result = _resolve_crm_credentials(existing, "airtable", None)
    assert result == existing  # NIET gewist


def test_resolve_overwrites_with_new_creds():
    from app.routers.organizations import _resolve_crm_credentials

    existing = json.dumps({"api_key": "patOLD", "base_id": "appOLD", "table_name": "Leads"})
    result = _resolve_crm_credentials(existing, "airtable", _creds())
    assert json.loads(result) == {"api_key": "patABC", "base_id": "appXYZ", "table_name": "Leads"}


def test_resolve_clears_when_type_not_airtable():
    from app.routers.organizations import _resolve_crm_credentials

    existing = json.dumps({"api_key": "patOLD", "base_id": "appOLD", "table_name": "Leads"})
    assert _resolve_crm_credentials(existing, "none", None) is None
    assert _resolve_crm_credentials(existing, "hubspot", None) is None


def test_resolve_no_existing_no_new():
    from app.routers.organizations import _resolve_crm_credentials

    assert _resolve_crm_credentials(None, "airtable", None) is None


# ─── _serialize_crm ─────────────────────────────────────────────────────────────

def test_serialize_crm_airtable_and_none():
    from app.routers.organizations import _serialize_crm

    assert _serialize_crm("airtable", None) is None
    assert _serialize_crm("none", _creds()) is None
    parsed = json.loads(_serialize_crm("airtable", _creds()))
    assert parsed["api_key"] == "patABC"
    assert parsed["base_id"] == "appXYZ"
