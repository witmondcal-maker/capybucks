from __future__ import annotations

from datetime import UTC, datetime, timedelta

from capybucks.core.http import get_json
from capybucks.core.jsonutil import require_list
from capybucks.core.models import AssetType, History, OHLCVBar, Provenance, Quote
from capybucks.core.provider import Provider
from capybucks.exceptions import ProviderError, SymbolNotFound

_OHLC = "https://api.coingecko.com/api/v3/coins/{coin_id}/ohlc"

_IDS = {
    "BTC": "bitcoin",
    "BTC-USD": "bitcoin",
    "BTCUSD": "bitcoin",
    "ETH": "ethereum",
    "ETH-USD": "ethereum",
    "ETHUSD": "ethereum",
    "SOL": "solana",
    "SOL-USD": "solana",
}

_DAY_BUCKETS = (1, 7, 14, 30, 90, 180, 365)


class CoinGeckoProvider(Provider):
    name = "coingecko"
    requires_key = False
    supports_stream = False

    def supports(self, asset_type: AssetType) -> bool:
        return asset_type is AssetType.CRYPTO

    async def fetch_history(
        self,
        symbol: str,
        *,
        start: datetime | None = None,
        end: datetime | None = None,
        interval: str = "1d",
        auto_adjust: bool = True,
    ) -> History:
        if interval not in {"1d", "1h"}:
            raise ProviderError(f"coingecko does not support interval {interval!r}")
        coin_id = to_coingecko_id(symbol)
        finish = end or datetime.now(UTC)
        begin = start or (finish - timedelta(days=30))
        params = {"vs_currency": "usd", "days": _days_param(begin, finish)}
        payload = await get_json(
            _OHLC.format(coin_id=coin_id),
            provider=self.name,
            params=params,
        )
        return parse_ohlc(payload, symbol=symbol)

    async def fetch_quote(self, symbol: str) -> Quote:
        history = await self.fetch_history(symbol, interval="1d")
        last = history.bars[-1]
        return Quote(
            symbol=symbol.upper(),
            price=last.close,
            timestamp=last.timestamp,
            currency="USD",
            delayed=True,
        )


def to_coingecko_id(symbol: str) -> str:
    key = symbol.upper().replace("/", "-")
    if key in _IDS:
        return _IDS[key]
    return symbol.lower()


def _days_param(start: datetime, end: datetime) -> str:
    span = max((end - start).days, 1)
    for bucket in _DAY_BUCKETS:
        if span <= bucket:
            return str(bucket)
    return "max"


def parse_ohlc(payload: object, *, symbol: str) -> History:
    rows = require_list(payload, where="coingecko ohlc")
    bars: list[OHLCVBar] = []
    for row in rows:
        if not isinstance(row, list) or len(row) < 5:
            continue
        ts_ms, open_, high, low, close = row[0], row[1], row[2], row[3], row[4]
        if not isinstance(ts_ms, int | float):
            continue
        stamp = datetime.fromtimestamp(float(ts_ms) / 1000.0, tz=UTC)
        close_f = float(close)
        bars.append(
            OHLCVBar(
                timestamp=stamp,
                open=float(open_),
                high=float(high),
                low=float(low),
                close=close_f,
                adj_close=close_f,
                volume=None,
            )
        )
    if not bars:
        raise SymbolNotFound(symbol, provider="coingecko")
    return History(
        bars=bars,
        provenance=Provenance(
            provider="coingecko",
            delayed=True,
            adjustment="none",
            asof=datetime.now(UTC),
            timezone="UTC",
            currency="USD",
        ),
    )
