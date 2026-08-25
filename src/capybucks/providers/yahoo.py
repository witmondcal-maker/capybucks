from __future__ import annotations

from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from capybucks.core.http import get_json
from capybucks.core.jsonutil import require_dict, require_list
from capybucks.core.models import (
    ActionEvent,
    AssetType,
    History,
    NewsItem,
    OHLCVBar,
    OptionChain,
    Provenance,
    Quote,
    StatementKind,
    StatementTable,
)
from capybucks.core.provider import Provider
from capybucks.exceptions import ProviderError, SymbolNotFound
from capybucks.providers.yahoo_fundamentals import (
    fetch_yahoo_actions,
    fetch_yahoo_chain,
    fetch_yahoo_expirations,
    fetch_yahoo_news,
    fetch_yahoo_statement,
)

_CHART = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"

_INTERVALS: dict[str, str] = {
    "1m": "1m",
    "2m": "2m",
    "5m": "5m",
    "15m": "15m",
    "30m": "30m",
    "60m": "60m",
    "90m": "90m",
    "1h": "1h",
    "1d": "1d",
    "5d": "5d",
    "1wk": "1wk",
    "1w": "1wk",
    "1mo": "1mo",
}


class YahooProvider(Provider):
    """Unofficial Yahoo chart endpoint. Zero-config; usually delayed."""

    name = "yahoo"
    requires_key = False
    supports_stream = False

    def supports(self, asset_type: AssetType) -> bool:
        return asset_type in {AssetType.EQUITY, AssetType.CRYPTO}

    async def fetch_history(
        self,
        symbol: str,
        *,
        start: datetime | None = None,
        end: datetime | None = None,
        interval: str = "1d",
        auto_adjust: bool = True,
    ) -> History:
        mapped = _INTERVALS.get(interval)
        if mapped is None:
            raise ProviderError(f"yahoo does not support interval {interval!r}")
        finish = end or datetime.now(UTC)
        begin = start or finish
        params = {
            "interval": mapped,
            "period1": str(int(begin.timestamp())),
            "period2": str(int(finish.timestamp()) + 1),
            "events": "div|split",
            "includeAdjustedClose": "true",
        }
        payload = await get_json(
            _CHART.format(symbol=symbol),
            provider=self.name,
            params=params,
        )
        return _parse_chart(payload, symbol=symbol, auto_adjust=auto_adjust)

    async def fetch_quote(self, symbol: str) -> Quote:
        history = await self.fetch_history(symbol, interval="1d")
        last = history.bars[-1]
        return Quote(
            symbol=symbol.upper(),
            price=last.close,
            timestamp=last.timestamp,
            currency=history.provenance.currency,
            delayed=True,
        )

    async def fetch_statement(
        self,
        symbol: str,
        *,
        kind: StatementKind,
        quarterly: bool = False,
    ) -> StatementTable:
        return await fetch_yahoo_statement(symbol, kind=kind, quarterly=quarterly)

    async def fetch_option_expirations(self, symbol: str) -> list[str]:
        return await fetch_yahoo_expirations(symbol)

    async def fetch_option_chain(self, symbol: str, *, expiration: str) -> OptionChain:
        return await fetch_yahoo_chain(symbol, expiration=expiration)

    async def fetch_news(self, symbol: str) -> list[NewsItem]:
        return await fetch_yahoo_news(symbol)

    async def fetch_actions(self, symbol: str) -> list[ActionEvent]:
        return await fetch_yahoo_actions(symbol)


def _parse_chart(payload: object, *, symbol: str, auto_adjust: bool) -> History:
    root = require_dict(payload, where="yahoo")
    chart = require_dict(root.get("chart"), where="yahoo.chart")
    error = chart.get("error")
    if error:
        raise SymbolNotFound(symbol, provider="yahoo")
    results = chart.get("result")
    if results is None:
        raise SymbolNotFound(symbol, provider="yahoo")
    rows = require_list(results, where="yahoo.chart.result")
    if not rows:
        raise SymbolNotFound(symbol, provider="yahoo")
    result = require_dict(rows[0], where="yahoo result")
    meta = require_dict(result.get("meta"), where="yahoo.meta")
    timestamps = require_list(result.get("timestamp"), where="yahoo.timestamp")
    indicators = require_dict(result.get("indicators"), where="yahoo.indicators")
    quotes = require_list(indicators.get("quote"), where="yahoo.quote")
    quote = require_dict(quotes[0], where="yahoo.quote[0]")
    adj_list = _adj_closes(indicators)

    tz_name = meta.get("exchangeTimezoneName")
    if not isinstance(tz_name, str) and symbol.upper().endswith(".SA"):
        tz_name = "America/Sao_Paulo"
    tz = ZoneInfo(str(tz_name)) if isinstance(tz_name, str) else UTC
    currency = meta.get("currency")
    currency_s = str(currency) if isinstance(currency, str) else "USD"

    opens = require_list(quote.get("open"), where="open")
    highs = require_list(quote.get("high"), where="high")
    lows = require_list(quote.get("low"), where="low")
    closes = require_list(quote.get("close"), where="close")
    volumes = require_list(quote.get("volume"), where="volume")

    bars: list[OHLCVBar] = []
    for index, raw_ts in enumerate(timestamps):
        close = _num(closes[index]) if index < len(closes) else None
        if close is None:
            continue
        ts = datetime.fromtimestamp(int(_num(raw_ts) or 0), tz=UTC).astimezone(tz)
        adj = None
        if adj_list is not None and index < len(adj_list):
            adj = _num(adj_list[index])
        close_out = adj if auto_adjust and adj is not None else close
        bars.append(
            OHLCVBar(
                timestamp=ts,
                open=_num(opens[index]) or close,
                high=_num(highs[index]) or close,
                low=_num(lows[index]) or close,
                close=close_out,
                adj_close=adj,
                volume=_num(volumes[index]) if index < len(volumes) else None,
            )
        )
    if not bars:
        raise SymbolNotFound(symbol, provider="yahoo")
    return History(
        bars=bars,
        provenance=Provenance(
            provider="yahoo",
            delayed=True,
            adjustment="split_and_dividend" if auto_adjust else "none",
            asof=datetime.now(UTC),
            timezone=str(tz),
            currency=currency_s,
        ),
    )


def _adj_closes(indicators: dict[str, object]) -> list[object] | None:
    raw = indicators.get("adjclose")
    if raw is None:
        return None
    rows = require_list(raw, where="yahoo.adjclose")
    if not rows:
        return None
    block = require_dict(rows[0], where="yahoo.adjclose[0]")
    return require_list(block.get("adjclose"), where="adjclose")


def _num(value: object) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None
