from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId

from app.core.errors import AppError


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def parse_object_id(value: str, what: str = "Resource") -> ObjectId:
    """Malformed ids are reported as 404, the same as ids that belong to someone else."""
    try:
        return ObjectId(value)
    except (InvalidId, TypeError):
        raise AppError(404, "not_found", f"{what} not found.")
