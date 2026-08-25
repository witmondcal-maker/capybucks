# 0006: Provider capabilities (auth, rate limit, stream)

**Status**: accepted
**Date**: 2026-08-23

## Context

The first protocol draft was `fetch_history` + `fetch_quote`. Paid keys,
per-vendor rate limits, and WebSocket quotes were marked out of scope.
That would force streaming and credentials to bolt on as a second system
— the opposite of a library you can grow into without changing imports.

## Decision

Every provider declares:

- `name`, `requires_key`, `supports_stream`
- `supports(asset_type)`
- `fetch_history(...)` (required)
- `fetch_quote(...)` (optional until implemented)
- `stream_quotes(...)` — default raises `StreamingNotSupportedError`;
  signature exists from day one even if unimplemented

Rate-limit errors are a typed `RateLimitError`. Retry policy is
per-provider, never on `SymbolNotFound`.

Yahoo scrape/cookie impersonation is **not** a core capability. Use
`httpx`. If Yahoo throttles, another registered provider (Stooq, paid)
is the answer, via an explicit pin or a later default — not TLS tricks.

## Alternatives considered

- **REST-only protocol, add stream in a v2 class** — two APIs forever.
- **`curl_cffi` in core to impersonate Chrome** — brittle wheels, a
  maintenance trap for unofficial scrapers.

## Consequences

- Phase 1 can ship REST-only providers without lying about streaming.
- Phase 2 keys (`CAPYBUCKS_TWELVEDATA_KEY`, `~/.capybucks.toml`) fit the
  same type.
- Install extras (`[polars]`, later `[twelvedata]`) keep the default
  extra-light.
