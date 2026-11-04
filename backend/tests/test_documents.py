import io

from app.config import settings
from tests.conftest import sign_in


def _upload(client, headers, name="notes.txt", content=b"Folio stores documents.", mime="text/plain"):
    return client.post("/documents/upload", headers=headers, files={"file": (name, io.BytesIO(content), mime)})


def test_upload_list_delete(client, mongo):
    headers = sign_in(client, "docs@example.com")
    response = _upload(client, headers)
    assert response.status_code == 201, response.text
    doc = response.json()
    assert doc["filename"] == "notes.txt"
    assert doc["mime_type"] == "text/plain"
    assert doc["size_bytes"] == len(b"Folio stores documents.")
    assert doc["status"] in {"uploaded", "indexing", "indexed"}

    stored = mongo.documents.find_one({})
    assert (settings.storage_root / stored["storage_path"]).exists()
    assert stored["storage_path"].startswith(str(stored["user_id"]))

    listing = client.get("/documents", headers=headers).json()
    assert [d["id"] for d in listing] == [doc["id"]]

    assert client.delete(f"/documents/{doc['id']}", headers=headers).status_code == 204
    assert client.get("/documents", headers=headers).json() == []
    assert not (settings.storage_root / stored["storage_path"]).exists()


def test_upload_requires_auth(client):
    assert _upload(client, {}).status_code == 401


def test_rejects_file_over_the_size_cap(client, mongo):
    headers = sign_in(client, "big@example.com")
    too_big = b"a" * (settings.max_upload_bytes + 1)
    response = _upload(client, headers, name="big.txt", content=too_big)
    assert response.status_code == 413
    assert mongo.documents.count_documents({}) == 0
    assert settings.max_upload_bytes <= 10 * 1024 * 1024


def test_accepts_file_exactly_at_limit(client):
    headers = sign_in(client, "edge@example.com")
    response = _upload(client, headers, name="edge.txt", content=b"a" * settings.max_upload_bytes)
    assert response.status_code == 201, response.text


def test_rejects_unsupported_and_spoofed_types(client, mongo):
    headers = sign_in(client, "types@example.com")
    assert _upload(client, headers, name="image.png", content=b"\x89PNG", mime="image/png").status_code == 415
    spoofed = _upload(client, headers, name="fake.pdf", content=b"not really a pdf", mime="application/pdf")
    assert spoofed.status_code == 415
    assert _upload(client, headers, name="empty.txt", content=b"").status_code == 400
    assert mongo.documents.count_documents({}) == 0


def test_documents_are_scoped_to_owner(client):
    alice = sign_in(client, "alice@example.com")
    doc_id = _upload(client, alice).json()["id"]
    bob = sign_in(client, "bob@example.com")
    assert client.get("/documents", headers=bob).json() == []
    assert client.delete(f"/documents/{doc_id}", headers=bob).status_code == 404
    assert client.delete("/documents/not-an-id", headers=bob).status_code == 404
    assert len(client.get("/documents", headers=alice).json()) == 1
