# Errors

capybucks raises **typed exceptions** instead of returning an empty
DataFrame or a column of `NaN`. Catch these from `capybucks` (they are
re-exported on the package).

```python
import capybucks as cb
from capybucks.exceptions import SymbolNotFound, MissingAPIKey

try:
    cb.download("NOPE")
except SymbolNotFound as err:
    print(err.symbol, err.provider, err.hint)
```

All public failures inherit `CapybucksError`.

## Hierarchy

```
CapybucksError
├── ProviderError          network, schema, HTTP 4xx/5xx after mapping
│   ├── RateLimitError     HTTP 429 (and some 403s)
│   ├── MissingAPIKey      no/invalid key for a gated provider
│   └── SymbolNotFound     the source has no series (incl. delisted)
├── ProviderNotFound       provider="…" is not registered
├── NoProviderError        no default for this asset/interval
├── MultiDownloadError     every symbol in a batch failed
└── StreamingNotSupportedError
```

`NotImplementedError` can still appear if you call `Ticker.financials` on
a provider that has no fundamentals (CoinGecko, Stooq). That is a
capability gap, not a missing ticker.

## SymbolNotFound

The provider returned no bars (or an explicit “not found”). Fields:

- `symbol`
- `provider` (may be `None` in theory; usually set)
- `hint` — for Brazilian cash tickers matching `ABCD1` / `ABCD11`, the
  hint is `{symbol}.SA`

```python
try:
    cb.download("PETR4")
except cb.SymbolNotFound as err:
    assert err.hint == "PETR4.SA"
    cb.download(err.hint)
```

We do **not** auto-append `.SA`. Silent rewrite would fetch the wrong
listing if you meant something else.

## MissingAPIKey

Raised when you pin `provider="twelvedata"` (or another gated source)
without `CAPYBUCKS_TWELVEDATA_KEY` and without `~/.capybucks.toml`. Also
raised when Twelve Data's JSON says the key is invalid.

The message tells you which env var to set. Do not commit `.env` files.

## RateLimitError

The vendor asked you to slow down. Backoff/retry may already have run
inside the client (transient 5xx / 429 policy is per-request). If it
still raises, wait or pin another provider **explicitly** — capybucks
will not switch sources for you.

## MultiDownloadError

Only when **no** ticker in the batch produced a frame. Inspect
`exc.errors`: a dict of symbol → the error for that symbol.

A mixed batch (two live names, one dead) does **not** raise this. The
dead name lands in `frame.attrs["errors"]`.

## ProviderError

Catch-all for a source that responded wrongly: HTML instead of CSV
(Stooq bot-check), unexpected JSON shape, HTTP 4xx/5xx that is not
mapped more specifically.

## What you should not do

```python
df = cb.download("AAPL")
if df.empty:  # this is not how missing data is signaled
    ...
```

A successful call has rows. Absence is an exception. Batch holes are
`attrs["errors"]`.
