from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

import capybucks as cb
from capybucks.core.bootstrap import install_default_providers
from capybucks.core.config import get_api_key, set_config_path
from capybucks.core.ratelimit import _last, acquire
from capybucks.core.registry import get_registry, reset_registry
from capybucks.exceptions import MissingAPIKey, SymbolNotFound


def test_env_key_wins(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("CAPYBUCKS_TWELVEDATA_KEY", "from-env")
    set_config_path(tmp_path / "capybucks.toml")
    (tmp_path / "capybucks.toml").write_text(
        '[keys]\ntwelvedata = "from-toml"\n', encoding="utf-8"
    )
    assert get_api_key("twelvedata") == "from-env"


def test_toml_key(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CAPYBUCKS_TWELVEDATA_KEY", raising=False)
    set_config_path(tmp_path / "capybucks.toml")
    (tmp_path / "capybucks.toml").write_text(
        '[keys]\ntwelvedata = "from-toml"\n', encoding="utf-8"
    )
    assert get_api_key("twelvedata") == "from-toml"


def test_missing_key_is_typed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CAPYBUCKS_TWELVEDATA_KEY", raising=False)
    reset_registry()
    install_default_providers(get_registry())
    with pytest.raises(MissingAPIKey):
        cb.download("AAPL", provider="twelvedata")


def test_b3_symbol_hint() -> None:
    with pytest.raises(SymbolNotFound, match=r"PETR4\.SA") as caught:
        cb.download("PETR4")
    assert caught.value.hint == "PETR4.SA"


@pytest.mark.asyncio
async def test_ratelimit_spaces_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CAPYBUCKS_NO_RATELIMIT", raising=False)
    _last.clear()
    start = datetime.now(UTC)
    await acquire("yahoo")
    await acquire("yahoo")
    elapsed = (datetime.now(UTC) - start).total_seconds()
    assert elapsed >= 0.14
