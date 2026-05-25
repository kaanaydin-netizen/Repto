"""
Airtable Setup Script — configureert de Repto Leads tabel in een bestaande base.

Stap 1: Maak een lege base aan op airtable.com (klik "+ Create a base")
Stap 2: Kopieer de base ID uit de URL (bijv. airtable.com/appXXXXXXXX/...)
Stap 3: Voer dit script uit:

    cd /Users/kaanaydin/Desktop/Antigravity/Repto/api
    source .venv/bin/activate
    AIRTABLE_API_KEY="pat..." AIRTABLE_BASE_ID="appXXXXX" python setup_airtable.py

Het script:
  - Hernoemt de eerste tabel naar "Leads"
  - Voegt alle benodigde kolommen toe
  - Print de env vars voor Railway
"""
import os
import sys
import httpx

API_KEY  = os.environ.get("AIRTABLE_API_KEY", "")
BASE_ID  = os.environ.get("AIRTABLE_BASE_ID", "")

if not API_KEY or not BASE_ID:
    print("❌ Stel AIRTABLE_API_KEY én AIRTABLE_BASE_ID in als omgevingsvariabelen")
    print("   Voorbeeld: AIRTABLE_API_KEY='pat...' AIRTABLE_BASE_ID='appXXX' python setup_airtable.py")
    sys.exit(1)

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}
TABLE_NAME = "Leads"
META_URL   = f"https://api.airtable.com/v0/meta/bases/{BASE_ID}"


def get_tables() -> list:
    r = httpx.get(f"{META_URL}/tables", headers=HEADERS)
    if r.status_code != 200:
        print(f"❌ Kon tabellen niet ophalen: {r.status_code} {r.text[:300]}")
        sys.exit(1)
    return r.json().get("tables", [])


def rename_table(table_id: str, new_name: str):
    r = httpx.patch(f"{META_URL}/tables/{table_id}", headers=HEADERS, json={"name": new_name})
    if r.status_code not in (200, 201):
        print(f"⚠️  Kon tabel niet hernoemen: {r.status_code} {r.text[:200]}")


def add_field(table_id: str, field: dict):
    r = httpx.post(f"{META_URL}/tables/{table_id}/fields", headers=HEADERS, json=field)
    if r.status_code not in (200, 201):
        print(f"⚠️  Veld '{field['name']}' niet toegevoegd: {r.status_code} {r.text[:200]}")
    else:
        print(f"   ✅ {field['name']}")


def main():
    print(f"🚀 Airtable setup voor Repto (base: {BASE_ID})...\n")

    tables = get_tables()
    if not tables:
        print("❌ Geen tabellen gevonden in deze base")
        sys.exit(1)

    first_table = tables[0]
    table_id    = first_table["id"]
    existing_fields = {f["name"] for f in first_table.get("fields", [])}

    # Hernoem de tabel naar "Leads" als hij nog anders heet
    if first_table["name"] != TABLE_NAME:
        rename_table(table_id, TABLE_NAME)
        print(f"✅ Tabel hernoemd naar '{TABLE_NAME}'")
    else:
        print(f"✅ Tabel '{TABLE_NAME}' bestaat al")

    # Velden die we nodig hebben (Naam bestaat al als primary field)
    new_fields = [
        {"name": "Telefoon",       "type": "phoneNumber"},
        {"name": "Adres",          "type": "singleLineText"},
        {"name": "Type Werk",      "type": "singleLineText"},
        {"name": "Gewenste Datum", "type": "singleLineText"},
        {"name": "Urgentie",       "type": "singleSelect",
         "options": {"choices": [{"name": "ja",  "color": "redBright"},
                                  {"name": "nee", "color": "greenBright"}]}},
        {"name": "Status",         "type": "singleSelect",
         "options": {"choices": [{"name": "new"},
                                  {"name": "in_progress"},
                                  {"name": "appointment_set"},
                                  {"name": "closed"}]}},
        {"name": "Datum",          "type": "singleLineText"},
        {"name": "Eerste Bericht", "type": "multilineText"},
    ]

    print("\n📋 Velden toevoegen:")
    for field in new_fields:
        if field["name"] not in existing_fields:
            add_field(table_id, field)
        else:
            print(f"   ⏭️  {field['name']} (bestaat al)")

    print(f"\n{'=' * 55}")
    print("✅ Airtable base klaar! Kopieer deze Railway env vars:")
    print(f"{'=' * 55}")
    print(f"  AIRTABLE_API_KEY    = {API_KEY}")
    print(f"  AIRTABLE_BASE_ID    = {BASE_ID}")
    print(f"  AIRTABLE_TABLE_NAME = {TABLE_NAME}")
    print(f"{'=' * 55}")
    print("\nRailway instellen:")
    print(f"  railway variables set AIRTABLE_API_KEY=\"{API_KEY}\"")
    print(f"  railway variables set AIRTABLE_BASE_ID=\"{BASE_ID}\"")
    print(f"  railway variables set AIRTABLE_TABLE_NAME=\"{TABLE_NAME}\"")


if __name__ == "__main__":
    main()
