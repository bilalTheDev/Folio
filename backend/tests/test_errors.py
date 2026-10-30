"""Error shape and mapping tests."""

from backend.app.errors import FolioError, error_body
from backend.app.rag.validate import IngestError
from backend.app.services.documents import map_ingest_error


def test_error_body_shape() -> None:
    payload = error_body("daily_limit", "Too many questions", 3600)
    assert payload == {
        "error": {
            "code": "daily_limit",
            "message": "Too many questions",
            "retry_after": 3600,
        }
    }


def test_map_ingest_too_large() -> None:
    err = map_ingest_error(IngestError("too_large", "File exceeds the 10 MB limit."))
    assert isinstance(err, FolioError)
    assert err.status_code == 413
    assert err.code == "too_large"
