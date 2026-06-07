"""
Tests voor de lead-notificatie-rendering (email_service._build_html).

Belangrijk vangnet: send_lead_notification slikt alle fouten in (notificatie is
niet-kritisch), dus een renderfout op een web-/e-maillead zou STIL leiden tot
verdwenen notificaties. Deze test rendert daarom direct _build_html voor een
web_form-gesprek zonder telefoon en controleert het kanaal-label + dat null-velden
niet crashen. Geen httpx nodig.
"""
from types import SimpleNamespace

from app.services.email_service import _build_html


def _conv(**kw):
    base = dict(id="cv-1", channel="whatsapp", wa_contact_name="Jan",
                wa_contact_phone="32470123456")
    base.update(kw)
    return SimpleNamespace(**base)


def _org():
    return SimpleNamespace(name="Klant BV", crm_type="airtable")


def _contact(**kw):
    base = dict(name=None, phone=None, email=None, score=None, score_reason=None)
    base.update(kw)
    return SimpleNamespace(**base)


def test_build_html_web_form_null_phone():
    """Web-form-lead zonder telefoon: rendert het kanaal-label + e-mail, geen crash."""
    html = _build_html(
        _conv(channel="web_form", wa_contact_phone=None, wa_contact_name=None),
        _org(), "Ik wil een demo", [],
        _contact(name="Jan Janssen", email="jan@x.be", score="lauw", score_reason="lauw — ..."),
    )
    assert isinstance(html, str)
    assert "Webformulier" in html        # kanaal-label gerenderd
    assert "Jan Janssen" in html         # naam uit Contact
    assert "jan@x.be" in html            # e-mailrij aanwezig
    assert "32470" not in html           # geen telefoon → geen telefoonrij


def test_build_html_whatsapp_label():
    """WhatsApp-pad blijft het juiste label + telefoon tonen."""
    html = _build_html(
        _conv(), _org(), "hallo", [],
        _contact(phone="32470123456", score="warm"),
    )
    assert "WhatsApp" in html
    assert "32470123456" in html
