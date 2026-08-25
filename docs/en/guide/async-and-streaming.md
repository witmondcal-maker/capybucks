# Async and streaming

## Why two APIs

`async_api/` is the source of truth (HTTP, cache, retry). `capybucks.download`
and `capybucks.Ticker` are thin sync wrappers. They call `run_sync`, which
uses `asyncio.run` when no loop is running, or a **worker thread** when
Jupyter already has a loop. That is why `download()` does not raise
`RuntimeError: This event loop is already running`.

Do not duplicate business logic in `sync/`. If you are writing a provider,
implement the async methods only.

## Awaiting downloads

```python
from capybucks.async_api import download, AsyncTicker

df = await download("AAPL", period="5d")
hist = await AsyncTicker("AAPL").history(period="5d")
inc = await AsyncTicker("AAPL").financials()
```

On `AsyncTicker`, financials/news/options are **async methods**, not
properties (`await ticker.financials()`). The sync `Ticker` exposes the
same names as properties for notebook convenience.

`await download(["AAPL", "MSFT"])` fetches concurrently with
`asyncio.gather`. One dead ticker does not cancel the others.

## Streaming quotes

Only Twelve Data declares `supports_stream = True`. Yahoo, Stooq, and
CoinGecko raise `StreamingNotSupportedError`.

Install the extra, set the key, pin the provider:

```bash
pip install "capybucks[stream]"
```

```python
from capybucks.async_api import AsyncTicker

ticker = AsyncTicker("AAPL", provider="twelvedata")
async for quote in ticker.stream():
    print(quote.symbol, quote.price, quote.timestamp, quote.delayed)
    break
```

`Quote.delayed` is `False` on websocket prints (they are live as far as
this client can tell). REST history from the same vendor remains
`delayed=True` on the DataFrame. Do not mix them in one series without
noticing.

Heartbeats and non-price events are skipped. Missing `[stream]`
(`websockets`) raises `StreamingNotSupportedError`. Missing key raises
`MissingAPIKey` before connecting.

The sync `Ticker` has **no** `stream()` method. Streaming is async-only.

## Configure cache from async code

```python
from pathlib import Path
from capybucks.async_api import configure_cache

configure_cache(Path("./.cache/capybucks"))
```

Same helper the tests use. See [Cache and provenance](cache-and-provenance.md).
