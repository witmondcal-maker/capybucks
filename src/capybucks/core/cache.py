from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol

import pandas as pd

from capybucks.core.models import History, OHLCVBar, Provenance

CacheKey = tuple[str, str, str, str, str]
SeriesId = tuple[str, str, str]


def history_cache_key(
    *,
    provider: str,
    symbol: str,
    interval: str,
    start: str,
    end: str,
) -> CacheKey:
    return (provider, symbol.upper(), interval, start, end)


def series_id(*, provider: str, symbol: str, interval: str) -> SeriesId:
    return (provider, symbol.upper(), interval)


class CacheBackend(Protocol):
    def get_series(self, key: SeriesId) -> History | None: ...

    def put_series(self, key: SeriesId, value: History) -> None: ...


class MemoryCache:
    def __init__(self) -> None:
        self._store: dict[SeriesId, History] = {}

    def get_series(self, key: SeriesId) -> History | None:
        return self._store.get(key)

    def put_series(self, key: SeriesId, value: History) -> None:
        existing = self._store.get(key)
        self._store[key] = value if existing is None else merge_history(existing, value)


class ParquetCache:
    """On-disk OHLCV, one series per provider/symbol/interval. Same source only."""

    def __init__(self, root: Path) -> None:
        self.root = root

    def _dir(self, key: SeriesId) -> Path:
        provider, symbol, interval = key
        return self.root / provider / symbol / interval

    def get_series(self, key: SeriesId) -> History | None:
        folder = self._dir(key)
        parquet = folder / "ohlcv.parquet"
        meta_path = folder / "meta.json"
        if not parquet.exists() or not meta_path.exists():
            return None
        frame = pd.read_parquet(parquet)
        raw = json.loads(meta_path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            return None
        provenance = Provenance.model_validate(raw)
        bars = [
            OHLCVBar(
                timestamp=_as_datetime(index),
                open=float(row["open"]),
                high=float(row["high"]),
                low=float(row["low"]),
                close=float(row["close"]),
                adj_close=None
                if pd.isna(row["adj_close"])
                else float(row["adj_close"]),
                volume=None if pd.isna(row["volume"]) else float(row["volume"]),
            )
            for index, row in frame.iterrows()
        ]
        return History(bars=bars, provenance=provenance)

    def put_series(self, key: SeriesId, value: History) -> None:
        existing = self.get_series(key)
        merged = value if existing is None else merge_history(existing, value)
        folder = self._dir(key)
        folder.mkdir(parents=True, exist_ok=True)
        frame = pd.DataFrame(
            {
                "open": [bar.open for bar in merged.bars],
                "high": [bar.high for bar in merged.bars],
                "low": [bar.low for bar in merged.bars],
                "close": [bar.close for bar in merged.bars],
                "adj_close": [bar.adj_close for bar in merged.bars],
                "volume": [bar.volume for bar in merged.bars],
            },
            index=pd.DatetimeIndex(
                [bar.timestamp for bar in merged.bars],
                name="timestamp",
            ),
        )
        frame.to_parquet(folder / "ohlcv.parquet")
        (folder / "meta.json").write_text(
            merged.provenance.model_dump_json(),
            encoding="utf-8",
        )


class LayeredCache:
    def __init__(self, memory: MemoryCache, disk: ParquetCache | None) -> None:
        self.memory = memory
        self.disk = disk

    def get_series(self, key: SeriesId) -> History | None:
        hit = self.memory.get_series(key)
        if hit is not None:
            return hit
        if self.disk is None:
            return None
        loaded = self.disk.get_series(key)
        if loaded is not None:
            self.memory.put_series(key, loaded)
        return loaded

    def put_series(self, key: SeriesId, value: History) -> None:
        self.memory.put_series(key, value)
        if self.disk is not None:
            self.disk.put_series(key, value)


def merge_history(left: History, right: History) -> History:
    if left.provenance.provider != right.provenance.provider:
        raise ValueError("refusing to merge OHLCV from two providers")
    by_ts = {bar.timestamp: bar for bar in left.bars}
    by_ts.update({bar.timestamp: bar for bar in right.bars})
    bars = [by_ts[key] for key in sorted(by_ts)]
    provenance = right.provenance.model_copy(
        update={
            "covered_from": _min_dt(
                left.provenance.covered_from, right.provenance.covered_from
            ),
            "covered_to": _max_dt(
                left.provenance.covered_to, right.provenance.covered_to
            ),
        }
    )
    return History(bars=bars, provenance=provenance)


def coverage_gaps(
    history: History | None,
    start: datetime,
    end: datetime,
) -> list[tuple[datetime, datetime]]:
    if history is None or not history.bars:
        return [(start, end)]
    first = history.provenance.covered_from or history.bars[0].timestamp
    last = history.provenance.covered_to or history.bars[-1].timestamp
    if end < first or start > last:
        return [(start, end)]
    gaps: list[tuple[datetime, datetime]] = []
    if start < first:
        gaps.append((start, first))
    if end > last:
        gaps.append((last, end))
    return gaps


def _min_dt(left: datetime | None, right: datetime | None) -> datetime | None:
    if left is None:
        return right
    if right is None:
        return left
    return min(left, right)


def _max_dt(left: datetime | None, right: datetime | None) -> datetime | None:
    if left is None:
        return right
    if right is None:
        return left
    return max(left, right)


def slice_history(history: History, start: datetime, end: datetime) -> History:
    bars = [bar for bar in history.bars if start <= bar.timestamp <= end]
    return History(bars=bars, provenance=history.provenance)


def _as_datetime(value: object) -> datetime:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value
    if isinstance(value, pd.Timestamp):
        converted = value.to_pydatetime()
        if converted.tzinfo is None:
            return converted.replace(tzinfo=UTC)
        return converted
    raise TypeError(f"unsupported timestamp {type(value)!r}")
