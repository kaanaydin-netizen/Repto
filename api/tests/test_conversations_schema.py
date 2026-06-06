"""
Regressietest voor ConversationOut na increment 2.

Sinds `Conversation.wa_contact_phone` nullable is (web-/e-maillead heeft geen nummer),
moet het response-schema een None-telefoon accepteren — anders gooit de eerste niet-
WhatsApp-lead in list_conversations/get_conversation een ResponseValidationError (500).
Het schema neemt ook het nieuwe `channel`-veld mee.
"""
from datetime import datetime
from types import SimpleNamespace

from app.routers.conversations import ConversationOut


def _conv(**overrides):
    base = dict(
        id="cv-1", org_id="org-1", channel="whatsapp",
        wa_contact_phone="32470123456", wa_contact_name="Jan", status="new",
        crm_synced_at=None, created_at=datetime.now(), updated_at=datetime.now(),
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def test_conversation_out_accepts_null_phone():
    """Web-/e-maillead zonder telefoon mag niet crashen op het response-schema."""
    out = ConversationOut.model_validate(_conv(channel="web_form", wa_contact_phone=None))
    assert out.wa_contact_phone is None
    assert out.channel == "web_form"


def test_conversation_out_includes_channel():
    """Het kanaal-veld wordt doorgegeven (whatsapp-pad blijft intact)."""
    out = ConversationOut.model_validate(_conv())
    assert out.channel == "whatsapp"
    assert out.wa_contact_phone == "32470123456"
