from __future__ import annotations

from datetime import UTC, datetime

from capybucks.core.http import get_json
from capybucks.core.jsonutil import require_dict, require_list
from capybucks.core.models import (
    ActionEvent,
    NewsItem,
    OptionChain,
    OptionContract,
    StatementKind,
    StatementTable,
)
from capybucks.exceptions import ProviderError, SymbolNotFound

_SUMMARY = "https://query1.finance.yahoo.com/v10/finance/quoteSummary/{symbol}"
_OPTIONS = "https://query1.finance.yahoo.com/v7/finance/options/{symbol}"
_SEARCH = "https://query1.finance.yahoo.com/v1/finance/search"
_CHART = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"

_MODULES: dict[tuple[StatementKind, bool], str] = {
    (StatementKind.INCOME, False): "incomeStatementHistory",
    (StatementKind.INCOME, True): "incomeStatementHistoryQuarterly",
    (StatementKind.BALANCE, False): "balanceSheetHistory",
    (StatementKind.BALANCE, True): "balanceSheetHistoryQuarterly",
    (StatementKind.CASHFLOW, False): "cashflowStatementHistory",
    (StatementKind.CASHFLOW, True): "cashflowStatementHistoryQuarterly",
}

_LIST_KEYS = {
    StatementKind.INCOME: "incomeStatementHistory",
    StatementKind.BALANCE: "balanceSheetStatements",
    StatementKind.CASHFLOW: "cashflowStatements",
}


async def fetch_yahoo_statement(
    symbol: str, *, kind: StatementKind, quarterly: bool
) -> StatementTable:
    module = _MODULES[(kind, quarterly)]
    payload = await get_json(
        _SUMMARY.format(symbol=symbol),
        provider="yahoo",
        params={"modules": module},
    )
    block = _quote_summary_module(payload, module=module, symbol=symbol)
    rows = _statement_rows(block, kind=kind)
    if not rows:
        raise SymbolNotFound(symbol, provider="yahoo")
    items: list[str] = []
    for row in rows:
        for key in row:
            if key not in items and key != "endDate":
                items.append(key)
    periods: list[str] = []
    for row in rows:
        end = row.get("endDate")
        periods.append(end if isinstance(end, str) else "")
    values: list[list[float | None]] = []
    for item in items:
        values.append([_as_float(row.get(item)) for row in rows])
    return StatementTable(
        kind=kind,
        quarterly=quarterly,
        periods=periods,
        items=items,
        values=values,
    )


async def fetch_yahoo_expirations(symbol: str) -> list[str]:
    payload = await get_json(_OPTIONS.format(symbol=symbol), provider="yahoo")
    result = _option_result(payload, symbol=symbol)
    raw_dates = require_list(result.get("expirationDates"), where="expirationDates")
    out: list[str] = []
    for item in raw_dates:
        if isinstance(item, int | float):
            out.append(datetime.fromtimestamp(int(item), tz=UTC).date().isoformat())
    return out


async def fetch_yahoo_chain(symbol: str, *, expiration: str) -> OptionChain:
    day = datetime.fromisoformat(expiration).replace(tzinfo=UTC)
    payload = await get_json(
        _OPTIONS.format(symbol=symbol),
        provider="yahoo",
        params={"date": str(int(day.timestamp()))},
    )
    result = _option_result(payload, symbol=symbol)
    options = require_list(result.get("options"), where="options")
    if not options:
        raise SymbolNotFound(symbol, provider="yahoo")
    block = require_dict(options[0], where="options[0]")
    calls = [
        _contract(item, expiration)
        for item in require_list(block.get("calls"), where="calls")
    ]
    puts = [
        _contract(item, expiration)
        for item in require_list(block.get("puts"), where="puts")
    ]
    return OptionChain(expiration=expiration, calls=calls, puts=puts)


async def fetch_yahoo_news(symbol: str) -> list[NewsItem]:
    payload = await get_json(
        _SEARCH,
        provider="yahoo",
        params={"q": symbol, "quotesCount": "0", "newsCount": "10"},
    )
    root = require_dict(payload, where="search")
    news = require_list(root.get("news"), where="news")
    items: list[NewsItem] = []
    for raw in news:
        row = require_dict(raw, where="news item")
        title = row.get("title")
        if not isinstance(title, str):
            continue
        published = row.get("providerPublishTime")
        published_at = None
        if isinstance(published, int | float):
            published_at = datetime.fromtimestamp(int(published), tz=UTC)
        publisher = row.get("publisher")
        link = row.get("link")
        items.append(
            NewsItem(
                title=title,
                publisher=publisher if isinstance(publisher, str) else None,
                link=link if isinstance(link, str) else None,
                published_at=published_at,
            )
        )
    return items


async def fetch_yahoo_actions(symbol: str) -> list[ActionEvent]:
    payload = await get_json(
        _CHART.format(symbol=symbol),
        provider="yahoo",
        params={
            "interval": "1d",
            "range": "max",
            "events": "div|split",
        },
    )
    root = require_dict(payload, where="yahoo")
    chart = require_dict(root.get("chart"), where="chart")
    results = chart.get("result")
    if results is None:
        raise SymbolNotFound(symbol, provider="yahoo")
    rows = require_list(results, where="result")
    if not rows:
        raise SymbolNotFound(symbol, provider="yahoo")
    result = require_dict(rows[0], where="result[0]")
    events = result.get("events")
    if events is None:
        return []
    block = require_dict(events, where="events")
    out: list[ActionEvent] = []
    dividends = block.get("dividends")
    if isinstance(dividends, dict):
        for raw in dividends.values():
            item = require_dict(raw, where="dividend")
            ts = item.get("date")
            amount = item.get("amount")
            if isinstance(ts, int | float) and isinstance(amount, int | float):
                out.append(
                    ActionEvent(
                        timestamp=datetime.fromtimestamp(int(ts), tz=UTC),
                        kind="dividend",
                        value=float(amount),
                    )
                )
    splits = block.get("splits")
    if isinstance(splits, dict):
        for raw in splits.values():
            item = require_dict(raw, where="split")
            ts = item.get("date")
            num = item.get("numerator")
            den = item.get("denominator")
            if (
                isinstance(ts, int | float)
                and isinstance(num, int | float)
                and isinstance(den, int | float)
                and den != 0
            ):
                out.append(
                    ActionEvent(
                        timestamp=datetime.fromtimestamp(int(ts), tz=UTC),
                        kind="split",
                        value=float(num) / float(den),
                    )
                )
    out.sort(key=lambda event: event.timestamp)
    return out


def _quote_summary_module(
    payload: object, *, module: str, symbol: str
) -> dict[str, object]:
    root = require_dict(payload, where="quoteSummary")
    wrapper = require_dict(root.get("quoteSummary"), where="quoteSummary")
    if wrapper.get("error"):
        raise SymbolNotFound(symbol, provider="yahoo")
    results = wrapper.get("result")
    if results is None:
        raise SymbolNotFound(symbol, provider="yahoo")
    rows = require_list(results, where="result")
    if not rows:
        raise SymbolNotFound(symbol, provider="yahoo")
    first = require_dict(rows[0], where="result[0]")
    block = first.get(module)
    if block is None:
        raise ProviderError(f"yahoo quoteSummary missing module {module}")
    return require_dict(block, where=module)


def _statement_rows(
    block: dict[str, object], *, kind: StatementKind
) -> list[dict[str, str | float | None]]:
    key = _LIST_KEYS[kind]
    raw_list = block.get(key)
    if raw_list is None:
        # incomeStatementHistory nests the list under the same name
        raw_list = block.get("incomeStatementHistory")
    if raw_list is None:
        return []
    rows_out: list[dict[str, str | float | None]] = []
    for raw in require_list(raw_list, where=key):
        row = require_dict(raw, where="statement row")
        parsed: dict[str, str | float | None] = {}
        end = row.get("endDate")
        parsed["endDate"] = _end_date(end)
        for field, value in row.items():
            if field in {"maxAge", "endDate"}:
                continue
            parsed[field] = _raw_number(value)
        rows_out.append(parsed)
    return rows_out


def _end_date(value: object) -> str:
    if isinstance(value, dict):
        fmt = value.get("fmt")
        if isinstance(fmt, str):
            return fmt
        raw = value.get("raw")
        if isinstance(raw, int | float):
            return datetime.fromtimestamp(int(raw), tz=UTC).date().isoformat()
    return ""


def _raw_number(value: object) -> float | None:
    if isinstance(value, dict):
        raw = value.get("raw")
        if isinstance(raw, int | float) and not isinstance(raw, bool):
            return float(raw)
        return None
    if isinstance(value, int | float) and not isinstance(value, bool):
        return float(value)
    return None


def _as_float(value: str | float | None) -> float | None:
    if isinstance(value, int | float) and not isinstance(value, bool):
        return float(value)
    return None


def _option_result(payload: object, *, symbol: str) -> dict[str, object]:
    root = require_dict(payload, where="optionChain")
    chain = require_dict(root.get("optionChain"), where="optionChain")
    if chain.get("error"):
        raise SymbolNotFound(symbol, provider="yahoo")
    results = chain.get("result")
    if results is None:
        raise SymbolNotFound(symbol, provider="yahoo")
    rows = require_list(results, where="optionChain.result")
    if not rows:
        raise SymbolNotFound(symbol, provider="yahoo")
    return require_dict(rows[0], where="optionChain.result[0]")


def _contract(raw: object, expiration: str) -> OptionContract:
    row = require_dict(raw, where="contract")
    symbol = row.get("contractSymbol")
    strike = row.get("strike")
    if not isinstance(symbol, str) or not isinstance(strike, int | float):
        raise ProviderError("yahoo option contract missing symbol/strike")
    in_the_money_raw = row.get("inTheMoney")
    return OptionContract(
        contract_symbol=symbol,
        strike=float(strike),
        last_price=_opt_float(row.get("lastPrice")),
        bid=_opt_float(row.get("bid")),
        ask=_opt_float(row.get("ask")),
        volume=_opt_float(row.get("volume")),
        open_interest=_opt_float(row.get("openInterest")),
        implied_volatility=_opt_float(row.get("impliedVolatility")),
        in_the_money=in_the_money_raw if isinstance(in_the_money_raw, bool) else None,
        expiration=expiration,
    )


def _opt_float(value: object) -> float | None:
    if isinstance(value, int | float) and not isinstance(value, bool):
        return float(value)
    return None
