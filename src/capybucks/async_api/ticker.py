from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import datetime

import pandas as pd

from capybucks.async_api.download import download, infer_asset_type
from capybucks.core.frames import (
    OptionChainFrames,
    actions_to_frame,
    news_to_frame,
    option_chain_to_frames,
    statement_to_pandas,
)
from capybucks.core.models import Quote, StatementKind
from capybucks.core.provider import Provider
from capybucks.core.registry import get_registry
from capybucks.exceptions import SymbolNotFound


class AsyncTicker:
    """Async handle for one symbol. Sync ``Ticker`` wraps these methods."""

    def __init__(self, symbol: str, *, provider: str | None = None) -> None:
        self.symbol = symbol.upper()
        self.provider = provider

    def _source(self) -> Provider:
        return get_registry().resolve(
            provider=self.provider,
            asset_type=infer_asset_type(self.symbol),
            interval="1d",
        )

    async def history(
        self,
        *,
        period: str = "1mo",
        interval: str = "1d",
        start: datetime | None = None,
        end: datetime | None = None,
        auto_adjust: bool = True,
        cache: bool = True,
    ) -> pd.DataFrame:
        return await download(
            self.symbol,
            period=period,
            interval=interval,
            start=start,
            end=end,
            auto_adjust=auto_adjust,
            provider=self.provider,
            cache=cache,
        )

    async def _statement(self, kind: StatementKind, *, quarterly: bool) -> pd.DataFrame:
        table = await self._source().fetch_statement(
            self.symbol, kind=kind, quarterly=quarterly
        )
        return statement_to_pandas(table)

    async def financials(self) -> pd.DataFrame:
        return await self._statement(StatementKind.INCOME, quarterly=False)

    async def quarterly_financials(self) -> pd.DataFrame:
        return await self._statement(StatementKind.INCOME, quarterly=True)

    async def balance_sheet(self) -> pd.DataFrame:
        return await self._statement(StatementKind.BALANCE, quarterly=False)

    async def quarterly_balance_sheet(self) -> pd.DataFrame:
        return await self._statement(StatementKind.BALANCE, quarterly=True)

    async def cashflow(self) -> pd.DataFrame:
        return await self._statement(StatementKind.CASHFLOW, quarterly=False)

    async def quarterly_cashflow(self) -> pd.DataFrame:
        return await self._statement(StatementKind.CASHFLOW, quarterly=True)

    async def options(self) -> tuple[str, ...]:
        dates = await self._source().fetch_option_expirations(self.symbol)
        return tuple(dates)

    async def option_chain(self, expiration: str | None = None) -> OptionChainFrames:
        source = self._source()
        chosen = expiration
        if chosen is None:
            dates = await source.fetch_option_expirations(self.symbol)
            if not dates:
                raise SymbolNotFound(self.symbol, provider=source.name)
            chosen = dates[0]
        chain = await source.fetch_option_chain(self.symbol, expiration=chosen)
        return option_chain_to_frames(chain)

    async def news(self) -> pd.DataFrame:
        return news_to_frame(await self._source().fetch_news(self.symbol))

    async def actions(self) -> pd.DataFrame:
        return actions_to_frame(await self._source().fetch_actions(self.symbol))

    async def dividends(self) -> pd.Series:
        frame = await self.actions()
        series = frame["Dividends"]
        return series[series != 0]

    async def splits(self) -> pd.Series:
        frame = await self.actions()
        series = frame["Stock Splits"]
        return series[series != 0]

    async def quote(self) -> Quote:
        return await self._source().fetch_quote(self.symbol)

    def stream(self) -> AsyncIterator[Quote]:
        return self._source().stream_quotes(self.symbol)
