"""Logging filter that redacts sensitive key fields."""

from __future__ import annotations

import logging
from typing import Any

SENSITIVE_NAMES = frozenset(
    {
        "key",
        "api_key",
        "authorization",
        "x-provider-key",
    }
)

REDACTED = "[REDACTED]"


def _redact_mapping(data: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of data with sensitive keys redacted."""
    redacted: dict[str, Any] = {}
    for name, value in data.items():
        if name.lower() in SENSITIVE_NAMES:
            redacted[name] = REDACTED
        elif isinstance(value, dict):
            redacted[name] = _redact_mapping(value)
        else:
            redacted[name] = value
    return redacted


class SensitiveDataFilter(logging.Filter):
    """Drop or redact fields named key, api_key, authorization, or x-provider-key."""

    def filter(self, record: logging.LogRecord) -> bool:
        for name in SENSITIVE_NAMES:
            if hasattr(record, name):
                setattr(record, name, REDACTED)

        if isinstance(record.args, dict):
            record.args = _redact_mapping(record.args)
        elif isinstance(record.args, tuple):
            record.args = tuple(
                _redact_mapping(arg) if isinstance(arg, dict) else arg for arg in record.args
            )

        message = record.__dict__.get("msg")
        if isinstance(message, dict):
            record.msg = _redact_mapping(message)

        return True


def install_logging_filter() -> None:
    """Attach SensitiveDataFilter to the root logger and common handlers."""
    sensitive_filter = SensitiveDataFilter()
    root = logging.getLogger()
    root.addFilter(sensitive_filter)
    for handler in root.handlers:
        handler.addFilter(sensitive_filter)
    logging.getLogger("folio").addFilter(sensitive_filter)
