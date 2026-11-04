import io

import pytest

from app.services import llm
from tests.conftest import sign_in

TOKEN = "hf_abcdefghijklmnopqrstuvwxyz1234"

ALPHA = (
    "Project Alpha handbook.\n\n"
    "The Alpha launch date is the fourteenth of March. The launch codename is BLUE HERON.\n\n"
    "Alpha budget owners must file expense reports within ten working days."
)
BETA = (
    "Beta research notes.\n\n"
    "The Beta team studies migratory patterns of arctic terns. Field work happens in Svalbard every June."
)


@pytest.fixture
def fake_llm(monkeypatch):
    calls = []

    async def answer(**kwargs):
        calls.append(kwargs)
        return "Here is what your documents say [1]."

    monkeypatch.setattr(llm, "answer", answer)
    return calls


def _onboard(client, email, filename, text):
    headers = sign_in(client, email)
    files = {"file": (filename, io.BytesIO(text.encode()), "text/plain")}
    doc = client.post("/documents/upload", headers=headers, files=files).json()
    client.patch("/users/me/hf-token", headers=headers, json={"token": TOKEN})
    client.patch("/users/me/provider", headers=headers, json={"provider": "groq", "model": "openai/gpt-oss-120b"})
    assert client.patch("/users/me/onboarding", headers=headers).status_code == 200
    return headers, doc


def _status(client, headers, doc_id):
    return next(d for d in client.get("/documents", headers=headers).json() if d["id"] == doc_id)


def test_upload_is_indexed_with_chunks(client):
    headers, doc = _onboard(client, "index@example.com", "alpha.txt", ALPHA)
    current = _status(client, headers, doc["id"])
    assert current["status"] == "indexed"
    assert current["chunk_count"] > 0

    reindex = client.post(f"/documents/{doc['id']}/reindex", headers=headers)
    assert reindex.status_code == 202
    after = _status(client, headers, doc["id"])
    assert after["status"] == "indexed" and after["chunk_count"] == current["chunk_count"]


def test_document_without_text_fails(client):
    headers = sign_in(client, "blank@example.com")
    files = {"file": ("blank.txt", io.BytesIO(b"   \n\n  "), "text/plain")}
    doc = client.post("/documents/upload", headers=headers, files=files).json()
    assert _status(client, headers, doc["id"])["status"] == "failed"


def test_chat_returns_grounded_answer_with_sources(client, fake_llm):
    headers, doc = _onboard(client, "chat@example.com", "alpha.txt", ALPHA)
    session = client.post("/chat/sessions", headers=headers, json={}).json()
    assert session["title"] == "Untitled chat"

    reply = client.post(
        f"/chat/sessions/{session['id']}/messages", headers=headers, json={"content": "What is the launch codename?"}
    )
    assert reply.status_code == 200, reply.text
    body = reply.json()
    assert body["session"]["title"] == "What is the launch codename?"
    sources = body["assistant_message"]["sources"]
    assert sources and sources[0]["document_id"] == doc["id"]
    assert sources[0]["filename"] == "alpha.txt"
    assert any("BLUE HERON" in s["chunk_text"] for s in sources)

    # The provider call receives the decrypted token and the retrieved passages.
    assert fake_llm[0]["hf_token"] == TOKEN
    assert fake_llm[0]["provider"] == "groq"
    assert TOKEN not in reply.text

    history = client.get(f"/chat/sessions/{session['id']}/messages", headers=headers).json()
    assert [m["role"] for m in history] == ["user", "assistant"]
    assert history[1]["sources"][0]["chunk_text"] == sources[0]["chunk_text"]


def test_deleted_document_is_no_longer_retrieved(client, fake_llm):
    headers, doc = _onboard(client, "gone@example.com", "alpha.txt", ALPHA)
    assert client.delete(f"/documents/{doc['id']}", headers=headers).status_code == 204
    session = client.post("/chat/sessions", headers=headers, json={}).json()
    reply = client.post(
        f"/chat/sessions/{session['id']}/messages", headers=headers, json={"content": "launch codename"}
    ).json()
    assert reply["assistant_message"]["sources"] == []
    assert fake_llm == []


def test_session_rename_delete_and_isolation(client, fake_llm):
    headers, _ = _onboard(client, "owner@example.com", "alpha.txt", ALPHA)
    session = client.post("/chat/sessions", headers=headers, json={}).json()
    client.post(f"/chat/sessions/{session['id']}/messages", headers=headers, json={"content": "budget rules?"})

    renamed = client.patch(f"/chat/sessions/{session['id']}", headers=headers, json={"title": "  Budget  "})
    assert renamed.status_code == 200 and renamed.json()["title"] == "Budget"

    listing = client.get("/chat/sessions", headers=headers).json()
    assert listing[0]["last_message"]
    assert client.get("/chat/sessions?q=budg", headers=headers).json()[0]["id"] == session["id"]
    assert client.get("/chat/sessions?q=zzz", headers=headers).json() == []

    other, _ = _onboard(client, "intruder@example.com", "beta.txt", BETA)
    assert client.get(f"/chat/sessions/{session['id']}/messages", headers=other).status_code == 404
    assert client.patch(f"/chat/sessions/{session['id']}", headers=other, json={"title": "x"}).status_code == 404
    assert client.delete(f"/chat/sessions/{session['id']}", headers=other).status_code == 404

    assert client.delete(f"/chat/sessions/{session['id']}", headers=headers).status_code == 204
    assert client.get(f"/chat/sessions/{session['id']}", headers=headers).status_code == 404


def test_retrieval_never_crosses_users(client, fake_llm):
    alice, alice_doc = _onboard(client, "alice@example.com", "alpha.txt", ALPHA)
    bob, bob_doc = _onboard(client, "bob@example.com", "beta.txt", BETA)

    # Bob asks about Alice's content: he must only ever get his own passages.
    session = client.post("/chat/sessions", headers=bob, json={}).json()
    reply = client.post(
        f"/chat/sessions/{session['id']}/messages", headers=bob, json={"content": "What is the Alpha launch codename?"}
    ).json()
    sources = reply["assistant_message"]["sources"]
    assert sources and {s["document_id"] for s in sources} == {bob_doc["id"]}
    assert all("BLUE HERON" not in s["chunk_text"] for s in sources)
    assert all("BLUE HERON" not in s["chunk_text"] for s in fake_llm[-1]["sources"])

    session = client.post("/chat/sessions", headers=alice, json={}).json()
    reply = client.post(
        f"/chat/sessions/{session['id']}/messages", headers=alice, json={"content": "Where does field work happen?"}
    ).json()
    assert {s["document_id"] for s in reply["assistant_message"]["sources"]} == {alice_doc["id"]}

    # Document ids are not usable across accounts either.
    assert client.post(f"/documents/{alice_doc['id']}/reindex", headers=bob).status_code == 404
