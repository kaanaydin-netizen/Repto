"""
Airtable Setup Script — maakt automatisch een Repto base + Leads tabel aan.

Gebruik:
    cd /Users/kaanaydin/Desktop/Antigravity/Repto/api
    AIRTABLE_API_KEY="pat..." python setup_airtable.py

Na afloop worden BASE_ID en TABLE_NAME geprint — kopieer ze naar Railway env vars
of gebruik ze in update_org_crm.py.

Vereiste token scopes: data.records:write, schema.bases:write
"""
import os
import sys
import json
import httpx

API_KEY = os.environ.get("AIRTABLE_API_KEY", "")
if not API_KEY:
    print("❌ Stel AIRTABLE_API_KEY in als omgevingsvariabele")
    sys.exit(1)

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}

BASE_NAME = "Repto Leads"
TABLE_NAME = "Leads"

# Kolommen voor de Leads tabel
FIELDS = [
    {"name": "Datum",          "type": "singleLineText"},
    {"name": "Naam",           "type": "singleLineText"},
    {"name": "Telefoon",       "type": "phoneNumber"},
    {"name": "Adres",          "type": "singleLineText"},
    {"name": "Type Werk",      "type": "singleLineText"},
    {"name": "Gewenste Datum", "type": "singleLineText"},
    {"name": "Urgentie",       "type": "singleSelect",
     "options": {"choices": [{"name": "ja", "color": "redBright"},
                              {"name": "nee", "color": "greenBright"}]}},
    {"name": "Status",         "type": "singleSelect",
     "options": {"choices": [{"name": "new"},
                              {"name": "in_progress"},
                              {"name": "appointment_set"},
                              {"name": "closed"}]}},
    {"name": "Eerste Bericht", "type": "multilineText"},
]


def get_workspace_id() -> str:
    """Haal het eerste workspace ID op van de gebruiker."""
    resp = httpx.get("https://api.airtable.com/v0/meta/workspaces", headers=HEADERS)
    if resp.status_code != 200:
        print(f"❌ Kon workspaces niet ophalen: {resp.status_code} {resp.text[:200]}")
        sys.exit(1)
    workspaces = resp.json().get("workspaces", [])
    if not workspaces:
        print("❌ Geen workspaces gevonden")
        sys.exit(1)
    ws = workspaces[0]
    print(f"✅ Workspace gevonden: {ws['name']} (id: {ws['id']})")
    return ws["id"]


def create_base(workspace_id: str) -> str:
    """Maak een nieuwe Airtable base aan met de Leads tabel."""
    payload = {
        "name": BASE_NAME,
        "workspaceId": workspace_id,
        "tables": [
            {
                "name": TABLE_NAME,
                "fields": FIELDS,
            }
        ],
    }
    resp = httpx.post(
        "https://api.airtable.com/v0/meta/bases",
        headers=HEADERS,
        json=payload,
    )
    if resp.status_code not in (200, 201):
        print(f"❌ Base aanmaken mislukt: {resp.status_code} {resp.text[:300]}")
        sys.exit(1)

    data = resp.json()
    base_id = data["id"]
    print(f"✅ Base aangemaakt: {BASE_NAME} (id: {base_id})")
    return base_id


def main():
    print("🚀 Airtable setup voor Repto...\n")

    workspace_id = get_workspace_id()
    base_id = create_base(workspace_id)

    print("\n" + "=" * 50)
    print("✅ Klaar! Kopieer deze waarden:")
    print(f"   AIRTABLE_API_KEY  = {API_KEY[:15]}...")
    print(f"   AIRTABLE_BASE_ID  = {base_id}")
    print(f"   AIRTABLE_TABLE_NAME = {TABLE_NAME}")
    print("=" * 50)
    print("\nRailway env vars instellen:")
    print(f"  railway variables set AIRTABLE_API_KEY={API_KEY}")
    print(f"  railway variables set AIRTABLE_BASE_ID={base_id}")
    print(f"  railway variables set AIRTABLE_TABLE_NAME={TABLE_NAME}")
    print("\nOf voer update_org_crm.py uit om de test-org bij te werken:")
    print(f"  DATABASE_URL=\"...\" AIRTABLE_API_KEY=\"{API_KEY[:10]}...\" AIRTABLE_BASE_ID=\"{base_id}\" python update_org_crm.py")


if __name__ == "__main__":
    main()
