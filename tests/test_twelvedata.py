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
from capybucks.exceptions import MissingAPIKey, NoProviderError
from capybucks.providers.twelvedata import parse_stream_message

FIXTURES = Path(__file__).parent / "fixtures" / "twelvedata"
START = datetime(2024, 1, 1, tzinfo=UTC)
END = datetime(2024, 1, 10, tzinfo=UTC)


def _market(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CAPYBUCKS_TWELVEDATA_KEY", "test-key")
    reset_registry()
    install_default_providers(get_registry())


@respx.mock
def test_twelvedata_history(monkeypatch: pytest.MonkeyPatch) -> None:
    _market(monkeypatch)
    payload = json.loads(
        (FIXTURES / "time_series_aapl.json").read_text(encoding="utf-8")
    )
    respx.get(url__regex=r".*api.twelvedata.com/time_series.*").mock(
        return_value=httpx.Response(200, json=payload)
    )
    frame = cb.download("AAPL", start=START, end=END, provider="twelvedata")
    assert frame.attrs["provider"] == "twelvedata"
    assert len(frame) == 3
    assert float(frame["Close"].iloc[-1]) == 185.5


@respx.mock
def test_twelvedata_financials(monkeypatch: pytest.MonkeyPatch) -> None:
    _market(monkeypatch)
    payload = json.loads((FIXTURES / "income_aapl.json").read_text(encoding="utf-8"))
    respx.get(url__regex=r".*api.twelvedata.com/income_statement.*").mock(
        return_value=httpx.Response(200, json=payload)
    )
    frame = cb.Ticker("AAPL", provider="twelvedata").financials
    assert "revenue" in frame.index
    assert float(frame.loc["net_income"].iloc[0]) == 96995000000.0


@respx.mock
def test_twelvedata_invalid_key(monkeypatch: pytest.MonkeyPatch) -> None:
    _market(monkeypatch)
    payload = json.loads((FIXTURES / "error_key.json").read_text(encoding="utf-8"))
    respx.get(url__regex=r".*api.twelvedata.com/time_series.*").mock(
        return_value=httpx.Response(200, json=payload)
    )
    with pytest.raises(MissingAPIKey):
        cb.download("AAPL", start=START, end=END, provider="twelvedata")


def test_fx_requires_explicit_provider() -> None:
    with pytest.raises(NoProviderError):
        cb.download("EUR/USD")


def test_stream_message_skips_heartbeat() -> None:
    assert parse_stream_message({"event": "heartbeat"}, symbol="AAPL") is None
    quote = parse_stream_message(
        {"event": "price", "symbol": "AAPL", "price": 185.5, "timestamp": 1704672000},
        symbol="AAPL",
    )
    assert quote is not None
    assert quote.price == 185.5
    assert quote.delayed is False
