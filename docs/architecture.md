# Architecture overview

Four layers, top to bottom. User-facing guides are the Guide section of
the HTML docs (`en/guide/` and `pt/guide/`). This page is the contributor
map. If it drifts from the code, trust the code and fix this doc.

```
src/capybucks/
  sync/         public blocking API — thin wrapper over async_api/
  async_api/    public async API — source of truth
  core/         pydantic bars, cache, retry, registry, pandas conversion
  providers/    one module per source (yahoo, stooq, coingecko, twelvedata, memory)
```

## Data flow

`download()` / `Ticker.history()` → registry resolves **one** provider
(explicit `provider=` or a deterministic default for that asset + interval)
→ provider fetches and validates into `OHLCVBar` + `Provenance` → optional
cache/retry on that same provider → pandas DataFrame with OHLCV columns
and provenance in `df.attrs`.

Fallback across providers is **opt-in** (ADR 0004). It never concatenates
candles from two sources in one series.

## Public vs internal models

Internally, every bar is Pydantic so a renamed JSON field fails at the
provider boundary. Users receive pandas (and optionally Polars). Snapshots
such as `Quote` may stay Pydantic. See ADR 0003 and ADR 0005.

## Providers (shipped)

| Asset class | Default | Pin |
|---|---|---|
| Equities (all intervals) | Yahoo | `provider="stooq"` (daily CSV) or `"twelvedata"` (key) |
| Crypto | CoinGecko | `provider="twelvedata"` |
| FX | none (pin required) | `provider="twelvedata"` (`EUR/USD`) |
| Tests | `MemoryProvider` | `provider="memory"` |

Yahoo is the zero-config default because Stooq currently returns a JS
bot-check to many non-browser clients. Pin Stooq when the CSV endpoint is
reachable. Do not stitch Yahoo and Stooq into one series. Twelve Data
never becomes the silent default — missing keys raise `MissingAPIKey`.

B3 symbols use the Yahoo suffix (`.SA`). A bare ticker like `PETR4`
raises `SymbolNotFound` with a `.SA` hint. Chart timezones come from the
provider (`America/Sao_Paulo` on B3).
