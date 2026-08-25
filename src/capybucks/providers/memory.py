from __future__ import annotations

from datetime import UTC, datetime, timedelta

from capybucks.core.models import (
    ActionEvent,
    AssetType,
    History,
    NewsItem,
    OHLCVBar,
    OptionChain,
    OptionContract,
    Provenance,
    Quote,
    StatementKind,
    StatementTable,
)
from capybucks.core.provider import Provider
from capybucks.exceptions import SymbolNotFound

KNOWN_EQUITIES = frozenset({"AAPL", "MSFT"})


class MemoryProvider(Provider):
    """Deterministic OHLCV for tests. Not a market source."""

    name = "memory"
    requires_key = False
    supports_stream = False

    def supports(self, asset_type: AssetType) -> bool:
        return asset_type is AssetType.EQUITY

    async def fetch_history(
        self,
        symbol: str,
        *,
        start: datetime | None = None,
        end: datetime | None = None,
        interval: str = "1d",
        auto_adjust: bool = True,
    ) -> History:
        ticker = symbol.upper()
        if ticker not in KNOWN_EQUITIES:
            raise SymbolNotFound(ticker, provider=self.name)
        finish = end or datetime.now(UTC)
        if finish.tzinfo is None:
            finish = finish.replace(tzinfo=UTC)
        begin = start or (finish - timedelta(days=5))
        if begin.tzinfo is None:
            begin = begin.replace(tzinfo=UTC)
        bars: list[OHLCVBar] = []
        seed = 100.0 if ticker == "AAPL" else 200.0
        cursor = begin
        day = 0
        while cursor <= finish and day < 10:
            price = seed + day
            adj = price if auto_adjust else price * 0.99
            bars.append(
                OHLCVBar(
                    timestamp=cursor,
                    open=price,
                    high=price + 1,
                    low=price - 1,
                    close=price,
                    adj_close=adj,
                    volume=1_000_000 + day,
                )
            )
            cursor = cursor + timedelta(days=1)
            day += 1
        if not bars:
            raise SymbolNotFound(ticker, provider=self.name)
        return History(
            bars=bars,
            provenance=Provenance(
                provider=self.name,
                delayed=False,
                adjustment="split_and_dividend" if auto_adjust else "none",
                asof=finish,
                timezone="UTC",
                currency="USD",
            ),
        )

    async def fetch_quote(self, symbol: str) -> Quote:
        ticker = symbol.upper()
        if ticker not in KNOWN_EQUITIES:
            raise SymbolNotFound(ticker, provider=self.name)
        price = 100.0 if ticker == "AAPL" else 200.0
        return Quote(
            symbol=ticker,
            price=price,
            timestamp=datetime.now(UTC),
            currency="USD",
            delayed=False,
        )

    async def fetch_statement(
        self,
        symbol: str,
        *,
        kind: StatementKind,
        quarterly: bool = False,
    ) -> StatementTable:
        self._require(symbol)
        return StatementTable(
            kind=kind,
            quarterly=quarterly,
            periods=["2023-12-31", "2022-12-31"],
            items=["Total Revenue", "Net Income"],
            values=[[100.0, 90.0], [20.0, 18.0]],
        )

    async def fetch_option_expirations(self, symbol: str) -> list[str]:
        self._require(symbol)
        return ["2024-01-19", "2024-02-16"]

    async def fetch_option_chain(self, symbol: str, *, expiration: str) -> OptionChain:
        self._require(symbol)
        call = OptionContract(
            contract_symbol=f"{symbol.upper()}240119C00100000",
            strike=100.0,
            last_price=12.5,
            bid=12.0,
            ask=13.0,
            volume=10.0,
            open_interest=100.0,
            implied_volatility=0.4,
            in_the_money=True,
            expiration=expiration,
        )
        put = OptionContract(
            contract_symbol=f"{symbol.upper()}240119P00100000",
            strike=100.0,
            last_price=1.5,
            bid=1.4,
            ask=1.6,
            volume=5.0,
            open_interest=50.0,
            implied_volatility=0.35,
            in_the_money=False,
            expiration=expiration,
        )
        return OptionChain(expiration=expiration, calls=[call], puts=[put])

    async def fetch_news(self, symbol: str) -> list[NewsItem]:
        self._require(symbol)
        return [
            NewsItem(
                title=f"{symbol.upper()} test headline",
                publisher="MemoryWire",
                link="https://example.com/news",
                published_at=datetime(2024, 1, 8, tzinfo=UTC),
            )
        ]

    async def fetch_actions(self, symbol: str) -> list[ActionEvent]:
        self._require(symbol)
        return [
            ActionEvent(
                timestamp=datetime(2023, 8, 11, tzinfo=UTC),
                kind="dividend",
                value=0.24,
            ),
            ActionEvent(
                timestamp=datetime(2020, 8, 31, tzinfo=UTC),
                kind="split",
                value=4.0,
            ),
        ]

    def _require(self, symbol: str) -> None:
        if symbol.upper() not in KNOWN_EQUITIES:
            raise SymbolNotFound(symbol.upper(), provider=self.name)
