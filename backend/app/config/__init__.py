"""Application settings and provider configuration.

Note: Settings live in this package (not a sibling config.py) because Python
cannot have both a config.py module and a config/ directory.
"""

from backend.app.config.settings import Settings, get_settings

__all__ = ["Settings", "get_settings"]
