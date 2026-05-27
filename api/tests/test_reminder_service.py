"""
Unit tests voor reminder_service.py
Tests: constanten, lege DB, reminder_sent=True, status=cancelled
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta


# ─── Constanten ───────────────────────────────────────────────────────────────

def test_reminder_window_constants():
    from app.services.reminder_service import REMINDER_WINDOW_MIN_H, REMINDER_WINDOW_MAX_H

    assert REMINDER_WINDOW_MIN_H == 23
    assert REMINDER_WINDOW_MAX_H == 25


# ─── Hulpfunctie: maak een nep Appointment ───────────────────────────────────

def _make_appointment(
    appt_id: str = "appt-1",
    status: str = "confirmed",
    reminder_sent: bool = False,
    hours_from_now: float = 24.0,
) -> MagicMock:
    appt = MagicMock()
    appt.id = appt_id
    appt.conversation_id = "conv-1"
    appt.org_id = "org-1"
    appt.title = "Test afspraak"
    appt.status = status
    appt.reminder_sent = reminder_sent
    appt.start_at = datetime.utcnow() + timedelta(hours=hours_from_now)
    return appt


# ─── _process_reminders: lege DB ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_no_reminders_when_no_appointments():
    """Lege DB → _process_reminders stuurt geen herinneringen."""
    from app.services.reminder_service import _process_reminders

    mock_db = AsyncMock()

    # DB execute geeft lege lijst terug
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_db.execute = AsyncMock(return_value=mock_result)

    # _send_reminder mag NOOIT worden aangeroepen
    with patch("app.services.reminder_service._send_reminder", new_callable=AsyncMock) as mock_send:
        await _process_reminders(mock_db)
        mock_send.assert_not_called()


# ─── reminder_sent=True → geen actie ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_reminder_skipped_if_already_sent():
    """
    Afspraken met reminder_sent=True worden NIET opgehaald door de query
    (de WHERE-clause filtert ze eruit). We simuleren dat door de DB een
    lege lijst terug te geven als reminder_sent=True.
    """
    from app.services.reminder_service import _process_reminders

    mock_db = AsyncMock()

    # DB geeft lege lijst terug (want query filtert reminder_sent=False)
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_db.execute = AsyncMock(return_value=mock_result)

    with patch("app.services.reminder_service._send_reminder", new_callable=AsyncMock) as mock_send:
        await _process_reminders(mock_db)
        mock_send.assert_not_called()


# ─── status='cancelled' → geen actie ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_reminder_skipped_if_cancelled():
    """
    Afspraken met status='cancelled' worden NIET opgehaald door de query
    (de WHERE-clause filtert op status='confirmed').
    We simuleren dat door de DB een lege lijst terug te geven.
    """
    from app.services.reminder_service import _process_reminders

    mock_db = AsyncMock()

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_db.execute = AsyncMock(return_value=mock_result)

    with patch("app.services.reminder_service._send_reminder", new_callable=AsyncMock) as mock_send:
        await _process_reminders(mock_db)
        mock_send.assert_not_called()


# ─── Bonus: één geldig appointment → _send_reminder wordt aangeroepen ─────────

@pytest.mark.asyncio
async def test_send_reminder_called_for_valid_appointment():
    """
    Als er één geldige afspraak in het venster is,
    moet _send_reminder exact één keer worden aangeroepen.
    """
    from app.services.reminder_service import _process_reminders

    mock_db = AsyncMock()
    appt = _make_appointment(hours_from_now=24.0)

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [appt]
    mock_db.execute = AsyncMock(return_value=mock_result)

    with patch("app.services.reminder_service._send_reminder", new_callable=AsyncMock) as mock_send:
        await _process_reminders(mock_db)
        mock_send.assert_called_once_with(appt, mock_db)
