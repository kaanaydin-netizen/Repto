"""
Unit tests voor whatsapp_service.py — verifieert de Meta Cloud API request-vorm
(URL, Bearer-header en JSON-payload) voor zowel vrije tekst als templates.
httpx wordt volledig gemockt; er gaat geen echt verkeer naar Meta.
"""
import pytest
from unittest.mock import AsyncMock


class _FakeResp:
    status_code = 200
    text = "{}"

    def json(self):
        return {"messages": [{"id": "wamid.OUT"}]}

    def raise_for_status(self):
        return None


class _FakeClient:
    """Vangt de laatste post-aanroep op in de class-attribuut `captured`."""
    captured: dict = {}

    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def post(self, url, headers=None, json=None):
        _FakeClient.captured = {"url": url, "headers": headers, "json": json}
        return _FakeResp()


@pytest.fixture
def wa_service(monkeypatch):
    from app.services import whatsapp_service as mod
    monkeypatch.setattr(mod.httpx, "AsyncClient", _FakeClient)
    _FakeClient.captured = {}
    return mod.WhatsAppService(db=AsyncMock())


@pytest.mark.asyncio
async def test_send_message_builds_meta_text_request(wa_service):
    await wa_service.send_message(
        to_phone="+32499123456",
        message="Goedendag!",
        phone_number_id="PNID_42",
    )
    cap = _FakeClient.captured
    # URL bevat versie + phone_number_id
    assert cap["url"].endswith("/v22.0/PNID_42/messages")
    assert cap["url"].startswith("https://graph.facebook.com/")
    # Bearer-token header
    assert cap["headers"]["Authorization"] == "Bearer test-access-token"
    # Payload-vorm: '+' gestript, type text
    body = cap["json"]
    assert body["messaging_product"] == "whatsapp"
    assert body["to"] == "32499123456"
    assert body["type"] == "text"
    assert body["text"]["body"] == "Goedendag!"


@pytest.mark.asyncio
async def test_send_message_falls_back_to_default_sender(wa_service):
    await wa_service.send_message(to_phone="32499123456", message="hoi")
    # Geen phone_number_id meegegeven → default uit settings (conftest: 123456789)
    assert _FakeClient.captured["url"].endswith("/123456789/messages")


@pytest.mark.asyncio
async def test_send_template_builds_meta_template_request(wa_service):
    await wa_service.send_template_message(
        to_phone="32499123456",
        template_name="appointment_reminder",
        language_code="nl",
        body_params=["Jan", "Repto BV", "maandag 10:00"],
        phone_number_id="PNID_42",
    )
    body = _FakeClient.captured["json"]
    assert body["type"] == "template"
    assert body["template"]["name"] == "appointment_reminder"
    assert body["template"]["language"] == {"code": "nl"}
    params = body["template"]["components"][0]["parameters"]
    assert [p["text"] for p in params] == ["Jan", "Repto BV", "maandag 10:00"]
    assert all(p["type"] == "text" for p in params)


@pytest.mark.asyncio
async def test_send_template_without_params_omits_components(wa_service):
    await wa_service.send_template_message(
        to_phone="32499123456",
        template_name="hello_world",
        language_code="en_US",
    )
    template = _FakeClient.captured["json"]["template"]
    assert "components" not in template
