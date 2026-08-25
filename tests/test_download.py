from __future__ import annotations

import pandas as pd
import pytest

import capybucks as cb
from capybucks.core.frames import OHLCV_COLUMNS
from capybucks.core.registry import reset_registry
from capybucks.exceptions import MultiDownloadError, NoProviderError, SymbolNotFound


def test_download_single_ticker_ohlcv_columns() -> None:
    frame = cb.download("AAPL", period="5d")
    assert list(frame.columns) == list(OHLCV_COLUMNS)
    assert isinstance(frame.index, pd.DatetimeIndex)
    assert frame.index.tz is not None
    assert frame.attrs["provider"] == "memory"
    assert frame.attrs["delayed"] is False
    assert "currency" in frame.attrs
    assert not frame.empty


def test_ticker_history_matches_download() -> None:
    direct = cb.download("MSFT", period="5d")
    via_ticker = cb.Ticker("MSFT").history(period="5d")
    assert list(direct.columns) == list(via_ticker.columns)
    assert direct.attrs["provider"] == via_ticker.attrs["provider"]
    pd.testing.assert_series_equal(direct["Close"], via_ticker["Close"])


def test_unknown_symbol_raises() -> None:
    with pytest.raises(SymbolNotFound) as caught:
        cb.download("NOPE")
    assert caught.value.symbol == "NOPE"
    assert caught.value.provider == "memory"


def test_multi_ticker_partial_success() -> None:
    frame = cb.download(["AAPL", "NOPE", "MSFT"])
    tickers = set(frame.columns.get_level_values(0))
    assert tickers == {"AAPL", "MSFT"}
    assert "NOPE" in frame.attrs["errors"]


def test_multi_ticker_all_missing() -> None:
    with pytest.raises(MultiDownloadError) as caught:
        cb.download(["NOPE", "ALSO"])
    assert "NOPE" in caught.value.errors
    assert "ALSO" in caught.value.errors


def test_no_provider_registered() -> None:
    reset_registry()
    with pytest.raises(NoProviderError):
        cb.download("AAPL")


def test_explicit_unknown_provider() -> None:
    with pytest.raises(cb.ProviderNotFound):
        cb.download("AAPL", provider="not-a-provider")
