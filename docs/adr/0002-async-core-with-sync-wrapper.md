# 0002: Async core with a synchronous wrapper on top

**Status**: accepted
**Date**: 2026-08-16

## Context

The library serves two audiences: batch/async pulls, and people who want
`download("AAPL")` to block in a notebook. Jupyter already has a running
event loop.

## Decision

`async_api/` is the source of truth. `sync/` runs the coroutine on a loop,
using a worker thread when a loop is already running so Jupyter does not
raise `RuntimeError`. No business logic is duplicated in `sync/`.

## Alternatives considered

- **Sync-only core, thread pool for HTTP** — weaker throughput; fights
  httpx.
- **Async-only** — loses the blocking one-liner audience.
- **`nest_asyncio`** — process-wide monkey patch; too much magic.

## Consequences

- Providers use `httpx`, not `requests`.
- `curl_cffi` / TLS impersonation is not a core dependency.
- Bugfixes in fetch/cache/retry land once, in `async_api/`.
