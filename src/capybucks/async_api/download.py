from __future__ import annotations

import asyncio
import os
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path
from typing import Literal

import pandas as pd

from capybucks.core.cache import (
    LayeredCache,
    MemoryCache,
    ParquetCache,
    coverage_gaps,
    merge_history,
    series_id,
    slice_history,
)
from capybucks.core.frames import history_to_pandas
from capybucks.core.models import AssetType, History
from capybucks.core.period import resolve_range
from capybucks.core.provider import Provider
from capybucks.core.registry import get_registry
from capybucks.core.retry import with_retry
from capybucks.exceptions import CapybucksError, MultiDownloadError, SymbolNotFound

_CRYPTO_TICKERS = frozenset({"BTC", "ETH", "SOL", "DOGE", "XRP", "ADA"})
_cache = LayeredCache(MemoryCache(), None)


def configure_cache(disk_dir: Path | None) -> None:
    """Point the process cache at a directory (tests use a tmp path)."""
    global _cache
    disk = ParquetCache(disk_dir) if disk_dir is not None else None
    _cache = LayeredCache(MemoryCache(), disk)


def _ensure_cache() -> LayeredCache:
    if _cache.disk is None:
        raw = os.environ.get("CAPYBUCKS_CACHE_DIR")
        root = Path(raw) if raw else Path.home() / ".cache" / "capybucks"
        configure_cache(root)
    return _cache


def infer_asset_type(symbol: str) -> AssetType:
    upper = symbol.upper()
    if "/" in upper:
        return AssetType.FX
    if (
        upper in _CRYPTO_TICKERS
        or "-" in upper
        or upper.endswith("USDT")
        or upper.endswith("-USD")
    ):
        return AssetType.CRYPTO
    return AssetType.EQUITY


def _normalize_symbols(tickers: str | Sequence[str]) -> list[str]:
    if isinstance(tickers, str):
        parts = tickers.replace(",", " ").split()
        return [part.strip().upper() for part in parts if part.strip()]
    return [str(ticker).strip().upper() for ticker in tickers if str(ticker).strip()]


async def _provider_fetch(
    provider: Provider,
    symbol: str,
    *,
    start: datetime,
    end: datetime,
    interval: str,
    auto_adjust: bool,
) -> History:
    @with_retry
    async def _call() -> History:
        history = await provider.fetch_history(
            symbol,
            start=start,
            end=end,
            interval=interval,
            auto_adjust=auto_adjust,
        )
        if not history.bars:
            raise SymbolNotFound(symbol, provider=provider.name)
        return history

    return await _call()


async def _fetch_one(
    provider: Provider,
    symbol: str,
    *,
    start: datetime,
    end: datetime,
    interval: str,
    auto_adjust: bool,
    use_cache: bool,
) -> pd.DataFrame:
    cache = _ensure_cache()
    key = series_id(provider=provider.name, symbol=symbol, interval=interval)
    stored = cache.get_series(key) if use_cache else None
    gaps = coverage_gaps(stored, start, end)
    if stored is not None and not gaps:
        return history_to_pandas(slice_history(stored, start, end))

    merged: History | None = stored
    for gap_start, gap_end in gaps:
        piece = await _provider_fetch(
            provider,
            symbol,
            start=gap_start,
            end=gap_end,
            interval=interval,
            auto_adjust=auto_adjust,
        )
        stamped = piece.model_copy(
            update={
                "provenance": piece.provenance.model_copy(
                    update={"covered_from": gap_start, "covered_to": gap_end}
                )
            }
        )
        merged = stamped if merged is None else merge_history(merged, stamped)
    if merged is None or not merged.bars:
        raise SymbolNotFound(symbol, provider=provider.name)
    if use_cache:
        cache.put_series(key, merged)
    sliced = slice_history(merged, start, end)
    if not sliced.bars:
        raise SymbolNotFound(symbol, provider=provider.name)
    return history_to_pandas(sliced)


async def download(
    tickers: str | Sequence[str],
    *,
    period: str = "1mo",
    interval: str = "1d",
    start: datetime | None = None,
    end: datetime | None = None,
    auto_adjust: bool = True,
    provider: str | None = None,
    group_by: Literal["ticker", "column"] = "ticker",
    cache: bool = True,
) -> pd.DataFrame:
    """Fetch OHLCV. One ticker → flat columns; several → MultiIndex columns."""
    symbols = _normalize_symbols(tickers)
    if not symbols:
        raise ValueError("download() requires at least one ticker")
    begin, finish = resolve_range(period=period, start=start, end=end)

    async def _one(symbol: str) -> pd.DataFrame:
        asset_type = infer_asset_type(symbol)
        source = get_registry().resolve(
            provider=provider,
            asset_type=asset_type,
            interval=interval,
        )
        return await _fetch_one(
            source,
            symbol,
            start=begin,
            end=finish,
            interval=interval,
            auto_adjust=auto_adjust,
            use_cache=cache,
        )

    if len(symbols) == 1:
        return await _one(symbols[0])

    gathered = await asyncio.gather(
        *[_one(symbol) for symbol in symbols],
        return_exceptions=True,
    )
    frames: dict[str, pd.DataFrame] = {}
    errors: dict[str, CapybucksError] = {}
    for symbol, result in zip(symbols, gathered, strict=True):
        if isinstance(result, CapybucksError):
            errors[symbol] = result
        elif isinstance(result, BaseException):
            wrapped = ProviderErrorFromBase(result)
            errors[symbol] = wrapped
        else:
            frames[symbol] = result

    if not frames:
        raise MultiDownloadError(errors)

    combined = _combine(frames, group_by=group_by)
    combined.attrs["errors"] = {name: str(exc) for name, exc in errors.items()}
    if frames:
        sample = next(iter(frames.values()))
        for key in ("provider", "delayed", "adjustment", "asof", "currency"):
            combined.attrs.setdefault(key, sample.attrs.get(key))
    return combined


class ProviderErrorFromBase(CapybucksError):
    """Wrap unexpected exceptions from a provider so the batch can continue."""

    def __init__(self, cause: BaseException) -> None:
        self.cause = cause
        super().__init__(str(cause))


def _combine(
    frames: dict[str, pd.DataFrame],
    *,
    group_by: Literal["ticker", "column"],
) -> pd.DataFrame:
    if group_by == "ticker":
        pieces = []
        for symbol, frame in frames.items():
            renamed = frame.copy()
            renamed.columns = pd.MultiIndex.from_product([[symbol], renamed.columns])
            pieces.append(renamed)
        return pd.concat(pieces, axis=1).sort_index()

    pieces = []
    for symbol, frame in frames.items():
        renamed = frame.copy()
        renamed.columns = pd.MultiIndex.from_product([renamed.columns, [symbol]])
        pieces.append(renamed)
    return pd.concat(pieces, axis=1).sort_index()
