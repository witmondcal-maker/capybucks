from __future__ import annotations

from datetime import UTC, datetime, timedelta

_PERIODS: dict[str, timedelta] = {
    "1d": timedelta(days=1),
    "5d": timedelta(days=5),
    "1mo": timedelta(days=31),
    "3mo": timedelta(days=93),
    "6mo": timedelta(days=186),
    "1y": timedelta(days=366),
    "2y": timedelta(days=731),
    "5y": timedelta(days=365 * 5 + 2),
    "10y": timedelta(days=365 * 10 + 3),
    "max": timedelta(days=365 * 50),
}


def resolve_range(
    *,
    period: str,
    start: datetime | None,
    end: datetime | None,
    now: datetime | None = None,
) -> tuple[datetime, datetime]:
    """Map period/start/end to an inclusive UTC window."""
    moment = now or datetime.now(UTC)
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=UTC)
    moment = moment.replace(microsecond=0)
    finish = end if end is not None else moment
    if finish.tzinfo is None:
        finish = finish.replace(tzinfo=UTC)
    finish = finish.replace(microsecond=0)
    if start is not None:
        begin = start if start.tzinfo is not None else start.replace(tzinfo=UTC)
        return begin.replace(microsecond=0), finish
    if period == "ytd":
        begin = datetime(moment.year, 1, 1, tzinfo=UTC)
        return begin, finish
    try:
        delta = _PERIODS[period]
    except KeyError as exc:
        known = ", ".join(sorted(_PERIODS) + ["ytd"])
        raise ValueError(f"unknown period {period!r}; expected one of {known}") from exc
    return finish - delta, finish
