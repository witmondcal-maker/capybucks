# Indicators and calendars

## Technical indicators (`capybucks.ta`)

Functions are **vectorized pandas** over OHLCV columns. They do not
download data. You pass `Close` (and `High`/`Low`/`Volume` where needed).

The `[ta]` extra is a marker; pandas is already a hard dependency.
`pip install capybucks[ta]` is optional documentation of intent.

```python
import capybucks as cb
from capybucks.ta import rsi, sma, ema, macd, bollinger, atr, vwap, enrich

df = cb.download("AAPL", period="6mo")
rsi(df["Close"]).tail()
enrich(df, window=20).tail()
```

| Function | Inputs | Notes |
|---|---|---|
| `sma` / `ema` | close, `window=20` | EMA uses `span=window`, `adjust=False` |
| `rsi` | close, `window=14` | Wilder smoothing (`alpha=1/window`) |
| `macd` | close, `fast=12`, `slow=26`, `signal=9` | DataFrame `macd`, `signal`, `histogram` |
| `bollinger` | close, `window=20`, `num_std=2` | `mid`, `upper`, `lower` |
| `atr` | high, low, close, `window=14` | True range, Wilder mean |
| `vwap` | high, low, close, volume | Cumulative typical price × volume |
| `enrich` | full OHLCV frame | Adds SMA, EMA, RSI, MACD, BB, ATR, VWAP columns |

These are textbook formulas, not a trading system. Windows are
parameters, not advice.

## B3 (Brazil)

Yahoo lists Brazilian cash equities as `{ticker}.SA` (Petrobras ON →
`PETR4.SA`). A bare `PETR4` raises `SymbolNotFound` with
`hint="PETR4.SA"`. We do not rewrite the symbol for you.

Chart timezones come from the provider. Yahoo's B3 meta is
`America/Sao_Paulo`, so the DatetimeIndex is that zone when the payload
says so. If timezone is missing and the symbol ends in `.SA`, Yahoo
parsing falls back to `America/Sao_Paulo`.

Currency on that series is typically `BRL`.

```python
import capybucks as cb

df = cb.download("PETR4.SA", period="1mo")
df.index.tz  # America/Sao_Paulo
df.attrs["currency"]
```

## Session calendars (`capybucks[calendars]`)

Install `exchange-calendars` via the extra:

```bash
pip install "capybucks[calendars]"
```

```python
from datetime import datetime, timezone
from capybucks.calendars import calendar_for_symbol, is_session

calendar_for_symbol("PETR4.SA")  # "BVMF" (B3)
calendar_for_symbol("AAPL")  # "XNYS"
calendar_for_symbol("VOD.L")  # "XLON"

is_session(datetime(2024, 1, 8, 17, tzinfo=timezone.utc), symbol="AAPL")
```

`is_session` converts tz-aware timestamps into the calendar's zone before
asking “is this a trading day?”. Naive datetimes are treated as calendar
dates.

Without the extra, `get_calendar` / `is_session` raise `ImportError` with
the install hint.
