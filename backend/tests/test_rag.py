import io

import pytest

from app.services import llm
from tests.conftest import sign_in

TOKEN = "gsk_abcdefghijklmnopqrstuvwxyz1234"

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

    async def condense(**kwargs):
        return kwargs["question"]

    monkeypatch.setattr(llm, "answer", answer)
    monkeypatch.setattr(llm, "condense_query", condense)
    return calls


def _onboard(client, email, filename, text):
    headers = sign_in(client, email)
    files = {"file": (filename, io.BytesIO(text.encode()), "text/plain")}
    doc = client.post("/documents/upload", headers=headers, files=files).json()
    saved = client.patch(
        "/users/me/credentials",
        headers=headers,
        json={
            "provider": "groq",
            "auth_mode": "native",
            "token": TOKEN,
            "model": "openai/gpt-oss-120b",
        },
    )
    assert saved.status_code == 200, saved.text
    assert client.patch("/users/me/onboarding", headers=headers).status_code == 200
    return headers, doc


def _status(client, headers, doc_id):
    return next(d for d in client.get("/documents", headers=headers).json() if d["id"] == doc_id)


def test_ingest_stores_section_metadata(client, mongo):
    headers, doc = _onboard(client, "meta@example.com", "alpha.txt", ALPHA)
    user = mongo.users.find_one({"email": "meta@example.com"})
    from app.services.rag import _collection

    stored = _collection(str(user["_id"])).get(
        where={"folio_document_id": doc["id"]}, include=["metadatas", "documents"]
    )
    assert stored["metadatas"]
    meta = stored["metadatas"][0]
    assert meta.get("filename") == "alpha.txt"
    assert meta.get("chunk_index")
    assert meta.get("page_or_section")
    assert any("BLUE HERON" in (text or "") for text in stored["documents"])


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


def test_query_and_passage_embeddings_use_different_prefixes():
    from app.services.rag import embed_model

    model = embed_model()
    text = "What is the launch codename?"
    query_vec = model.get_query_embedding(text)
    passage_vec = model.get_text_embedding(text)
    assert query_vec != passage_vec


INVOICE = (
    "Vendor invoice notes.\n\n"
    "Purchase order ZX-4419 must appear on every line item.\n"
    "The amount due is 18750.50 and is payable by 12 April.\n"
    "Shipping is FOB origin."
)


def test_rerank_promotes_buried_exact_chunk():
    from llama_index.core.schema import TextNode

    from app.services.rag import _maybe_rerank

    filler = [
        TextNode(text=f"Arctic terns migrate through Svalbard in wave {i} every June and eat small fish.")
        for i in range(8)
    ]
    target = TextNode(text="Purchase order ZX-4419 must appear on every line. The amount due is 18750.50.")
    ranked = [(node, 1.0 - (i * 0.05)) for i, node in enumerate([*filler, target])]
    assert "ZX-4419" in ranked[8][0].get_content()
    promoted = _maybe_rerank("What is payable for purchase order ZX-4419?", ranked, top_k=5)
    assert any("ZX-4419" in node.get_content() for node, _ in promoted)


def test_hybrid_retrieval_finds_exact_code_and_amount(client, fake_llm):
    headers, doc = _onboard(client, "hybrid@example.com", "invoice.txt", INVOICE)
    session = client.post("/chat/sessions", headers=headers, json={}).json()
    reply = client.post(
        f"/chat/sessions/{session['id']}/messages",
        headers=headers,
        json={"content": "What is payable for order ZX-4419?"},
    )
    assert reply.status_code == 200, reply.text
    sources = reply.json()["assistant_message"]["sources"]
    blob = " ".join(s["chunk_text"] for s in sources)
    assert "ZX-4419" in blob
    assert "18750.50" in blob


def test_paraphrased_query_still_retrieves_codename(client, fake_llm):
    headers, doc = _onboard(client, "paraphrase@example.com", "alpha.txt", ALPHA)
    session = client.post("/chat/sessions", headers=headers, json={}).json()
    reply = client.post(
        f"/chat/sessions/{session['id']}/messages",
        headers=headers,
        json={"content": "What do they call the launch internally?"},
    )
    assert reply.status_code == 200, reply.text
    sources = reply.json()["assistant_message"]["sources"]
    assert any("BLUE HERON" in s["chunk_text"] for s in sources)


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
    assert fake_llm[0]["token"] == TOKEN
    assert fake_llm[0]["credential"]["provider"] == "groq"
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


def test_switching_active_credential_changes_dispatch(client, fake_llm):
    headers, _ = _onboard(client, "switch@example.com", "alpha.txt", ALPHA)
    saved = client.patch(
        "/users/me/credentials",
        headers=headers,
        json={
            "provider": "cerebras",
            "auth_mode": "native",
            "token": "csk_abcdefghijklmnopqrstuvwxyz5678",
            "model": "gpt-oss-120b",
        },
    )
    assert saved.status_code == 200 and saved.json()["selected_provider"] == "cerebras"

    session = client.post("/chat/sessions", headers=headers, json={}).json()
    first = client.post(
        f"/chat/sessions/{session['id']}/messages", headers=headers, json={"content": "What is the launch codename?"}
    )
    assert first.status_code == 200, first.text
    assert fake_llm[-1]["credential"]["provider"] == "cerebras"

    activated = client.patch("/users/me/credentials/active", headers=headers, json={"provider": "groq"})
    assert activated.json()["selected_provider"] == "groq"
    second = client.post(
        f"/chat/sessions/{session['id']}/messages", headers=headers, json={"content": "What is the launch date?"}
    )
    assert second.status_code == 200, second.text
    assert fake_llm[-1]["credential"]["provider"] == "groq"


def test_hf_credits_error_is_not_generic_502(client, monkeypatch):
    from app.core.errors import AppError
    from app.services import llm

    async def boom(**kwargs):
        raise AppError(
            402,
            "provider_credits",
            "Your Hugging Face token has no Inference Provider credits. Add credits, upgrade to PRO, or switch to a native provider key in Settings.",
        )

    monkeypatch.setattr(llm, "answer", boom)
    headers, _ = _onboard(client, "credits@example.com", "alpha.txt", ALPHA)
    session = client.post("/chat/sessions", headers=headers, json={}).json()
    reply = client.post(
        f"/chat/sessions/{session['id']}/messages", headers=headers, json={"content": "What is the launch codename?"}
    )
    assert reply.status_code == 402
    body = reply.json()
    assert body["code"] == "provider_credits"
    assert "Inference Provider credits" in body["detail"]


def test_named_document_ids_matches_filename_and_stem():
    from bson import ObjectId

    from app.services.chat import named_document_ids

    alpha_id, beta_id = ObjectId(), ObjectId()
    docs = [{"_id": alpha_id, "filename": "alpha.txt"}, {"_id": beta_id, "filename": "beta.txt"}]
    assert named_document_ids("according to alpha.txt where does field work happen?", docs) == [str(alpha_id)]
    assert named_document_ids("Where does field work happen?", docs) is None


def test_follow_up_retrieves_budget_owners(client, fake_llm, monkeypatch):
    async def condense(**kwargs):
        if "budget" in kwargs["question"].lower() or "them" in kwargs["question"].lower():
            return "Alpha budget owners expense reports"
        return kwargs["question"]

    monkeypatch.setattr(llm, "condense_query", condense)
    headers, _ = _onboard(client, "followup@example.com", "alpha.txt", ALPHA)
    beta = client.post(
        "/documents/upload",
        headers=headers,
        files={"file": ("beta.txt", io.BytesIO(BETA.encode()), "text/plain")},
    )
    assert beta.status_code == 201, beta.text
    session = client.post("/chat/sessions", headers=headers, json={}).json()
    first = client.post(
        f"/chat/sessions/{session['id']}/messages",
        headers=headers,
        json={"content": "What is the launch codename?"},
    )
    assert first.status_code == 200, first.text
    reply = client.post(
        f"/chat/sessions/{session['id']}/messages",
        headers=headers,
        json={"content": "what about the budget owners?"},
    )
    assert reply.status_code == 200, reply.text
    blob = " ".join(s["chunk_text"] for s in reply.json()["assistant_message"]["sources"])
    assert "budget owners" in blob.lower() or "expense reports" in blob.lower()


def test_named_filename_never_returns_other_doc(client, fake_llm):
    headers, alpha = _onboard(client, "named@example.com", "alpha.txt", ALPHA)
    beta = client.post(
        "/documents/upload",
        headers=headers,
        files={"file": ("beta.txt", io.BytesIO(BETA.encode()), "text/plain")},
    )
    assert beta.status_code == 201, beta.text
    assert _status(client, headers, beta.json()["id"])["status"] == "indexed"
    session = client.post("/chat/sessions", headers=headers, json={}).json()
    reply = client.post(
        f"/chat/sessions/{session['id']}/messages",
        headers=headers,
        json={"content": "according to alpha.txt where does field work happen?"},
    )
    assert reply.status_code == 200, reply.text
    sources = reply.json()["assistant_message"]["sources"]
    assert sources
    assert {s["document_id"] for s in sources} == {alpha["id"]}
    assert all("Svalbard" not in s["chunk_text"] for s in sources)
    assert all("arctic terns" not in s["chunk_text"] for s in sources)


def test_empty_retrieval_uses_couldnt_find_path(client, fake_llm):
    headers, doc = _onboard(client, "empty@example.com", "alpha.txt", ALPHA)
    assert client.delete(f"/documents/{doc['id']}", headers=headers).status_code == 204
    session = client.post("/chat/sessions", headers=headers, json={}).json()
    reply = client.post(
        f"/chat/sessions/{session['id']}/messages",
        headers=headers,
        json={"content": "What is the launch codename?"},
    )
    assert reply.status_code == 200, reply.text
    body = reply.json()["assistant_message"]
    assert body["sources"] == []
    assert "couldn't find" in body["content"].lower()
    assert not body.get("groundedness_warning")
    assert fake_llm == []


def test_ungrounded_answer_sets_warning(client, monkeypatch):
    async def answer(**kwargs):
        return "Paris is the capital of France and has twelve million residents."

    async def condense(**kwargs):
        return kwargs["question"]

    monkeypatch.setattr(llm, "answer", answer)
    monkeypatch.setattr(llm, "condense_query", condense)
    headers, _ = _onboard(client, "ungrounded@example.com", "alpha.txt", ALPHA)
    session = client.post("/chat/sessions", headers=headers, json={}).json()
    reply = client.post(
        f"/chat/sessions/{session['id']}/messages",
        headers=headers,
        json={"content": "What is the launch codename?"},
    )
    assert reply.status_code == 200, reply.text
    body = reply.json()["assistant_message"]
    assert body["sources"]
    assert body["groundedness_warning"] is True


def test_groundedness_heuristic_unit():
    from app.services.chat import groundedness_warning

    sources = [{"chunk_text": "The launch codename is BLUE HERON.", "parent_text": "The launch codename is BLUE HERON."}]
    assert groundedness_warning("The launch codename is BLUE HERON [1].", sources) is False
    assert groundedness_warning("Paris is the capital of France.", sources) is True
    assert groundedness_warning("I couldn't find it in the documents.", sources) is False
    assert groundedness_warning("BLUE HERON [9].", sources) is True
