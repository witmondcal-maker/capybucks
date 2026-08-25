"""Vectorized indicators over pandas OHLCV columns.

Install extra is a no-op marker (`pip install capybucks[ta]`); pandas is already
a hard dependency. Functions take Series, not DataFrames, so they compose.
"""

from __future__ import annotations

import pandas as pd


def sma(close: pd.Series, window: int = 20) -> pd.Series:
    """Simple moving average of ``close``."""
    return close.rolling(window=window, min_periods=window).mean()


def ema(close: pd.Series, window: int = 20) -> pd.Series:
    """Exponential moving average (``span=window``, ``adjust=False``)."""
    return close.ewm(span=window, adjust=False).mean()


def rsi(close: pd.Series, window: int = 14) -> pd.Series:
    """Relative strength index with Wilder smoothing."""
    delta = close.diff()
    gain = delta.clip(lower=0.0)
    loss = (-delta).clip(lower=0.0)
    avg_gain = gain.ewm(alpha=1 / window, min_periods=window, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / window, min_periods=window, adjust=False).mean()
    rs = avg_gain / avg_loss.where(avg_loss != 0.0)
    return 100.0 - (100.0 / (1.0 + rs))


def macd(
    close: pd.Series,
    *,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> pd.DataFrame:
    """MACD line, signal line, and histogram."""
    macd_line = ema(close, fast) - ema(close, slow)
    signal_line = ema(macd_line, signal)
    return pd.DataFrame(
        {
            "macd": macd_line,
            "signal": signal_line,
            "histogram": macd_line - signal_line,
        }
    )


def bollinger(
    close: pd.Series, *, window: int = 20, num_std: float = 2.0
) -> pd.DataFrame:
    """Bollinger mid, upper, and lower bands."""
    mid = sma(close, window)
    std = close.rolling(window=window, min_periods=window).std()
    width = std * num_std
    return pd.DataFrame(
        {
            "mid": mid,
            "upper": mid + width,
            "lower": mid - width,
        }
    )


def atr(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    *,
    window: int = 14,
) -> pd.Series:
    """Average true range with Wilder smoothing."""
    prev_close = close.shift(1)
    tr = pd.concat(
        [
            high - low,
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return tr.ewm(alpha=1 / window, min_periods=window, adjust=False).mean()


def vwap(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    volume: pd.Series,
) -> pd.Series:
    """Volume-weighted average price from typical price."""
    typical = (high + low + close) / 3.0
    cum_vol = volume.cumsum()
    return (typical * volume).cumsum() / cum_vol.where(cum_vol != 0.0)


def enrich(frame: pd.DataFrame, *, window: int = 20) -> pd.DataFrame:
    """Add SMA/EMA/RSI/MACD/BB/ATR/VWAP columns to an OHLCV frame."""
    out = frame.copy()
    close = out["Close"]
    out["SMA"] = sma(close, window)
    out["EMA"] = ema(close, window)
    out["RSI"] = rsi(close)
    macd_frame = macd(close)
    out["MACD"] = macd_frame["macd"]
    out["MACD Signal"] = macd_frame["signal"]
    bands = bollinger(close, window=window)
    out["BB Mid"] = bands["mid"]
    out["BB Upper"] = bands["upper"]
    out["BB Lower"] = bands["lower"]
    out["ATR"] = atr(out["High"], out["Low"], close)
    out["VWAP"] = vwap(out["High"], out["Low"], close, out["Volume"])
    return out
