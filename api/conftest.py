"""
Pytest-configuratie.

Zet hermetische test-env vóór de app-modules worden geïmporteerd, zodat de
Settings (pydantic) altijd laden — onafhankelijk van een lokale .env. Env vars
hebben in pydantic-settings voorrang op het .env-bestand, dus deze waarden winnen.
"""
import os

# Verplichte settings-velden van een veilige testwaarde voorzien
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost/test")
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-ant-test")
os.environ.setdefault("WHATSAPP_ACCESS_TOKEN", "test-access-token")
os.environ.setdefault("WHATSAPP_PHONE_NUMBER_ID", "123456789")
os.environ.setdefault("WHATSAPP_VERIFY_TOKEN", "test-verify-token")
os.environ.setdefault("WHATSAPP_API_VERSION", "v22.0")

import pytest  # noqa: E402


@pytest.fixture
def anyio_backend():
    return "asyncio"
