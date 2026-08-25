# 0001: Pluggable providers with automatic fallback

**Status**: superseded by [ADR-0004](0004-opt-in-fallback.md)
**Date**: 2026-08-16

## Context

Typical unofficial market-data helpers hardcode a single Yahoo source. A
break there takes every consumer down at once.

## Original decision

Every source is a `Provider`. The registry tries providers in priority
order and falls through on failure, raising only after all have failed.

## Why this was superseded

Automatic fallback across vendors silently mixes adjustment methods,
calendars, and delays. That is a backtest bug with a success-shaped
return value. Pluggable providers remain; automatic fallback does not.
See ADR-0004.
