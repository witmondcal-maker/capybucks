# download()

`capybucks.download` fetches OHLCV and returns a pandas DataFrame. It is
the batch entry point. For financials, options, and news, use
[`Ticker`](ticker.md).

```python
import capybucks as cb
from datetime import datetime, timezone

cb.download("AAPL")
cb.download("AAPL", period="1y", interval="1d")
cb.download("AAPL", start=datetime(2024, 1, 1, tzinfo=timezone.utc))
cb.download(["AAPL", "MSFT"], group_by="ticker")
cb.download("BTC-USD")  # crypto → CoinGecko by default
cb.download("AAPL", provider="twelvedata", cache=False)
```

## Parameters

| Name | Default | Meaning |
|---|---|---|
| `tickers` | (required) | One symbol, a comma/space string, or a sequence |
| `period` | `"1mo"` | Lookback if `start` is omitted |
| `interval` | `"1d"` | Bar size |
| `start` / `end` | `None` | Inclusive window; `end` defaults to now |
| `auto_adjust` | `True` | Prefer split/dividend-adjusted close when the source has it |
| `provider` | `None` | Pin a source; otherwise a default for the asset class |
| `group_by` | `"ticker"` | Multi-ticker column layout |
| `cache` | `True` | Read/write the parquet cache for this call |

Symbols are uppercased. `"aapl, msft"` and `["AAPL", "MSFT"]` are the
same request.

## Periods

If you pass `start`, `period` is ignored. Otherwise `period` is subtracted
from `end` (or now):

`1d`, `5d`, `1mo`, `3mo`, `6mo`, `1y`, `2y`, `5y`, `10y`, `max`, `ytd`.

Unknown periods raise `ValueError` with the list of known names — not a
silent empty frame.

`max` is a long lookback (50 years of calendar time on our side). The
**provider** may return less. Yahoo in particular truncates intraday
history.

## Intervals

Common values: `1m`, `5m`, `15m`, `30m`, `1h`, `1d`, `1wk`, `1mo`.

Not every provider implements every interval. Yahoo covers the list
above (plus a few aliases such as `1w` → `1wk`). Twelve Data maps
`1d` → `1day`, `1wk` → `1week`. CoinGecko's public OHLC is coarse
(daily-ish). If the source rejects an interval you get `ProviderError`,
not a resampled guess.

Intraday ranges are short on unofficial endpoints. Ask for `period="5d"`
on `1m`, not `period="max"`.

## One ticker vs many

One symbol → a **flat** column index (`Open`, `High`, …).

Several symbols → a **MultiIndex**. `group_by="ticker"` puts the symbol
on top (`AAPL, Open`). `group_by="column"` puts the field on top
(`Open, AAPL`), which is handy for `df["Close"]`.

```python
wide = cb.download(["AAPL", "MSFT"], group_by="column")
wide["Close"].tail()
```

## Partial batch failure

If you ask for three tickers and one is delisted, the other two still
return. The failed name is recorded on the combined frame:

```python
frame = cb.download(["AAPL", "NOTAREALTICKER", "MSFT"])
frame.attrs["errors"]  # {"NOTAREALTICKER": "..."}
```

If **every** symbol fails, `download` raises `MultiDownloadError`. The
mapping `exc.errors` has each `CapybucksError`. That is the opposite of
retrying a dead ticker until the kernel dies.

## Asset type inference

The registry picks a **default** provider from the symbol shape when you
do not pass `provider=`:

| Pattern | Asset | Default |
|---|---|---|
| `BTC-USD`, `ETH`, names with `-`, `…USDT` | crypto | CoinGecko |
| `EUR/USD` (a slash) | FX | none — you must pin, usually `twelvedata` |
| everything else | equity | Yahoo |

Inference is a convenience, not a security master. `BRK-B` looks like
crypto because of the hyphen; pin `provider="yahoo"` if Yahoo is what
you want. `PETR4.SA` is equity (no slash, no hyphen).

## Cache flag

`cache=True` (default) stores bars under `~/.cache/capybucks` (or
`CAPYBUCKS_CACHE_DIR`), keyed by **provider + symbol + interval**. A
later call only fetches gaps. `cache=False` always hits the network and
does not write.

See [Cache and provenance](cache-and-provenance.md) for why two providers
never share a file.

## Return value

Always pandas today. Column names are the OHLCV set above. Provenance is
on `df.attrs`. An empty successful series does not happen: no bars from
the provider becomes `SymbolNotFound`.
