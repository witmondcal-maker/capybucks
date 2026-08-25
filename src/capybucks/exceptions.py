"""Public exceptions. Callers should catch these instead of empty frames."""

from __future__ import annotations

import re

_B3_TICKER = re.compile(r"^[A-Z]{4}\d{1,2}$")


class CapybucksError(Exception):
    """Base error for the public API."""


class ProviderError(CapybucksError):
    """A registered provider failed a fetch (network, schema, 5xx)."""


class RateLimitError(ProviderError):
    """The provider rejected the request as too frequent."""


class MissingAPIKey(ProviderError):
    """A key-gated provider was used without credentials."""

    def __init__(self, provider: str) -> None:
        self.provider = provider
        super().__init__(
            f"{provider} requires an API key "
            f"(env CAPYBUCKS_{provider.upper()}_KEY or ~/.capybucks.toml)"
        )


class SymbolNotFound(ProviderError):
    """The provider has no series for this symbol (including delisted)."""

    def __init__(self, symbol: str, *, provider: str | None = None) -> None:
        self.symbol = symbol
        self.provider = provider
        self.hint: str | None = None
        loc = f" via {provider}" if provider else ""
        message = f"no price data for {symbol!r}{loc}"
        if _B3_TICKER.fullmatch(symbol):
            self.hint = f"{symbol}.SA"
            message = f"{message}. Did you mean {self.hint}?"
        super().__init__(message)


class StreamingNotSupportedError(CapybucksError):
    """This provider has no live stream (see `supports_stream`)."""

    def __init__(self, provider: str) -> None:
        self.provider = provider
        super().__init__(f"{provider!r} does not support streaming quotes")


class ProviderNotFound(CapybucksError):
    """`provider=` named a source that is not registered."""

    def __init__(self, name: str) -> None:
        self.name = name
        super().__init__(f"unknown provider {name!r}")


class NoProviderError(CapybucksError):
    """No provider is registered for this asset/interval."""

    def __init__(self, *, asset_type: str, interval: str) -> None:
        self.asset_type = asset_type
        self.interval = interval
        super().__init__(
            f"no provider registered for {asset_type} interval {interval!r}."
        )


class MultiDownloadError(CapybucksError):
    """Every symbol in a batch download failed."""

    def __init__(self, errors: dict[str, CapybucksError]) -> None:
        self.errors = errors
        names = ", ".join(sorted(errors))
        super().__init__(f"download failed for all symbols: {names}")
