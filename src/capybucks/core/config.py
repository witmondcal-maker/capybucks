from __future__ import annotations

import os
import tomllib
from pathlib import Path

_path: Path | None = None


def set_config_path(path: Path | None) -> None:
    """Tests point this at a temp file so ~/.capybucks.toml is never read."""
    global _path
    _path = path


def config_path() -> Path:
    return _path if _path is not None else Path.home() / ".capybucks.toml"


def get_api_key(provider: str) -> str | None:
    env_name = f"CAPYBUCKS_{provider.upper()}_KEY"
    env = os.environ.get(env_name)
    if env:
        return env.strip() or None
    path = config_path()
    if not path.is_file():
        return None
    raw = tomllib.loads(path.read_text(encoding="utf-8"))
    keys = raw.get("keys")
    if not isinstance(keys, dict):
        return None
    value = keys.get(provider)
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None
