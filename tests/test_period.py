from __future__ import annotations

from datetime import UTC, datetime

from capybucks.core.period import resolve_range


def test_ytd_starts_january_first() -> None:
    now = datetime(2026, 8, 23, tzinfo=UTC)
    start, end = resolve_range(period="ytd", start=None, end=None, now=now)
    assert start == datetime(2026, 1, 1, tzinfo=UTC)
    assert end == now
