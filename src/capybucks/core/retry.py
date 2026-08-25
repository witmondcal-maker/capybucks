from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TypeVar

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from capybucks.exceptions import RateLimitError

T = TypeVar("T")


def with_retry(fn: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
    """Retry transient rate limits on the same provider. Never wraps SymbolNotFound."""
    return retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.05, min=0.05, max=0.4),
        retry=retry_if_exception_type(RateLimitError),
    )(fn)
