from importlib.metadata import PackageNotFoundError, version

from capybucks.core.bootstrap import install_default_providers
from capybucks.core.registry import get_registry
from capybucks.exceptions import (
    CapybucksError,
    MissingAPIKey,
    MultiDownloadError,
    NoProviderError,
    ProviderError,
    ProviderNotFound,
    RateLimitError,
    StreamingNotSupportedError,
    SymbolNotFound,
)
from capybucks.sync import Ticker, download

try:
    __version__ = version("capybucks")
except PackageNotFoundError:  # pragma: no cover — editable / source tree
    __version__ = "0.0.1"

install_default_providers(get_registry())

__all__ = [
    "CapybucksError",
    "MissingAPIKey",
    "MultiDownloadError",
    "NoProviderError",
    "ProviderError",
    "ProviderNotFound",
    "RateLimitError",
    "StreamingNotSupportedError",
    "SymbolNotFound",
    "Ticker",
    "__version__",
    "download",
]
