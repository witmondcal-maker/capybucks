"""Exchange session calendars. Requires `pip install capybucks[calendars]`."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol, cast

import pandas as pd


class ExchangeCalendar(Protocol):
    """Minimal surface of `exchange_calendars.ExchangeCalendar` we call."""

    tz: object

    def is_session(self, value: object) -> bool: ...


def calendar_for_symbol(symbol: str) -> str:
    """Map a ticker suffix to an exchange_calendars code."""
    upper = symbol.upper()
    if upper.endswith(".SA"):
        return "BVMF"
    if upper.endswith(".L"):
        return "XLON"
    return "XNYS"


def get_calendar(name: str) -> ExchangeCalendar:
    try:
        import exchange_calendars as xcals
    except ImportError as exc:
        raise ImportError(
            "session calendars require the [calendars] extra: "
            "pip install capybucks[calendars]"
        ) from exc
    return cast(ExchangeCalendar, xcals.get_calendar(name))


def is_session(
    when: datetime,
    *,
    symbol: str | None = None,
    calendar: str | None = None,
) -> bool:
    code = calendar or calendar_for_symbol(symbol or "")
    cal = get_calendar(code)
    stamp = pd.Timestamp(when)
    if stamp.tzinfo is not None:
        stamp = stamp.tz_convert(str(cal.tz)).tz_localize(None)
    return bool(cal.is_session(stamp.normalize()))
