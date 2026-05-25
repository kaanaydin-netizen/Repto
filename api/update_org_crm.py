"""
Update de test-organisatie in Railway Postgres:
  - crm_type: → "airtable"
  - crm_credentials_encrypted: Airtable api_key + base_id + table_name

Gebruik:
    cd /Users/kaanaydin/Desktop/Antigravity/Repto/api
    DATABASE_URL="postgresql://..." \
    AIRTABLE_API_KEY="pat..." \
    AIRTABLE_BASE_ID="app..." \
    python update_org_crm.py

Optioneel: AIRTABLE_TABLE_NAME (standaard: "Leads")
"""
import asyncio
import json
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.models.conversation import Organization

TWILIO_FROM = "whatsapp:+14155238886"

DATABASE_URL = os.environ.get("DATABASE_URL", "")
if not DATABASE_URL:
    print("❌ Stel DATABASE_URL in als omgevingsvariabele")
    sys.exit(1)

AIRTABLE_API_KEY = os.environ.get("AIRTABLE_API_KEY", "")
AIRTABLE_BASE_ID = os.environ.get("AIRTABLE_BASE_ID", "")
AIRTABLE_TABLE_NAME = os.environ.get("AIRTABLE_TABLE_NAME", "Leads")

if not AIRTABLE_API_KEY or not AIRTABLE_BASE_ID:
    print("❌ Stel AIRTABLE_API_KEY en AIRTABLE_BASE_ID in als omgevingsvariabelen")
    sys.exit(1)

# asyncpg verwacht postgresql+asyncpg://
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def update_org():
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Organization).where(
                Organization.whatsapp_phone_number_id == TWILIO_FROM
            )
        )
        org = result.scalar_one_or_none()

        if not org:
            print(f"❌ Geen organisatie gevonden voor {TWILIO_FROM}")
            return

        print(f"✅ Organisatie gevonden: {org.name} (id: {org.id})")
        print(f"   Huidige crm_type: {org.crm_type}")

        credentials = {
            "api_key": AIRTABLE_API_KEY,
            "base_id": AIRTABLE_BASE_ID,
            "table_name": AIRTABLE_TABLE_NAME,
        }

        org.crm_type = "airtable"
        org.crm_credentials_encrypted = json.dumps(credentials)
        await db.commit()

        print(f"✅ Bijgewerkt!")
        print(f"   crm_type: {org.crm_type}")
        print(f"   base_id: {AIRTABLE_BASE_ID}")
        print(f"   table_name: {AIRTABLE_TABLE_NAME}")
        print(f"   api_key: {AIRTABLE_API_KEY[:10]}...")


asyncio.run(update_org())
