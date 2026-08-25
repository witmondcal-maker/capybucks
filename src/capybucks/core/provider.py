from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from datetime import datetime

from capybucks.core.models import (
    ActionEvent,
    AssetType,
    History,
    NewsItem,
    OptionChain,
    Quote,
    StatementKind,
    StatementTable,
)
from capybucks.exceptions import StreamingNotSupportedError


class Provider(ABC):
    """One market-data source. Implementations live under `providers/`."""

    name: str
    requires_key: bool = False
    supports_stream: bool = False

    @abstractmethod
    def supports(self, asset_type: AssetType) -> bool:
        """Whether this source covers the asset class at all."""

    @abstractmethod
    async def fetch_history(
        self,
        symbol: str,
        *,
        start: datetime | None = None,
        end: datetime | None = None,
        interval: str = "1d",
        auto_adjust: bool = True,
    ) -> History:
        """Return a validated OHLCV series. Raise SymbolNotFound if empty."""

    async def fetch_quote(self, symbol: str) -> Quote:
        raise NotImplementedError(f"{self.name} does not implement fetch_quote")

    async def fetch_statement(
        self,
        symbol: str,
        *,
        kind: StatementKind,
        quarterly: bool = False,
    ) -> StatementTable:
        raise NotImplementedError(f"{self.name} does not implement financials")

    async def fetch_option_expirations(self, symbol: str) -> list[str]:
        raise NotImplementedError(f"{self.name} does not implement options")

    async def fetch_option_chain(self, symbol: str, *, expiration: str) -> OptionChain:
        raise NotImplementedError(f"{self.name} does not implement options")

    async def fetch_news(self, symbol: str) -> list[NewsItem]:
        raise NotImplementedError(f"{self.name} does not implement news")

    async def fetch_actions(self, symbol: str) -> list[ActionEvent]:
        raise NotImplementedError(f"{self.name} does not implement dividends/splits")

    def stream_quotes(self, symbol: str) -> AsyncIterator[Quote]:
        raise StreamingNotSupportedError(self.name)
