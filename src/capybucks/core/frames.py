from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal, NamedTuple

import pandas as pd

from capybucks.core.models import (
    ActionEvent,
    History,
    NewsItem,
    OptionChain,
    OptionContract,
    StatementTable,
)

OHLCV_COLUMNS = ("Open", "High", "Low", "Close", "Adj Close", "Volume")

FrameKind = Literal["pandas", "polars"]


def history_to_pandas(history: History) -> pd.DataFrame:
    """Convert a validated series to an OHLCV DataFrame."""
    index = pd.DatetimeIndex(
        [bar.timestamp for bar in history.bars],
        name="Date",
    )
    tz = history.provenance.timezone
    if index.tz is None:
        index = index.tz_localize(tz)
    elif str(index.tz) != tz:
        index = index.tz_convert(tz)

    adj = [
        bar.close if bar.adj_close is None else bar.adj_close for bar in history.bars
    ]
    volumes = [0.0 if bar.volume is None else bar.volume for bar in history.bars]
    frame = pd.DataFrame(
        {
            "Open": [bar.open for bar in history.bars],
            "High": [bar.high for bar in history.bars],
            "Low": [bar.low for bar in history.bars],
            "Close": [bar.close for bar in history.bars],
            "Adj Close": adj,
            "Volume": volumes,
        },
        index=index,
    )
    _apply_provenance(frame, history)
    return frame


def _apply_provenance(frame: pd.DataFrame, history: History) -> None:
    provenance = history.provenance
    asof = provenance.asof or datetime.now(UTC)
    frame.attrs["provider"] = provenance.provider
    frame.attrs["delayed"] = provenance.delayed
    frame.attrs["adjustment"] = provenance.adjustment
    frame.attrs["asof"] = asof
    frame.attrs["currency"] = provenance.currency
    frame.attrs.setdefault("errors", {})


class OptionChainFrames(NamedTuple):
    """`option_chain` result: calls and puts as DataFrames."""

    calls: pd.DataFrame
    puts: pd.DataFrame


_OPTION_COLUMNS = (
    "contractSymbol",
    "strike",
    "lastPrice",
    "bid",
    "ask",
    "volume",
    "openInterest",
    "impliedVolatility",
    "inTheMoney",
    "expiration",
)


def statement_to_pandas(table: StatementTable) -> pd.DataFrame:
    """Line items as the index, period-end dates as columns."""
    columns = pd.to_datetime(table.periods, errors="coerce")
    return pd.DataFrame(table.values, index=table.items, columns=columns)


def option_chain_to_frames(chain: OptionChain) -> OptionChainFrames:
    return OptionChainFrames(
        calls=_contracts_frame(chain.calls),
        puts=_contracts_frame(chain.puts),
    )


def _contracts_frame(contracts: list[OptionContract]) -> pd.DataFrame:
    if not contracts:
        return pd.DataFrame(columns=list(_OPTION_COLUMNS))
    rows = [
        {
            "contractSymbol": contract.contract_symbol,
            "strike": contract.strike,
            "lastPrice": contract.last_price,
            "bid": contract.bid,
            "ask": contract.ask,
            "volume": contract.volume,
            "openInterest": contract.open_interest,
            "impliedVolatility": contract.implied_volatility,
            "inTheMoney": contract.in_the_money,
            "expiration": contract.expiration,
        }
        for contract in contracts
    ]
    return pd.DataFrame(rows, columns=list(_OPTION_COLUMNS))


def news_to_frame(items: list[NewsItem]) -> pd.DataFrame:
    if not items:
        return pd.DataFrame(columns=["title", "publisher", "link", "published_at"])
    return pd.DataFrame(
        [
            {
                "title": item.title,
                "publisher": item.publisher,
                "link": item.link,
                "published_at": item.published_at,
            }
            for item in items
        ]
    )


def actions_to_frame(events: list[ActionEvent]) -> pd.DataFrame:
    """One row per timestamp with Dividends and Stock Splits columns."""
    empty = pd.DataFrame(columns=["Dividends", "Stock Splits"])
    if not events:
        return empty
    by_ts: dict[datetime, dict[str, float]] = {}
    for event in events:
        row = by_ts.setdefault(event.timestamp, {"Dividends": 0.0, "Stock Splits": 0.0})
        if event.kind == "dividend":
            row["Dividends"] = event.value
        elif event.kind == "split":
            row["Stock Splits"] = event.value
    index = pd.DatetimeIndex(list(by_ts.keys()), name="Date")
    return pd.DataFrame(list(by_ts.values()), index=index).sort_index()
