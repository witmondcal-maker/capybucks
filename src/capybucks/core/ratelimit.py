from __future__ import annotations

import asyncio
import os
import time

_DEFAULTS: dict[str, float] = {
    "yahoo": 0.15,
    "stooq": 0.4,
    "coingecko": 1.0,
    "twelvedata": 0.8,
}

_last: dict[str, float] = {}
_locks: dict[str, asyncio.Lock] = {}


def _lock_for(provider: str) -> asyncio.Lock:
    lock = _locks.get(provider)
    if lock is None:
        lock = asyncio.Lock()
        _locks[provider] = lock
    return lock


async def acquire(provider: str) -> None:
    """Serialize outbound calls per provider. Disabled when CAPYBUCKS_NO_RATELIMIT=1."""
    if os.environ.get("CAPYBUCKS_NO_RATELIMIT") == "1":
        return
    interval = _DEFAULTS.get(provider, 0.2)
    lock = _lock_for(provider)
    async with lock:
        previous = _last.get(provider, 0.0)
        wait = previous + interval - time.monotonic()
        if wait > 0:
            await asyncio.sleep(wait)
        _last[provider] = time.monotonic()
