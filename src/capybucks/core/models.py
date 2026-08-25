from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class AssetType(StrEnum):
    EQUITY = "equity"
    CRYPTO = "crypto"
    FX = "fx"
    BOND = "bond"


class OHLCVBar(BaseModel):
    """One candle after provider-side validation. Internal, not the public API."""

    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    adj_close: float | None = None
    volume: float | None = None


class Provenance(BaseModel):
    provider: str
    delayed: bool = True
    adjustment: str = "split_and_dividend"
    asof: datetime | None = None
    timezone: str = "UTC"
    currency: str | None = "USD"
    covered_from: datetime | None = None
    covered_to: datetime | None = None


class History(BaseModel):
    bars: list[OHLCVBar] = Field(default_factory=list)
    provenance: Provenance


class Quote(BaseModel):
    symbol: str
    price: float
    timestamp: datetime
    currency: str | None = None
    delayed: bool = True


class Instrument(BaseModel):
    symbol: str
    asset_type: AssetType
    name: str | None = None
    currency: str | None = None
    exchange: str | None = None


class StatementKind(StrEnum):
    INCOME = "income"
    BALANCE = "balance"
    CASHFLOW = "cashflow"


class StatementTable(BaseModel):
    """Line items × period-end dates. Converted to a DataFrame at the Ticker."""

    kind: StatementKind
    quarterly: bool
    periods: list[str]
    items: list[str]
    values: list[list[float | None]]


class OptionContract(BaseModel):
    contract_symbol: str
    strike: float
    last_price: float | None = None
    bid: float | None = None
    ask: float | None = None
    volume: float | None = None
    open_interest: float | None = None
    implied_volatility: float | None = None
    in_the_money: bool | None = None
    expiration: str


class OptionChain(BaseModel):
    expiration: str
    calls: list[OptionContract]
    puts: list[OptionContract]


class NewsItem(BaseModel):
    title: str
    publisher: str | None = None
    link: str | None = None
    published_at: datetime | None = None


class ActionEvent(BaseModel):
    timestamp: datetime
    kind: str
    value: float
