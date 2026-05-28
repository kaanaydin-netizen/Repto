"""
Seed script voor lokale development.
Maakt een test-organisatie aan die gekoppeld is aan het Meta phone_number_id.

Gebruik:
    cd /Users/kaanaydin/Desktop/Antigravity/Repto/api
    source .venv/bin/activate
    python seed_dev.py
"""
import asyncio
import uuid
import sys
import os

# Zorg dat de app importeerbaar is
sys.path.insert(0, os.path.dirname(__file__))

from app.database import AsyncSessionLocal, engine, Base
from app.models.conversation import Organization
from app.config import get_settings

settings = get_settings()


async def seed():
    # Maak tabellen aan als ze nog niet bestaan (alternatief voor alembic bij quick test)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        # Controleer of er al een organisatie is voor dit nummer
        from sqlalchemy import select
        existing = await db.execute(
            select(Organization).where(
                Organization.whatsapp_phone_number_id == settings.whatsapp_phone_number_id
            )
        )
        org = existing.scalar_one_or_none()

        if org:
            print(f"ℹ️  Organisatie bestaat al: {org.name} (id: {org.id})")
            return

        # Nieuwe test-organisatie aanmaken
        org = Organization(
            id=str(uuid.uuid4()),
            name="Test Installateur BV",
            sector="installateur",
            whatsapp_phone_number_id=settings.whatsapp_phone_number_id,
            ai_tone="vriendelijk",
            crm_type="none",
        )
        db.add(org)
        await db.commit()
        print(f"✅ Organisatie aangemaakt!")
        print(f"   Naam: {org.name}")
        print(f"   ID:   {org.id}")
        print(f"   WhatsApp nummer: {org.whatsapp_phone_number_id}")


if __name__ == "__main__":
    asyncio.run(seed())
