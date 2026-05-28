"""
Unit tests voor webhooks.py (Meta WhatsApp Cloud API).
Tests: GET-verificatie, CLOSING_TAG, POST-parsing van Meta JSON
(tekst → queued, statusupdate → genegeerd, niet-tekst → genegeerd).
"""
import pytest
from unittest.mock import AsyncMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient


# ─── CLOSING_TAG constante ────────────────────────────────────────────────────

def test_closing_tag_detected():
    from app.routers.webhooks import CLOSING_TAG

    assert CLOSING_TAG == "[GESPREK_AFGEROND]"
    reply_with_tag = "Bedankt voor uw bericht! [GESPREK_AFGEROND]"
    assert CLOSING_TAG in reply_with_tag
    clean = reply_with_tag.replace(CLOSING_TAG, "").strip()
    assert clean == "Bedankt voor uw bericht!"


# ─── Test-app ─────────────────────────────────────────────────────────────────

@pytest.fixture
def client():
    from app.routers import webhooks as wh_module

    app = FastAPI()
    app.include_router(wh_module.router)
    return TestClient(app, raise_server_exceptions=False)


# ─── GET: verificatie-handshake ────────────────────────────────────────────────

def test_verify_success_returns_challenge(client):
    """Correcte verify_token → hub.challenge wordt als platte tekst teruggegeven."""
    resp = client.get(
        "/webhooks/whatsapp",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "test-verify-token",  # uit conftest
            "hub.challenge": "1234567890",
        },
    )
    assert resp.status_code == 200
    assert resp.text == "1234567890"


def test_verify_wrong_token_returns_403(client):
    resp = client.get(
        "/webhooks/whatsapp",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "fout-token",
            "hub.challenge": "1234567890",
        },
    )
    assert resp.status_code == 403


# ─── POST: Meta JSON-payloads ──────────────────────────────────────────────────

def _text_payload(body="Hallo", from_phone="32499123456", phone_number_id="123456789"):
    return {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "WABA_ID",
            "changes": [{
                "field": "messages",
                "value": {
                    "messaging_product": "whatsapp",
                    "metadata": {"display_phone_number": "32...", "phone_number_id": phone_number_id},
                    "contacts": [{"profile": {"name": "Jan"}, "wa_id": from_phone}],
                    "messages": [{
                        "from": from_phone,
                        "id": "wamid.TEST",
                        "timestamp": "1700000000",
                        "type": "text",
                        "text": {"body": body},
                    }],
                },
            }],
        }],
    }


def test_text_message_queues_processing(client):
    """Een tekstbericht → process_incoming_message wordt precies één keer ingepland."""
    with patch("app.routers.webhooks.process_incoming_message", new_callable=AsyncMock) as mock_proc:
        resp = client.post("/webhooks/whatsapp", json=_text_payload(body="Lekkende kraan"))
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "queued": 1}
    mock_proc.assert_called_once()
    kwargs = mock_proc.call_args.kwargs
    assert kwargs["phone_number_id"] == "123456789"
    assert kwargs["from_phone"] == "32499123456"
    assert kwargs["body"] == "Lekkende kraan"
    assert kwargs["contact_name"] == "Jan"


def test_empty_body_not_queued(client):
    """Leeg tekstbericht → niets ingepland."""
    with patch("app.routers.webhooks.process_incoming_message", new_callable=AsyncMock) as mock_proc:
        resp = client.post("/webhooks/whatsapp", json=_text_payload(body="   "))
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "queued": 0}
    mock_proc.assert_not_called()


def test_status_update_ignored(client):
    """Statusupdate (delivered/read) bevat geen 'messages' → genegeerd."""
    payload = {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "WABA_ID",
            "changes": [{
                "field": "messages",
                "value": {
                    "messaging_product": "whatsapp",
                    "metadata": {"phone_number_id": "123456789"},
                    "statuses": [{"id": "wamid.X", "status": "delivered"}],
                },
            }],
        }],
    }
    with patch("app.routers.webhooks.process_incoming_message", new_callable=AsyncMock) as mock_proc:
        resp = client.post("/webhooks/whatsapp", json=payload)
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "queued": 0}
    mock_proc.assert_not_called()


def test_non_text_message_ignored(client):
    """Niet-tekst bericht (image) → genegeerd, niets ingepland."""
    payload = _text_payload()
    msg = payload["entry"][0]["changes"][0]["value"]["messages"][0]
    msg.pop("text")
    msg["type"] = "image"
    msg["image"] = {"id": "MEDIA_ID", "mime_type": "image/jpeg"}
    with patch("app.routers.webhooks.process_incoming_message", new_callable=AsyncMock) as mock_proc:
        resp = client.post("/webhooks/whatsapp", json=payload)
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "queued": 0}
    mock_proc.assert_not_called()


def test_non_waba_object_ignored(client):
    with patch("app.routers.webhooks.process_incoming_message", new_callable=AsyncMock) as mock_proc:
        resp = client.post("/webhooks/whatsapp", json={"object": "page", "entry": []})
    assert resp.status_code == 200
    assert resp.json() == {"status": "ignored"}
    mock_proc.assert_not_called()
