from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest
import respx

import capybucks as cb
from capybucks.core.bootstrap import install_default_providers
from capybucks.core.registry import get_registry, reset_registry
from capybucks.exceptions import ProviderError, SymbolNotFound

FIXTURES = Path(__file__).parent / "fixtures"
START = datetime(2024, 1, 1, tzinfo=UTC)
END = datetime(2024, 1, 10, tzinfo=UTC)


def _market_providers() -> None:
    reset_registry()
    install_default_providers(get_registry())


@respx.mock
def test_yahoo_history_from_fixture() -> None:
    _market_providers()
    payload = json.loads(
        (FIXTURES / "yahoo" / "chart_aapl.json").read_text(encoding="utf-8")
    )
    route = respx.get(url__regex=r".*/v8/finance/chart/AAPL.*").mock(
        return_value=httpx.Response(200, json=payload)
    )
    frame = cb.download("AAPL", start=START, end=END, provider="yahoo")
    assert frame.attrs["provider"] == "yahoo"
    assert frame.attrs["delayed"] is True
    assert len(frame) == 3
    assert float(frame["Close"].iloc[-1]) == 187.5
    cb.download("AAPL", start=START, end=END, provider="yahoo")
    assert route.call_count == 1


@respx.mock
def test_yahoo_missing_symbol() -> None:
    _market_providers()
    respx.get(url__regex=r".*/v8/finance/chart/NOPE.*").mock(
        return_value=httpx.Response(
            200,
            json={"chart": {"result": None, "error": {"code": "Not Found"}}},
        )
    )
    with pytest.raises(SymbolNotFound):
        cb.download("NOPE", start=START, end=END, provider="yahoo")


@respx.mock
def test_stooq_history_from_fixture() -> None:
    _market_providers()
    csv = (FIXTURES / "stooq" / "aapl.csv").read_text(encoding="utf-8")
    respx.get(url__regex=r".*stooq.com/q/d/l/.*").mock(
        return_value=httpx.Response(200, text=csv)
    )
    frame = cb.download("AAPL", start=START, end=END, provider="stooq")
    assert frame.attrs["provider"] == "stooq"
    assert len(frame) == 3


@respx.mock
def test_stooq_bot_check_is_typed_error() -> None:
    _market_providers()
    respx.get(url__regex=r".*stooq.com/q/d/l/.*").mock(
        return_value=httpx.Response(200, text="<!DOCTYPE html><html></html>")
    )
    with pytest.raises(ProviderError, match="bot-check"):
        cb.download("AAPL", start=START, end=END, provider="stooq")


@respx.mock
def test_coingecko_btc() -> None:
    _market_providers()
    payload = json.loads(
        (FIXTURES / "coingecko" / "btc_ohlc.json").read_text(encoding="utf-8")
    )
    respx.get(url__regex=r".*api.coingecko.com/api/v3/coins/bitcoin/ohlc.*").mock(
        return_value=httpx.Response(200, json=payload)
    )
    frame = cb.download("BTC-USD", start=START, end=END)
    assert frame.attrs["provider"] == "coingecko"
    assert len(frame) == 2
