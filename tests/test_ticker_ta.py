from __future__ import annotations

import pandas as pd
import pytest

import capybucks as cb
from capybucks.ta import bollinger, ema, enrich, macd, rsi, sma, vwap


def test_ticker_financials_from_memory() -> None:
    ticker = cb.Ticker("AAPL")
    frame = ticker.financials
    assert list(frame.index) == ["Total Revenue", "Net Income"]
    assert float(frame.loc["Total Revenue"].iloc[0]) == 100.0
    quarterly = ticker.quarterly_financials
    assert quarterly.shape == frame.shape


def test_ticker_options_news_actions() -> None:
    ticker = cb.Ticker("AAPL")
    assert ticker.options == ("2024-01-19", "2024-02-16")
    chain = ticker.option_chain()
    assert not chain.calls.empty
    assert not chain.puts.empty
    news = ticker.news
    assert "test headline" in str(news.iloc[0]["title"])
    assert float(ticker.dividends.iloc[0]) == pytest.approx(0.24)
    assert float(ticker.splits.iloc[0]) == pytest.approx(4.0)
    quote = ticker.quote()
    assert quote.price == 100.0


def test_sma_and_enrich() -> None:
    close = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
    out = sma(close, window=3)
    assert pd.isna(out.iloc[1])
    assert float(out.iloc[2]) == pytest.approx(2.0)
    assert float(ema(close, window=3).iloc[-1]) > 0
    history = cb.download("AAPL", period="5d")
    rich = enrich(history, window=3)
    assert "RSI" in rich.columns
    assert "VWAP" in rich.columns
    assert "BB Upper" in rich.columns
    rsi(history["Close"])
    macd(history["Close"])
    bollinger(history["Close"], window=3)
    vwap(history["High"], history["Low"], history["Close"], history["Volume"])
