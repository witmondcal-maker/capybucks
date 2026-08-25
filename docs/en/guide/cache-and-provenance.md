# Cache and provenance

Two ideas, one goal: you should always know **which vendor** produced a
number, and you should not pay for the same Yahoo range twice in one
afternoon.

## Provenance (`df.attrs`)

After `download()` / `Ticker.history()`, the DataFrame carries:

| Key | Meaning |
|---|---|
| `provider` | Registry name (`yahoo`, `twelvedata`, …) |
| `delayed` | `True` if this path is not a licensed real-time print |
| `adjustment` | `split_and_dividend` when `auto_adjust=True` and the source adjusted; else `none` |
| `asof` | Fetch time in this process |
| `currency` | From the provider when it sends one |
| `errors` | Batch: map of failed symbols → message (often `{}`) |

`attrs` is pandas' bag for metadata. Anything that does `df.copy()`
usually keeps it; anything that rebuilds a frame from numpy may drop it.
If you persist parquet yourself, write the attrs out or you lose the
contract.

Intraday vs daily, split-adjusted vs raw, delayed vs live: if those mix
in one column without a flag, the chart still looks pretty. Provenance
exists so that cannot happen quietly.

## On-disk cache

Default directory: `~/.cache/capybucks`, overridable with
`CAPYBUCKS_CACHE_DIR`.

Layout:

```
{root}/{provider}/{SYMBOL}/{interval}/ohlcv.parquet
{root}/{provider}/{SYMBOL}/{interval}/meta.json
```

The **provider is in the path**. Yahoo's AAPL daily file is not Twelve
Data's AAPL daily file. Merging them on disk would be the same bug as
silent fallback.

What is stored is the series plus coverage (`covered_from` /
`covered_to` on provenance). The next overlapping request only fetches
**gaps**. Weekends and holidays on the coverage window do not trigger an
infinite refetch.

```python
cb.download("AAPL", period="1y")  # network
cb.download("AAPL", period="1y")  # cache
cb.download("AAPL", period="1y", cache=False)  # network, no write
```

Tests point the cache at a temp dir. You can do the same:

```python
from pathlib import Path
from capybucks.async_api import configure_cache

configure_cache(Path("/tmp/capybucks-cache"))
```

`configure_cache(None)` clears the disk layer (memory layer still sits
in-process).

## Same provider only

`merge_history` will refuse to combine two `History` objects from
different `provenance.provider` values. That is enforced in core, not
as a suggestion in the README.

## Invalidation

There is no automatic “Yahoo restated yesterday” invalidation. If you
know a restatement happened, delete that symbol's folder or call with
`cache=False`. Cache TTL policy is intentionally not guessed — ask
before inventing one (see `AGENTS.md`).
