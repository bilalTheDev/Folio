"""Load provider configuration from providers.json."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

PROVIDERS_PATH = Path(__file__).resolve().parent.parent / "config" / "providers.json"


@lru_cache
def load_providers() -> dict[str, Any]:
    """Return the provider catalog keyed by provider id."""
    return json.loads(PROVIDERS_PATH.read_text(encoding="utf-8"))


def get_provider(provider_id: str) -> dict[str, Any]:
    """Return one provider config or raise KeyError."""
    catalog = load_providers()
    if provider_id not in catalog:
        raise KeyError(provider_id)
    return catalog[provider_id]


def list_providers_public() -> list[dict[str, Any]]:
    """Public provider list for the frontend switcher."""
    items: list[dict[str, Any]] = []
    for provider_id, config in load_providers().items():
        items.append(
            {
                "id": provider_id,
                "base_url": config["base_url"],
                "default_model": config["default_model"],
                "models": config["models"],
            }
        )
    return items
