from __future__ import annotations

from collections.abc import Sequence

from capybucks.core.models import AssetType
from capybucks.core.provider import Provider
from capybucks.exceptions import NoProviderError, ProviderNotFound

_registry: Registry | None = None


class Registry:
    def __init__(self) -> None:
        self._providers: dict[str, Provider] = {}
        self._defaults: dict[tuple[AssetType, str], str] = {}

    def register(
        self,
        provider: Provider,
        *,
        default_for: Sequence[tuple[AssetType, str]] | None = None,
    ) -> None:
        self._providers[provider.name] = provider
        if default_for is None:
            return
        for asset_type, interval in default_for:
            self._defaults[(asset_type, interval)] = provider.name

    def get(self, name: str) -> Provider:
        try:
            return self._providers[name]
        except KeyError as exc:
            raise ProviderNotFound(name) from exc

    def resolve(
        self,
        *,
        provider: str | None,
        asset_type: AssetType,
        interval: str,
    ) -> Provider:
        if provider is not None:
            return self.get(provider)
        name = self._defaults.get((asset_type, interval)) or self._defaults.get(
            (asset_type, "*")
        )
        if name is None:
            raise NoProviderError(asset_type=asset_type.value, interval=interval)
        return self.get(name)


def get_registry() -> Registry:
    global _registry
    if _registry is None:
        _registry = Registry()
    return _registry


def reset_registry() -> None:
    global _registry
    _registry = Registry()
