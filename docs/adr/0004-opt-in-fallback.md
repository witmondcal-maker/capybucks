# 0004: Opt-in fallback, deterministic default provider

**Status**: accepted
**Date**: 2026-08-23

## Context

ADR-0001 made automatic provider fallback the reliability story versus a
single hardcoded source. Adjusted close, session calendars, and delay
flags are not interchangeable across vendors. Concatenating Yahoo and
Stooq candles in one series produces a wrong backtest that looks like a
success.

## Decision

The registry resolves **one** provider per call:

1. Explicit `provider="stooq"` (or yahoo, twelvedata, …) wins.
2. Else a deterministic default for `(asset_type, interval)` — daily
   equity prefers Stooq when that provider is registered and zero-config.
3. Retry/backoff applies only to that provider.
4. `fallback=True` is opt-in and still must not stitch two sources into
   one `History`. A fallback, if ever implemented, is a full retry of the
   request on another provider, with provenance reflecting the source that
   actually answered, plus a warning.

`SymbolNotFound` is not retried and does not trigger fallback.

## Alternatives considered

- **Automatic fallback (ADR-0001)** — reliability theater; mixes data.
- **No defaults, user always passes provider** — kills the one-liner.

## Consequences

- Pinning a provider is how you get Yahoo's exact adjustment method.
- Reliability comes from fail-fast typed errors, cache, and not depending
  on Yahoo for daily bars — not from blending feeds.
