# Providers

A **provider** is one market-data source. capybucks never concatenates
two of them into a single OHLCV series. You either take the default for
the asset class or you pin `provider="…"`.

## Who is registered

| Name | Key? | Default for | History | Financials | Options | Stream |
|---|---|---|---|---|---|---|
| `yahoo` | no | equities | yes | yes | yes | no |
| `coingecko` | no | crypto | yes | no | no | no |
| `stooq` | no | — (pin only) | daily CSV | no | no | no |
| `twelvedata` | **yes** | — (pin only) | yes | yes | no | yes (`[stream]`) |
| `memory` | no | tests only | yes | yes | yes | no |

`memory` is not a market. Tests install it as the equity default so CI
never touches the network.

## Defaults vs pins

```python
cb.download("AAPL")  # Yahoo
cb.download("AAPL", provider="yahoo")
cb.download("AAPL", provider="stooq")
cb.download("AAPL", provider="twelvedata")
cb.download("BTC-USD")  # CoinGecko
cb.download("EUR/USD", provider="twelvedata")
```

FX has **no** default. `EUR/USD` without a pin raises `NoProviderError`.
That is intentional: we will not pretend Yahoo understands every FX pair.

Unknown `provider="blob"` raises `ProviderNotFound`.

## Yahoo

Unofficial chart and quoteSummary endpoints. Zero config. Usually
**delayed** (~15 minutes). `df.attrs["delayed"]` is `True`.

Yahoo is the equity default because Stooq, from many datacenter IPs,
returns a JavaScript bot-check page instead of CSV. We still ship Stooq
as a pin so you can use it when the CSV endpoint answers.

Intraday history is short. Fundamentals and options exist on `Ticker`.
Terms of use restrict automated collection — see the README disclaimer.

## Stooq

Daily CSV at `stooq.com`. Pin with `provider="stooq"`. If the body is
HTML (challenge page), you get `ProviderError` mentioning a bot-check —
not a parsed garbage frame.

Do not merge a Stooq series with a Yahoo series by hand and call it one
backtest. Adjustments and calendars differ.

## CoinGecko

Public OHLC for coins. Tickers like `BTC-USD`, `ETH-USD`, or `BTC` map
to CoinGecko ids internally. Rate limits are strict on the free API;
capybucks spaces CoinGecko calls (~1s). `CAPYBUCKS_NO_RATELIMIT=1`
disables that (tests only).

## Twelve Data

Official REST (and optional WebSocket). Requires
`CAPYBUCKS_TWELVEDATA_KEY` or `[keys].twelvedata` in `~/.capybucks.toml`.
Missing credentials raise `MissingAPIKey` **before** the HTTP call.

Twelve Data is never the silent default. You opt in with `provider=`.
REST history is still marked `delayed=True` in provenance until we have
a feed we can honestly call real-time. Stream quotes set `delayed=False`
on the `Quote` object because they come off the websocket.

Plan limits (credits, symbols) are Twelve Data's, not capybucks'. A `429`
becomes `RateLimitError`. A 401/invalid key in the JSON body becomes
`MissingAPIKey`.

Polygon is **not** implemented. It stays parked until Twelve Data is not
enough (US SIP, options firehose).

## One series, one source

Retry and backoff apply to **that** provider only. `SymbolNotFound` is
not retried (the name is not going to appear because we asked twice).
There is no `fallback=True` on `download()` today. If it is added later,
it will be a full retry on another provider with provenance pointing at
whoever actually answered — never a stitch of candles.

## Rate limits

Outbound GETs are serialized per provider (Yahoo ~0.15s, Stooq ~0.4s,
CoinGecko ~1s, Twelve Data ~0.8s). HTTP 429 → `RateLimitError`. HTTP 401
→ `MissingAPIKey`. HTTP 403 is treated as a rejection / rate-style error
(Yahoo uses it as a bot wall).
