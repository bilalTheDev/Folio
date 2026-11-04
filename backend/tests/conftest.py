import os
import shutil
import tempfile

os.environ["APP_ENV"] = "test"
os.environ["MONGODB_DB_NAME"] = "folio_test"
_STORAGE = tempfile.mkdtemp(prefix="folio-test-")
os.environ["STORAGE_DIR"] = _STORAGE
os.environ.setdefault("JWT_SECRET", "test-access-secret-not-for-production-use-32+")
os.environ.setdefault("JWT_REFRESH_SECRET", "test-refresh-secret-not-for-production-32+")
os.environ.setdefault("ENCRYPTION_KEY", "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=")
os.environ.setdefault("CORS_ORIGIN", "http://localhost:3000")
# Small cap so size-limit tests don't index a 10 MB dummy file.
os.environ["MAX_UPLOAD_BYTES"] = "8192"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from pymongo import MongoClient  # noqa: E402

from app.config import settings  # noqa: E402
from app.main import app  # noqa: E402

COLLECTIONS = ["users", "documents", "chat_sessions", "chat_messages"]
PASSWORD = "correct-horse-1"


@pytest.fixture(scope="session")
def _app_client():
    with TestClient(app) as client:
        yield client
    shutil.rmtree(_STORAGE, ignore_errors=True)


@pytest.fixture(scope="session")
def mongo():
    client = MongoClient(settings.mongodb_uri, tz_aware=True)
    yield client[settings.mongodb_db_name]
    client.drop_database(settings.mongodb_db_name)
    client.close()


@pytest.fixture
def client(_app_client, mongo):
    for name in COLLECTIONS:
        mongo[name].delete_many({})
    _app_client.cookies.clear()
    yield _app_client
    _app_client.cookies.clear()


def sign_in(client, email: str, password: str = PASSWORD) -> dict:
    """Create the account if needed, sign in, and return Authorization headers."""
    client.post("/auth/signup", json={"email": email, "password": password})
    response = client.post("/auth/signin", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}
