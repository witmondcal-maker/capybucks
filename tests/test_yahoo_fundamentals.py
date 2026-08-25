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

FIXTURES = Path(__file__).parent / "fixtures" / "yahoo"
START = datetime(2024, 1, 1, tzinfo=UTC)
END = datetime(2024, 1, 10, tzinfo=UTC)


def _yahoo() -> None:
    reset_registry()
    install_default_providers(get_registry())


@respx.mock
def test_yahoo_financials() -> None:
    _yahoo()
    payload = json.loads((FIXTURES / "income_aapl.json").read_text(encoding="utf-8"))
    respx.get(url__regex=r".*/v10/finance/quoteSummary/AAPL.*").mock(
        return_value=httpx.Response(200, json=payload)
    )
    frame = cb.Ticker("AAPL", provider="yahoo").financials
    assert "totalRevenue" in frame.index
    assert float(frame.loc["netIncome"].iloc[0]) == 96995000000.0


@respx.mock
def test_yahoo_options_and_chain() -> None:
    _yahoo()
    payload = json.loads((FIXTURES / "options_aapl.json").read_text(encoding="utf-8"))
    respx.get(url__regex=r".*/v7/finance/options/AAPL.*").mock(
        return_value=httpx.Response(200, json=payload)
    )
    ticker = cb.Ticker("AAPL", provider="yahoo")
    assert ticker.options[0] == "2024-01-19"
    chain = ticker.option_chain("2024-01-19")
    assert chain.calls.iloc[0]["contractSymbol"] == "AAPL240119C00100000"
    assert not chain.puts.iloc[0]["inTheMoney"]


@respx.mock
def test_yahoo_news() -> None:
    _yahoo()
    payload = json.loads((FIXTURES / "news_aapl.json").read_text(encoding="utf-8"))
    respx.get(url__regex=r".*/v1/finance/search.*").mock(
        return_value=httpx.Response(200, json=payload)
    )
    news = cb.Ticker("AAPL", provider="yahoo").news
    assert news.iloc[0]["title"] == "Apple reports earnings"


@respx.mock
def test_yahoo_actions() -> None:
    _yahoo()
    payload = json.loads((FIXTURES / "events_aapl.json").read_text(encoding="utf-8"))
    respx.get(url__regex=r".*/v8/finance/chart/AAPL.*").mock(
        return_value=httpx.Response(200, json=payload)
    )
    ticker = cb.Ticker("AAPL", provider="yahoo")
    assert float(ticker.dividends.iloc[0]) == pytest.approx(0.24)
    assert float(ticker.splits.iloc[0]) == pytest.approx(4.0)


@respx.mock
def test_b3_timezone_from_yahoo() -> None:
    _yahoo()
    payload = json.loads((FIXTURES / "chart_petr4.json").read_text(encoding="utf-8"))
    respx.get(url__regex=r".*/v8/finance/chart/PETR4\.SA.*").mock(
        return_value=httpx.Response(200, json=payload)
    )
    frame = cb.download("PETR4.SA", start=START, end=END, provider="yahoo")
    assert "Sao_Paulo" in str(frame.index.tz)
    assert frame.attrs["currency"] == "BRL"
