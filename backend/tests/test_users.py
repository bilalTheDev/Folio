import io
import logging

from tests.conftest import sign_in

TOKEN = "hf_abcdefghijklmnopqrstuvwxyz1234"


def _upload(client, headers):
    files = {"file": ("a.txt", io.BytesIO(b"Folio onboarding document."), "text/plain")}
    assert client.post("/documents/upload", headers=headers, files=files).status_code == 201


def test_hf_token_is_encrypted_and_masked(client, mongo, caplog):
    headers = sign_in(client, "tok@example.com")
    with caplog.at_level(logging.DEBUG):
        response = client.patch("/users/me/hf-token", headers=headers, json={"token": TOKEN})
    assert response.status_code == 200
    body = response.json()
    assert body["hf_token_masked"] == "hf_****1234"
    assert body["has_hf_token"] is True
    assert TOKEN not in response.text

    stored = mongo.users.find_one({"email": "tok@example.com"})["hf_token_encrypted"]
    assert stored and TOKEN not in stored and not stored.startswith("hf_")

    me = client.get("/users/me", headers=headers)
    assert TOKEN not in me.text and me.json()["hf_token_masked"] == "hf_****1234"
    assert TOKEN not in caplog.text


def test_hf_token_validation(client):
    headers = sign_in(client, "tok2@example.com")
    assert client.patch("/users/me/hf-token", headers=headers, json={"token": "not-a-token"}).status_code == 422
    assert client.patch("/users/me/hf-token", headers=headers, json={"token": "hf_ab cd ef"}).status_code == 422


def test_provider_must_be_allowlisted(client):
    headers = sign_in(client, "prov@example.com")
    providers = client.get("/providers", headers=headers).json()
    assert {p["id"] for p in providers} >= {"groq", "cerebras"}

    bad = client.patch("/users/me/provider", headers=headers, json={"provider": "groq", "model": "made/up"})
    assert bad.status_code == 422
    good = client.patch(
        "/users/me/provider", headers=headers, json={"provider": "groq", "model": "openai/gpt-oss-120b"}
    )
    assert good.status_code == 200
    assert good.json()["selected_provider"] == "groq"


def test_onboarding_is_sequential_and_enforced(client):
    headers = sign_in(client, "flow@example.com")

    def complete():
        return client.patch("/users/me/onboarding", headers=headers)

    assert client.post("/chat/sessions", headers=headers, json={}).status_code == 403

    missing = complete()
    assert missing.status_code == 409 and missing.json()["code"] == "onboarding_upload"

    _upload(client, headers)
    assert client.get("/users/me", headers=headers).json()["onboarding"]["next_step"] == "token"
    assert complete().json()["code"] == "onboarding_token"

    client.patch("/users/me/hf-token", headers=headers, json={"token": TOKEN})
    assert complete().json()["code"] == "onboarding_provider"

    client.patch("/users/me/provider", headers=headers, json={"provider": "cerebras", "model": "openai/gpt-oss-120b"})
    done = complete()
    assert done.status_code == 200
    assert done.json()["onboarding_completed"] is True
    assert done.json()["onboarding"]["next_step"] == "done"
    assert client.post("/chat/sessions", headers=headers, json={}).status_code == 201
