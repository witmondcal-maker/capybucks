from __future__ import annotations

from capybucks.core.models import AssetType
from capybucks.core.registry import Registry


def install_default_providers(registry: Registry) -> None:
    """Yahoo is the zero-config equity default; Stooq is pin-only (JS challenge)."""
    from capybucks.providers.coingecko import CoinGeckoProvider
    from capybucks.providers.stooq import StooqProvider
    from capybucks.providers.twelvedata import TwelveDataProvider
    from capybucks.providers.yahoo import YahooProvider

    registry.register(
        YahooProvider(),
        default_for=((AssetType.EQUITY, "*"),),
    )
    registry.register(StooqProvider())
    registry.register(
        CoinGeckoProvider(),
        default_for=((AssetType.CRYPTO, "*"),),
    )
    registry.register(TwelveDataProvider())
