"""
Test de Airtable sync rechtstreeks — zonder WhatsApp-verkeer.
Maakt een nep-gesprek aan in de Railway DB en synchroniseert het naar Airtable.

Gebruik:
    cd /Users/kaanaydin/Desktop/Antigravity/Repto/api
    source .venv/bin/activate
    DATABASE_URL="postgresql://..." \
    ANTHROPIC_API_KEY="sk-ant-..." \
    AIRTABLE_API_KEY="pat..." \
    AIRTABLE_BASE_ID="app..." \
    python test_airtable_sync.py
"""
import asyncio
import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(__file__))

# Zet env vars voordat settings worden geladen
os.environ.setdefault("WHATSAPP_ACCESS_TOKEN",   "test-token")
os.environ.setdefault("WHATSAPP_PHONE_NUMBER_ID", "123456789")
os.environ.setdefault("WHATSAPP_VERIFY_TOKEN",    "test")

DATABASE_URL = os.environ.get("DATABASE_URL", "")
if not DATABASE_URL:
    print("❌ DATABASE_URL niet ingesteld"); sys.exit(1)

if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
os.environ["DATABASE_URL"] = DATABASE_URL

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from app.models.conversation import Organization, Conversation, Message
from app.services.crm_sync_service import CrmSyncService

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def run():
    async with AsyncSessionLocal() as db:
        # Test-org ophalen
        result = await db.execute(
            select(Organization).where(
                Organization.whatsapp_phone_number_id
                == os.environ["WHATSAPP_PHONE_NUMBER_ID"]
            )
        )
        org = result.scalar_one_or_none()
        if not org:
            print("❌ Test-org niet gevonden"); return

        print(f"✅ Org: {org.name} | crm_type: {org.crm_type}")

        # Nep-gesprek aanmaken
        conv_id = str(uuid.uuid4())
        conv = Conversation(
            id=conv_id,
            org_id=org.id,
            wa_contact_phone="+31612345678",
            wa_contact_name="Jan de Vries",
            status="in_progress",
        )
        db.add(conv)
        await db.flush()

        # Nep-berichten toevoegen
        berichten = [
            ("inbound",  "Goedemiddag, ik heb een lekkende kraan in de keuken. Kunnen jullie volgende week langskomen? Ik zit in Amsterdam Noord."),
            ("outbound", "Goedemiddag Jan! Dat klinkt als een spoedklus. Wat is een handig tijdstip volgende week voor u?"),
            ("inbound",  "Dinsdag ochtend rond 9 uur zou ideaal zijn. Is het dringend want het lekt al 2 dagen."),
        ]
        for direction, content in berichten:
            db.add(Message(
                id=str(uuid.uuid4()),
                conversation_id=conv_id,
                direction=direction,
                content=content,
                ai_generated=(direction == "outbound"),
            ))
        await db.commit()
        await db.refresh(conv)
        print(f"✅ Testgesprek aangemaakt (id: {conv_id[:8]}...)")

        # CRM sync uitvoeren
        print("🔄 Airtable sync starten...")
        crm = CrmSyncService(db)
        await crm.sync(conversation=conv, org=org)

        print("✅ Sync klaar! Controleer je Airtable base:")
        print(f"   https://airtable.com/appOf8tCteylDQGac")


asyncio.run(run())
