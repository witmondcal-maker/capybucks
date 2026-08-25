# 0003: Typed multi-asset data model (internal)

**Status**: accepted (public frames: [ADR-0005](0005-pandas-public-frames.md))
**Date**: 2026-08-16

## Context

Equities, crypto, FX, and bonds share OHLCV but not every field. Provider
JSON drifts. Common wrappers push that drift onto the caller as `NaN`.

## Decision

`core/models.py` defines Pydantic `OHLCVBar`, `Quote`, `Instrument`, and
`Provenance`. Providers map raw responses into these types **before**
anything is converted to a DataFrame. Asset-specific models (`Equity`,
`CryptoPair`, …) add fields unique to that class when those asset classes
ship.

## Alternatives considered

- **Separate hierarchies per asset, no shared bar** — duplicates
  `download` per asset type.
- **Untyped dicts/DataFrames at the provider boundary** — schema drift is
  silent.

## Consequences

- A renamed provider field fails at fetch time.
- Shared bar fields are a cross-provider breaking change — treat
  `OHLCVBar` as a careful boundary.
- Users still receive pandas for series (ADR-0005). Pydantic does not
  cross the public time-series API.
