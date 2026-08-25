from __future__ import annotations

from capybucks.exceptions import ProviderError


def require_dict(value: object, *, where: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ProviderError(f"{where}: expected a JSON object")
    return {str(key): item for key, item in value.items()}


def require_list(value: object, *, where: str) -> list[object]:
    if not isinstance(value, list):
        raise ProviderError(f"{where}: expected a JSON array")
    return list(value)
