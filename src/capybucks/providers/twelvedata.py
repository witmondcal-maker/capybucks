from __future__ import annotations

import json
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta

from capybucks.core.config import get_api_key
from capybucks.core.http import get_json
from capybucks.core.jsonutil import require_dict, require_list
from capybucks.core.models import (
    AssetType,
    History,
    OHLCVBar,
    Provenance,
    Quote,
    StatementKind,
    StatementTable,
)
from capybucks.core.provider import Provider
from capybucks.exceptions import (
    MissingAPIKey,
    ProviderError,
    RateLimitError,
    StreamingNotSupportedError,
    SymbolNotFound,
)

_BASE = "https://api.twelvedata.com"
_WS = "wss://ws.twelvedata.com/v1/quotes/price"
_INTERVALS = {
    "1m": "1min",
    "5m": "5min",
    "15m": "15min",
    "30m": "30min",
    "1h": "1h",
    "1d": "1day",
    "1wk": "1week",
    "1w": "1week",
    "1mo": "1month",
}
_STATEMENT_PATH = {
    StatementKind.INCOME: "income_statement",
    StatementKind.BALANCE: "balance_sheet",
    StatementKind.CASHFLOW: "cash_flow",
}


class TwelveDataProvider(Provider):
    """Official REST API. Requires CAPYBUCKS_TWELVEDATA_KEY or ~/.capybucks.toml."""

    name = "twelvedata"
    requires_key = True
    supports_stream = True

    def supports(self, asset_type: AssetType) -> bool:
        return asset_type in {AssetType.EQUITY, AssetType.CRYPTO, AssetType.FX}

    def _key(self) -> str:
        key = get_api_key(self.name)
        if not key:
            raise MissingAPIKey(self.name)
        return key

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
            raise ProviderError(f"twelvedata does not support interval {interval!r}")
        finish = end or datetime.now(UTC)
        begin = start or (finish - timedelta(days=30))
        params = {
            "symbol": symbol,
            "interval": mapped,
            "start_date": begin.strftime("%Y-%m-%d"),
            "end_date": finish.strftime("%Y-%m-%d"),
            "apikey": self._key(),
            "format": "JSON",
            "outputsize": "5000",
        }
        payload = await get_json(
            f"{_BASE}/time_series", provider=self.name, params=params
        )
        return _parse_time_series(payload, symbol=symbol, auto_adjust=auto_adjust)

    async def fetch_quote(self, symbol: str) -> Quote:
        payload = await get_json(
            f"{_BASE}/quote",
            provider=self.name,
            params={"symbol": symbol, "apikey": self._key()},
        )
        root = require_dict(payload, where="twelvedata quote")
        _raise_status(root, symbol=symbol)
        price = _num(root.get("close") or root.get("price"))
        if price is None:
            raise SymbolNotFound(symbol, provider=self.name)
        return Quote(
            symbol=symbol.upper(),
            price=price,
            timestamp=datetime.now(UTC),
            currency=_str(root.get("currency")),
            delayed=True,
        )

    async def fetch_statement(
        self,
        symbol: str,
        *,
        kind: StatementKind,
        quarterly: bool = False,
    ) -> StatementTable:
        path = _STATEMENT_PATH[kind]
        payload = await get_json(
            f"{_BASE}/{path}",
            provider=self.name,
            params={
                "symbol": symbol,
                "period": "quarterly" if quarterly else "annual",
                "apikey": self._key(),
            },
        )
        return _parse_statement(payload, kind=kind, quarterly=quarterly, symbol=symbol)

    def stream_quotes(self, symbol: str) -> AsyncIterator[Quote]:
        return _stream_quotes(symbol, api_key=self._key())


def _parse_time_series(payload: object, *, symbol: str, auto_adjust: bool) -> History:
    root = require_dict(payload, where="twelvedata time_series")
    _raise_status(root, symbol=symbol)
    meta = require_dict(root.get("meta"), where="meta")
    values = require_list(root.get("values"), where="values")
    tz_name = _str(meta.get("exchange_timezone")) or "UTC"
    currency = _str(meta.get("currency"))
    bars: list[OHLCVBar] = []
    for raw in values:
        row = require_dict(raw, where="value")
        stamp = _parse_dt(_str(row.get("datetime")))
        close = _num(row.get("close"))
        if stamp is None or close is None:
            continue
        bars.append(
            OHLCVBar(
                timestamp=stamp,
                open=_num(row.get("open")) or close,
                high=_num(row.get("high")) or close,
                low=_num(row.get("low")) or close,
                close=close,
                adj_close=_num(row.get("close")),
                volume=_num(row.get("volume")),
            )
        )
    if not bars:
        raise SymbolNotFound(symbol, provider="twelvedata")
    bars.sort(key=lambda bar: bar.timestamp)
    return History(
        bars=bars,
        provenance=Provenance(
            provider="twelvedata",
            delayed=True,
            adjustment="split_and_dividend" if auto_adjust else "none",
            asof=datetime.now(UTC),
            timezone=tz_name,
            currency=currency,
        ),
    )


def _parse_statement(
    payload: object,
    *,
    kind: StatementKind,
    quarterly: bool,
    symbol: str,
) -> StatementTable:
    root = require_dict(payload, where="twelvedata statement")
    _raise_status(root, symbol=symbol)
    nested: object | None = None
    for key in ("income_statement", "balance_sheet", "cash_flow"):
        if key in root:
            nested = root.get(key)
            break
    rows_raw = require_list(
        nested if nested is not None else [], where="statement rows"
    )
    parsed: list[dict[str, float | None]] = []
    periods: list[str] = []
    items: list[str] = []
    for raw in rows_raw:
        row = require_dict(raw, where="statement row")
        period = _str(row.get("fiscal_date") or row.get("date")) or ""
        periods.append(period)
        numeric: dict[str, float | None] = {}
        for field, value in row.items():
            if field in {"fiscal_date", "date", "currency_symbol"}:
                continue
            number = _num(value)
            if number is not None:
                numeric[field] = number
                if field not in items:
                    items.append(field)
        parsed.append(numeric)
    if not parsed:
        raise SymbolNotFound(symbol, provider="twelvedata")
    by_item = [[row.get(item) for row in parsed] for item in items]
    return StatementTable(
        kind=kind,
        quarterly=quarterly,
        periods=periods,
        items=items,
        values=by_item,
    )


def parse_stream_message(payload: object, *, symbol: str) -> Quote | None:
    """Turn a Twelve Data WS JSON object into a Quote, or None for heartbeats."""
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except json.JSONDecodeError:
            return None
    if not isinstance(payload, dict):
        return None
    event = payload.get("event")
    if event not in {None, "price"}:
        return None
    price = _num(payload.get("price"))
    if price is None:
        return None
    stamp = payload.get("timestamp")
    when = datetime.now(UTC)
    if isinstance(stamp, int | float):
        when = datetime.fromtimestamp(int(stamp), tz=UTC)
    raw_symbol = payload.get("symbol")
    ticker = raw_symbol if isinstance(raw_symbol, str) else symbol
    return Quote(
        symbol=ticker.upper(),
        price=price,
        timestamp=when,
        currency=_str(payload.get("currency")),
        delayed=False,
    )


async def _stream_quotes(symbol: str, *, api_key: str) -> AsyncIterator[Quote]:
    try:
        from websockets.asyncio.client import connect
    except ImportError as exc:
        raise StreamingNotSupportedError("twelvedata") from exc
    url = f"{_WS}?apikey={api_key}"
    async with connect(url) as websocket:
        await websocket.send(
            json.dumps({"action": "subscribe", "params": {"symbols": symbol.upper()}})
        )
        async for raw in websocket:
            text = raw if isinstance(raw, str) else raw.decode("utf-8")
            quote = parse_stream_message(text, symbol=symbol)
            if quote is not None:
                yield quote


def _raise_status(root: dict[str, object], *, symbol: str) -> None:
    status = root.get("status")
    if status == "error" or root.get("code") in {400, 401, 403, 404, 429}:
        message = _str(root.get("message")) or "twelvedata error"
        if "not found" in message.lower() or root.get("code") == 404:
            raise SymbolNotFound(symbol, provider="twelvedata")
        if root.get("code") == 429:
            raise RateLimitError(message)
        if root.get("code") in {401, 403}:
            raise MissingAPIKey("twelvedata")
        raise ProviderError(message)


def _num(value: object) -> float | None:
    if value is None or value == "":
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


def _str(value: object) -> str | None:
    return value if isinstance(value, str) else None


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            parsed = datetime.strptime(value, fmt)
            return parsed.replace(tzinfo=UTC)
        except ValueError:
            continue
    return None
