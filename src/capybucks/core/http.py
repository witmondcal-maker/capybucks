from __future__ import annotations

from typing import cast

import httpx

from capybucks.core.ratelimit import acquire
from capybucks.exceptions import MissingAPIKey, ProviderError, RateLimitError

BROWSER_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

_TIMEOUT = httpx.Timeout(20.0)


def _client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        headers={"User-Agent": BROWSER_UA, "Accept": "*/*"},
        timeout=_TIMEOUT,
        follow_redirects=True,
    )


def _raise_status(response: httpx.Response, *, provider: str) -> None:
    if response.status_code == 429:
        raise RateLimitError(f"{provider} rate-limited this client")
    if response.status_code == 401:
        raise MissingAPIKey(provider)
    if response.status_code == 403:
        raise RateLimitError(
            f"{provider} rejected the request ({response.status_code})"
        )
    if response.status_code >= 400:
        raise ProviderError(f"{provider} HTTP {response.status_code}")


async def get_text(
    url: str, *, provider: str, params: dict[str, str] | None = None
) -> str:
    async with _client() as client:
        await acquire(provider)
        response = await client.get(url, params=params)
        _raise_status(response, provider=provider)
        return response.text


async def get_json(
    url: str, *, provider: str, params: dict[str, str] | None = None
) -> object:
    async with _client() as client:
        await acquire(provider)
        response = await client.get(url, params=params)
        _raise_status(response, provider=provider)
        return cast(object, response.json())
