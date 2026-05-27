"""
Unit tests voor ai_service.py
Tests: _parse_iso, APPOINTMENT_TOOL schema, build_system_prompt, generate_reply (gemockt)
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime


# ─── _parse_iso ───────────────────────────────────────────────────────────────

def test_parse_iso_valid_formats():
    from app.services.ai_service import _parse_iso

    cases = [
        ("2025-06-15T09:30:00", datetime(2025, 6, 15, 9, 30, 0)),
        ("2025-06-15T09:30",    datetime(2025, 6, 15, 9, 30)),
        ("2025-06-15 09:30:00", datetime(2025, 6, 15, 9, 30, 0)),
        ("2025-06-15 09:30",    datetime(2025, 6, 15, 9, 30)),
        ("2025-06-15",          datetime(2025, 6, 15)),
    ]
    for dt_str, expected in cases:
        result = _parse_iso(dt_str)
        assert result == expected, f"Mislukt voor: {dt_str!r}"


def test_parse_iso_invalid_returns_none():
    from app.services.ai_service import _parse_iso

    assert _parse_iso("") is None
    assert _parse_iso("onzin-datum") is None
    assert _parse_iso("15/06/2025") is None
    assert _parse_iso("not-a-date") is None


# ─── APPOINTMENT_TOOL schema ──────────────────────────────────────────────────

def test_appointment_tool_schema():
    from app.services.ai_service import APPOINTMENT_TOOL

    assert APPOINTMENT_TOOL["name"] == "create_appointment"

    required = APPOINTMENT_TOOL["input_schema"]["required"]
    assert "title" in required
    assert "start_at" in required
    assert "end_at" in required

    props = APPOINTMENT_TOOL["input_schema"]["properties"]
    assert "title" in props
    assert "start_at" in props
    assert "end_at" in props
    assert "contact_name" in props


# ─── build_system_prompt ──────────────────────────────────────────────────────

def _make_org(sector: str, name: str = "TestBedrijf"):
    """Maak een lichtgewicht nep-organisatie-object."""
    org = MagicMock()
    org.sector = sector
    org.name = name
    org.ai_tone = "professioneel"
    org.ai_system_prompt = ""
    return org


def test_build_system_prompt_installateur():
    from app.services.ai_service import build_system_prompt, CLOSING_INSTRUCTION

    org = _make_org("installateur")
    prompt = build_system_prompt(org)

    assert "installatiebedrijf" in prompt
    assert "TestBedrijf" in prompt
    # CLOSING_INSTRUCTION bevat de opening tekst "BELANGRIJK"
    assert "BELANGRIJK" in prompt
    assert "[GESPREK_AFGEROND]" in prompt


def test_build_system_prompt_fallback_to_algemeen():
    from app.services.ai_service import build_system_prompt, SECTOR_PROMPTS

    org = _make_org("onbekende_sector_xyz")
    prompt = build_system_prompt(org)

    # Moet de "algemeen" template gebruiken
    # De algemeen-template bevat "receptionist van {company_name}" zonder sector-specifiek woord
    algemeen_base = SECTOR_PROMPTS["algemeen"].format(
        company_name="TestBedrijf",
        tone="professioneel",
        company_info="",
    )
    assert algemeen_base in prompt


def test_build_system_prompt_contains_closing_instruction():
    from app.services.ai_service import build_system_prompt, CLOSING_INSTRUCTION

    for sector in ["installateur", "makelaar", "kinesist", "garage", "algemeen"]:
        org = _make_org(sector)
        prompt = build_system_prompt(org)
        assert CLOSING_INSTRUCTION in prompt, f"CLOSING_INSTRUCTION ontbreekt voor sector: {sector}"


# ─── generate_reply (gemockt) ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_generate_reply_returns_string():
    """
    Controleer dat generate_reply een string retourneert
    zonder echte Anthropic API calls te maken.
    """
    from app.services.ai_service import AIService

    # Nep DB-sessie
    mock_db = AsyncMock()

    # Nep organisatie
    mock_org = MagicMock()
    mock_org.id = "org-1"
    mock_org.name = "Test Installateurs"
    mock_org.sector = "installateur"
    mock_org.ai_tone = "vriendelijk"
    mock_org.ai_system_prompt = ""

    # DB execute voor org → geeft mock_org terug
    mock_scalar_org = MagicMock()
    mock_scalar_org.scalar_one_or_none.return_value = mock_org

    # DB execute voor history → geeft lege lijst terug
    mock_scalar_history = MagicMock()
    mock_scalar_history.scalars.return_value.all.return_value = []

    # Stel beide execute calls in (org eerst, dan history)
    mock_db.execute = AsyncMock(
        side_effect=[mock_scalar_org, mock_scalar_history]
    )

    # Nep Anthropic response met tekst-blok
    mock_text_block = MagicMock()
    mock_text_block.text = "Goedendag! Waarmee kan ik u helpen?"
    mock_text_block.type = "text"
    # hasattr(block, "text") moet True zijn
    type(mock_text_block).text = property(lambda self: "Goedendag! Waarmee kan ik u helpen?")

    mock_response = MagicMock()
    mock_response.stop_reason = "end_turn"  # geen tool_use loop
    mock_response.content = [mock_text_block]

    # Nep conversatie
    mock_conversation = MagicMock()
    mock_conversation.id = "conv-1"
    mock_conversation.org_id = "org-1"

    with patch("app.services.ai_service.anthropic.AsyncAnthropic") as mock_anthropic_cls:
        mock_client = AsyncMock()
        mock_anthropic_cls.return_value = mock_client
        mock_client.messages.create = AsyncMock(return_value=mock_response)

        service = AIService(db=mock_db)
        result = await service.generate_reply(
            conversation=mock_conversation,
            incoming_message="Hallo, ik heb een lekkage.",
        )

    assert isinstance(result, str)
    assert len(result) > 0
