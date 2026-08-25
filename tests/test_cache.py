from __future__ import annotations

from datetime import UTC, datetime

import pytest

from capybucks.core.cache import coverage_gaps, merge_history, slice_history
from capybucks.core.models import History, OHLCVBar, Provenance


def _bar(day: int, price: float) -> OHLCVBar:
    return OHLCVBar(
        timestamp=datetime(2024, 1, day, tzinfo=UTC),
        open=price,
        high=price + 1,
        low=price - 1,
        close=price,
        adj_close=price,
        volume=1.0,
    )


def test_merge_refuses_two_providers() -> None:
    left = History(
        bars=[_bar(1, 10.0)],
        provenance=Provenance(provider="yahoo"),
    )
    right = History(
        bars=[_bar(2, 11.0)],
        provenance=Provenance(provider="stooq"),
    )
    with pytest.raises(ValueError, match="two providers"):
        merge_history(left, right)


def test_coverage_gaps_and_slice() -> None:
    history = History(
        bars=[_bar(2, 10.0), _bar(3, 11.0)],
        provenance=Provenance(provider="memory"),
    )
    start = datetime(2024, 1, 1, tzinfo=UTC)
    end = datetime(2024, 1, 4, tzinfo=UTC)
    gaps = coverage_gaps(history, start, end)
    assert len(gaps) == 2
    sliced = slice_history(
        history,
        datetime(2024, 1, 2, tzinfo=UTC),
        datetime(2024, 1, 2, tzinfo=UTC),
    )
    assert len(sliced.bars) == 1
