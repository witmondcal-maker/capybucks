# Roadmap

Direction, not a Gantt chart. A phase is done when `pip`/`uv` install works,
the README example for that phase runs, fixture tests pass offline, and CI
is green. Do not start N+1 before N is usable.

North star: a one-liner that does not lie about its data, and a paid /
real-time path without switching libraries.

## Phase 0 — skeleton

- [x] Repo layout, MIT license, logo on README
- [x] `pyproject.toml` (uv/hatchling), ruff + mypy + pytest + CI
- [x] Public envelope: pandas + provenance attrs (not Pydantic-only)
- [x] `Provider` ABC with auth / rate-limit / `stream_quotes` hooks
- [x] `download()` / `Ticker` against an in-memory provider (tests)

## Phase 1 — one-liner

- [x] Yahoo as zero-config equity default (Stooq pin-only: JS bot-check)
- [x] CoinGecko for crypto
- [x] OHLCV columns, tz-aware index
- [x] Incremental parquet cache (same provider only)
- [x] Multi-ticker async, fail-fast on delisted symbols, partial results
- [x] Jupyter: no `RuntimeError` on a running loop
- [x] respx fixtures per provider; weekly `smoke.yml` without requiring a key

Done when `cb.download("AAPL")` returns a plottable frame with provenance.

## Phase 2 — Ticker surface (current)

- [x] Fundamentals (income, balance, cashflow; annual + quarterly)
- [x] Options chain; dividends / splits / actions
- [x] News where the provider actually has it (Yahoo search)
- [x] Twelve Data on the same `download()` / `Ticker` API
- [x] Per-provider rate limits; `~/.capybucks.toml` + `CAPYBUCKS_*_KEY`

Done when a typical history + financials + options notebook runs on this
import alone.

## Phase 3 — pull ahead

- [x] B3 (`.SA` hint, `America/Sao_Paulo` from Yahoo, `BVMF` calendar extra)
- [x] extras `[ta]` (SMA/EMA, RSI, MACD, Bollinger, ATR, VWAP) and `[calendars]`
- [x] WebSocket stream on Twelve Data (`capybucks[stream]`, `AsyncTicker.stream`)
- [ ] Polygon/Massive if Twelve Data is not enough for US realtime

Polygon stays parked until a real gap shows up (US SIP, options firehose).

## Out of scope

Workspace/UI, MCP, Excel, FastAPI clone, order execution, hosted SaaS,
a full backtester, silent fallback that stitches candles from two sources,
and a compatibility shim for another library unless migration proves we
need one.
