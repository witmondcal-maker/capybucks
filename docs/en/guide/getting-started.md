# Getting started

capybucks is a Python library for market data. You call `download()` or
`Ticker`, you get a pandas DataFrame, and you can tell **where the numbers
came from**. That last part is the point.

Common helpers online tend to hide the source, swallow a missing ticker as
an empty frame or a column of `NaN`, and leave you stuck on an unofficial
HTTP endpoint when you later need a licensed feed. capybucks keeps the
one-liner and makes those failure modes explicit.

## Install

```bash
pip install capybucks
```

Optional extras, only when you need them:

| Extra | What it unlocks |
|---|---|
| `[ta]` | Marker only — indicators already run on pandas |
| `[calendars]` | Exchange session calendars (`BVMF` for `.SA`) |
| `[stream]` | Twelve Data WebSocket quotes |
| `[polars]` | Reserved; public frames are pandas today |

```bash
pip install "capybucks[calendars,stream]"
```

From a clone: `uv sync --all-groups` (or `--all-extras`) / `pip install -e .`.
Python 3.11 or newer.

## First call

```python
import capybucks as cb

df = cb.download("AAPL", period="1mo")
df.tail()
```

What you should see:

- A `DatetimeIndex` named `Date`, timezone-aware (usually the exchange tz).
- Columns `Open`, `High`, `Low`, `Close`, `Adj Close`, `Volume`.
- Metadata on the frame, not as extra columns:

```python
df.attrs["provider"]  # e.g. "yahoo"
df.attrs["delayed"]  # True for unofficial / delayed feeds
df.attrs["adjustment"]  # "split_and_dividend" or "none"
df.attrs["asof"]  # when this process fetched the series
df.attrs["currency"]  # e.g. "USD"
```

`delayed=True` is a contract. A delayed quote must not look like a
real-time one. If you plot this next to a paid stream, read that flag.

## Who answered?

Equities such as `AAPL` go to **Yahoo** with no API key. That endpoint is
unofficial and usually delayed (~15 minutes). Crypto such as `BTC-USD`
goes to **CoinGecko**. You can pin another source with `provider=`:

```python
cb.download("AAPL", provider="twelvedata")  # needs a key; see Configuration
```

There is **no silent fallback**. If Yahoo is down, capybucks does not
quietly glue Stooq candles onto the same series. Mixing adjustment methods
and calendars in one frame is a backtest bug that looks like success. Pin
a provider, or wait and retry the same one.

## Missing symbols raise

```python
from capybucks.exceptions import SymbolNotFound

try:
    cb.download("THISISNOTATICKER")
except SymbolNotFound as err:
    print(err.symbol, err.provider)
```

You do not get an empty DataFrame. Catch `CapybucksError` (or a subclass)
instead of testing `df.empty`.

Brazilian cash equities on Yahoo need the `.SA` suffix. `PETR4` raises
`SymbolNotFound` with `err.hint == "PETR4.SA"`. See
[Indicators and calendars](indicators-and-calendars.md) for B3 timezones
and session calendars.

## Jupyter

`download()` is safe to call from a notebook. If an event loop is already
running, capybucks runs the fetch on a worker thread instead of raising
`RuntimeError`. The async API lives in `capybucks.async_api` if you want
to `await` it yourself — see [Async and streaming](async-and-streaming.md).

A walkthrough notebook is at
[examples/getting_started.ipynb](../../../examples/getting_started.ipynb).
Those cells hit the network.

## Data is not the license

The **software** is MIT. The **data** belongs to the provider. Do not
redistribute Yahoo (or any vendor) series as your own feed. Yahoo's terms
restrict automated collection; treat the default path as convenience for
research, not as a commercial entitlement.

Next: [download()](download.md) for periods, batches, and intervals.
