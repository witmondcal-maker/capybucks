from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import Literal

import pandas as pd

from capybucks.async_api.download import download as async_download
from capybucks.async_api.ticker import AsyncTicker
from capybucks.core.frames import OptionChainFrames
from capybucks.core.loop import run_sync
from capybucks.core.models import Quote


def download(
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
    """Fetch OHLCV as a pandas DataFrame.

    One ticker returns flat columns (``Open``, ``High``, ``Low``, ``Close``,
    ``Adj Close``, ``Volume``). Several tickers return a MultiIndex. Provenance
    is on ``df.attrs``. Missing names raise ``SymbolNotFound``, not an empty
    frame. Safe to call from Jupyter (running event loop).

    Args:
        tickers: One symbol, a comma/space-separated string, or a sequence.
        period: Lookback if ``start`` is omitted (``1d`` … ``max``, ``ytd``).
        interval: Bar size (``1m``, ``1h``, ``1d``, ``1wk``, ``1mo``, …).
        start: Inclusive window start. When set, ``period`` is ignored.
        end: Inclusive window end; defaults to now.
        auto_adjust: Prefer split/dividend-adjusted close when the source has it.
        provider: Pin a registered source. ``None`` uses the asset-class default.
        group_by: Multi-ticker layout: symbol on top (``ticker``) or field on top
            (``column``).
        cache: Read and write the parquet cache for this call.
    """
    return run_sync(
        lambda: async_download(
            tickers,
            period=period,
            interval=interval,
            start=start,
            end=end,
            auto_adjust=auto_adjust,
            provider=provider,
            group_by=group_by,
            cache=cache,
        )
    )


class Ticker:
    """Handle for one symbol. History shares ``download()``; other methods hit
    the same pinned (or default) provider.
    """

    def __init__(self, symbol: str, *, provider: str | None = None) -> None:
        self._async = AsyncTicker(symbol, provider=provider)

    @property
    def symbol(self) -> str:
        return self._async.symbol

    def history(
        self,
        *,
        period: str = "1mo",
        interval: str = "1d",
        start: datetime | None = None,
        end: datetime | None = None,
        auto_adjust: bool = True,
        cache: bool = True,
    ) -> pd.DataFrame:
        """OHLCV history. Same parameters as ``download()`` minus ``group_by``."""
        return run_sync(
            lambda: self._async.history(
                period=period,
                interval=interval,
                start=start,
                end=end,
                auto_adjust=auto_adjust,
                cache=cache,
            )
        )

    @property
    def financials(self) -> pd.DataFrame:
        """Annual income statement (line items × period-end dates)."""
        return run_sync(self._async.financials)

    @property
    def quarterly_financials(self) -> pd.DataFrame:
        """Quarterly income statement."""
        return run_sync(self._async.quarterly_financials)

    @property
    def balance_sheet(self) -> pd.DataFrame:
        """Annual balance sheet."""
        return run_sync(self._async.balance_sheet)

    @property
    def quarterly_balance_sheet(self) -> pd.DataFrame:
        """Quarterly balance sheet."""
        return run_sync(self._async.quarterly_balance_sheet)

    @property
    def cashflow(self) -> pd.DataFrame:
        """Annual cash-flow statement."""
        return run_sync(self._async.cashflow)

    @property
    def quarterly_cashflow(self) -> pd.DataFrame:
        """Quarterly cash-flow statement."""
        return run_sync(self._async.quarterly_cashflow)

    @property
    def options(self) -> tuple[str, ...]:
        """Listed option expiration dates as ISO ``YYYY-MM-DD`` strings."""
        return run_sync(self._async.options)

    def option_chain(self, expiration: str | None = None) -> OptionChainFrames:
        """Calls and puts for one expiry (nearest if ``expiration`` is omitted)."""
        return run_sync(lambda: self._async.option_chain(expiration))

    @property
    def news(self) -> pd.DataFrame:
        """Recent headlines when the provider has a news endpoint."""
        return run_sync(self._async.news)

    @property
    def actions(self) -> pd.DataFrame:
        """Dividends and splits aligned by timestamp."""
        return run_sync(self._async.actions)

    @property
    def dividends(self) -> pd.Series:
        """Non-zero dividend amounts."""
        return run_sync(self._async.dividends)

    @property
    def splits(self) -> pd.Series:
        """Split ratios (for example ``4.0`` for a 4-for-1)."""
        return run_sync(self._async.splits)

    def quote(self) -> Quote:
        """Latest snapshot the provider exposes (often delayed)."""
        return run_sync(self._async.quote)
