# 0005: Pandas as the public time-series type

**Status**: accepted
**Date**: 2026-08-23

## Context

The original AGENTS.md rule returned only Pydantic to users. Notebook
callers expect a DataFrame with `Open`/`High`/`Low`/`Close`/`Adj Close`/
`Volume` and a DatetimeIndex. Nobody computes RSI on `list[OHLCVBar]`.

## Decision

- Provider → core: Pydantic `OHLCVBar` + `Provenance` (ADR-0003).
- Public `download()` / `Ticker.history()`: `pandas.DataFrame` by default.
- Optional `as_frame="polars"` when the extra is installed.
- Provenance is copied onto `DataFrame.attrs`: `provider`, `delayed`,
  `adjustment`, `asof`, `currency`.
- `Quote` and similar snapshots may remain Pydantic.

Default column names are the usual OHLCV set so existing notebook code
keeps working. `columns="snake"` may be added later.

## Alternatives considered

- **Pydantic-only public API** — correct for services, fatal for
  notebooks.
- **Polars-only** — faster internals, smaller audience than pandas today.
- **Custom envelope object with `.df` only** — extra hop versus a bare
  DataFrame.

## Consequences

- pandas is a hard runtime dependency.
- `df.attrs` is the provenance channel; callers who strip attrs lose it.
- Tests assert column names and attrs, not only dtypes.
