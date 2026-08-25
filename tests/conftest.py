from __future__ import annotations

from pathlib import Path

import pytest

from capybucks.async_api.download import configure_cache
from capybucks.core.config import set_config_path
from capybucks.core.models import AssetType
from capybucks.core.registry import get_registry, reset_registry
from capybucks.providers.memory import MemoryProvider


@pytest.fixture(autouse=True)
def isolated_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    request: pytest.FixtureRequest,
) -> None:
    monkeypatch.setenv("CAPYBUCKS_NO_RATELIMIT", "1")
    if request.node.get_closest_marker("live") is None:
        monkeypatch.delenv("CAPYBUCKS_TWELVEDATA_KEY", raising=False)
    set_config_path(tmp_path / "capybucks.toml")
    reset_registry()
    get_registry().register(
        MemoryProvider(),
        default_for=((AssetType.EQUITY, "*"),),
    )
    configure_cache(tmp_path / "cache")
    yield
    reset_registry()
    set_config_path(None)
