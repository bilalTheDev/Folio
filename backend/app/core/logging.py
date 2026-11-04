import logging
import re

_PATTERNS = [
    (re.compile(r"hf_[A-Za-z0-9]{4,}"), "hf_[REDACTED]"),
    (re.compile(r"(?i)(bearer\s+)[A-Za-z0-9\-._~+/]+=*"), r"\1[REDACTED]"),
    (re.compile(r"(?i)(authorization['\"]?\s*[:=]\s*['\"]?)[^'\",\s]+"), r"\1[REDACTED]"),
]

_installed = False


def redact(text: str) -> str:
    for pattern, replacement in _PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def setup_logging() -> None:
    """Redact HF tokens and bearer credentials from every log record, whatever handler emits it."""
    global _installed
    if _installed:
        return
    base_factory = logging.getLogRecordFactory()

    def factory(*args, **kwargs):
        record = base_factory(*args, **kwargs)
        try:
            message = record.getMessage()
        except Exception:
            return record
        cleaned = redact(message)
        if cleaned != message:
            record.msg, record.args = cleaned, None
        return record

    logging.setLogRecordFactory(factory)
    logging.getLogger("folio").setLevel(logging.INFO)
    _installed = True
