"""
Unit tests voor webhooks.py
Tests: lege body, leeg telefoonnummer, CLOSING_TAG detectie
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ─── CLOSING_TAG constante ────────────────────────────────────────────────────

def test_closing_tag_detected():
    """CLOSING_TAG = '[GESPREK_AFGEROND]' moet correct worden herkend."""
    from app.routers.webhooks import CLOSING_TAG

    assert CLOSING_TAG == "[GESPREK_AFGEROND]"

    # Simuleer de detectielogica uit process_incoming_message
    reply_with_tag = "Bedankt voor uw bericht! [GESPREK_AFGEROND]"
    reply_without_tag = "Bedankt voor uw bericht!"

    assert CLOSING_TAG in reply_with_tag
    assert CLOSING_TAG not in reply_without_tag

    # strip-logica zoals in de code
    clean = reply_with_tag.replace(CLOSING_TAG, "").strip()
    assert clean == "Bedankt voor uw bericht!"


# ─── receive_message via ASGI TestClient ─────────────────────────────────────

def _build_test_app():
    """
    Bouw een minimale FastAPI-app met enkel de webhook router,
    zonder echte DB of settings te laden.
    """
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    # Mock de settings VOOR de import van modules die settings gebruiken
    mock_settings = MagicMock()
    mock_settings.anthropic_api_key = "test-key"
    mock_settings.twilio_account_sid = "ACtest"
    mock_settings.twilio_auth_token = "token"
    mock_settings.twilio_whatsapp_from = "whatsapp:+14155238886"
    mock_settings.database_url = "postgresql://user:pass@localhost/test"
    mock_settings.debug = False

    return mock_settings


@pytest.fixture
def webhook_client():
    """
    Fixture die een TestClient aanmaakt voor de webhook endpoint,
    met alle externe afhankelijkheden gemockt.
    """
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    mock_settings = _build_test_app()

    with patch("app.config.get_settings", return_value=mock_settings), \
         patch("app.database.get_settings", return_value=mock_settings), \
         patch("app.services.ai_service.get_settings", return_value=mock_settings), \
         patch("app.services.reminder_service.get_settings", return_value=mock_settings):

        # Laad de router pas ná het patchen van settings
        from fastapi.testclient import TestClient

        app = FastAPI()

        # Mock get_db dependency
        async def override_get_db():
            yield AsyncMock()

        from app.database import get_db
        from app.routers import webhooks as wh_module
        app.include_router(wh_module.router)
        app.dependency_overrides[get_db] = override_get_db

        client = TestClient(app, raise_server_exceptions=False)
        yield client


def test_empty_body_returns_ok(webhook_client):
    """Lege body → webhook retourneert {'status': 'ok'}."""
    with patch("app.routers.webhooks.process_incoming_message", new_callable=AsyncMock):
        response = webhook_client.post(
            "/webhooks/whatsapp",
            data={"From": "whatsapp:+32499123456", "To": "whatsapp:+14155238886", "Body": ""},
        )
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_empty_from_phone_returns_ok(webhook_client):
    """Leeg telefoonnummer → webhook retourneert {'status': 'ok'}."""
    with patch("app.routers.webhooks.process_incoming_message", new_callable=AsyncMock):
        response = webhook_client.post(
            "/webhooks/whatsapp",
            data={"From": "", "To": "whatsapp:+14155238886", "Body": "Hallo"},
        )
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
