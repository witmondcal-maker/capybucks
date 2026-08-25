from __future__ import annotations

from datetime import UTC, datetime

import pytest

from capybucks.calendars import calendar_for_symbol, get_calendar, is_session


def test_b3_calendar_code() -> None:
    assert calendar_for_symbol("PETR4.SA") == "BVMF"
    assert calendar_for_symbol("AAPL") == "XNYS"


def test_get_calendar_or_skip() -> None:
    pytest.importorskip("exchange_calendars")
    cal = get_calendar("XNYS")
    assert cal is not None
    monday = datetime(2024, 1, 8, 17, tzinfo=UTC)
    sunday = datetime(2024, 1, 7, 17, tzinfo=UTC)
    assert is_session(monday, calendar="XNYS") is True
    assert is_session(sunday, calendar="XNYS") is False
    assert is_session(monday, symbol="PETR4.SA") is True
