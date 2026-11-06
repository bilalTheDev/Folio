import io
import logging

from app.models.common import utcnow
from app.services.encryption import encrypt
from tests.conftest import sign_in

HF_TOKEN = "hf_abcdefghijklmnopqrstuvwxyz1234"
GROQ_TOKEN = "gsk_abcdefghijklmnopqrstuvwxyz1234"
CEREBRAS_TOKEN = "csk_abcdefghijklmnopqrstuvwxyz5678"


def _upload(client, headers):
    files = {"file": ("a.txt", io.BytesIO(b"Folio onboarding document."), "text/plain")}
    assert client.post("/documents/upload", headers=headers, files=files).status_code == 201


def _save_credential(client, headers, **overrides):
    payload = {
        "provider": "groq",
        "auth_mode": "native",
        "token": GROQ_TOKEN,
        "model": "openai/gpt-oss-120b",
        **overrides,
    }
    return client.patch("/users/me/credentials", headers=headers, json=payload)


def test_native_groq_key_is_encrypted_and_masked(client, mongo, caplog):
    headers = sign_in(client, "tok@example.com")
    with caplog.at_level(logging.DEBUG):
        response = _save_credential(client, headers)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["token_masked"] == "gsk_****1234"
    assert body["has_credential"] is True
    assert body["selected_provider"] == "groq"
    assert body["auth_mode"] == "native"
    assert GROQ_TOKEN not in response.text

    stored = mongo.users.find_one({"email": "tok@example.com"})
    assert "hf_token_encrypted" not in stored
    encrypted = stored["credentials"][0]["token_encrypted"]
    assert encrypted and GROQ_TOKEN not in encrypted and not encrypted.startswith("gsk_")

    listing = client.get("/users/me/credentials", headers=headers)
    assert listing.status_code == 200
    assert listing.json()[0]["token_masked"] == "gsk_****1234"
    assert listing.json()[0]["is_active"] is True
    assert GROQ_TOKEN not in listing.text
    assert GROQ_TOKEN not in caplog.text


def test_token_prefix_and_allowlist_validation(client):
    headers = sign_in(client, "tok2@example.com")
    assert (
        _save_credential(client, headers, token="not-a-token").status_code == 422
    )
    assert _save_credential(client, headers, token="gsk_ab cd").status_code == 422
    assert _save_credential(client, headers, model="made/up").status_code == 422
    assert _save_credential(client, headers, auth_mode="hf_inference_providers", token=GROQ_TOKEN).status_code == 422


def test_providers_catalog_includes_auth_modes(client):
    headers = sign_in(client, "prov@example.com")
    providers = client.get("/providers", headers=headers).json()
    ids = {p["id"] for p in providers}
    assert ids >= {"groq", "cerebras", "huggingface"}
    groq = next(p for p in providers if p["id"] == "groq")
    modes = {m["id"] for m in groq["auth_modes"]}
    assert modes == {"native", "hf_inference_providers"}


def test_onboarding_is_sequential_and_enforced(client):
    headers = sign_in(client, "flow@example.com")

    def complete():
        return client.patch("/users/me/onboarding", headers=headers)

    assert client.post("/chat/sessions", headers=headers, json={}).status_code == 403

    missing = complete()
    assert missing.status_code == 409 and missing.json()["code"] == "onboarding_upload"

    _upload(client, headers)
    assert client.get("/users/me", headers=headers).json()["onboarding"]["next_step"] == "provider"
    assert complete().json()["code"] == "onboarding_credential"

    saved = _save_credential(client, headers)
    assert saved.status_code == 200
    done = complete()
    assert done.status_code == 200
    assert done.json()["onboarding_completed"] is True
    assert done.json()["onboarding"]["next_step"] == "done"
    assert client.post("/chat/sessions", headers=headers, json={}).status_code == 201


def test_switch_and_remove_credentials(client):
    headers = sign_in(client, "switch@example.com")
    assert _save_credential(client, headers).status_code == 200
    second = _save_credential(
        client,
        headers,
        provider="cerebras",
        token=CEREBRAS_TOKEN,
        model="gpt-oss-120b",
    )
    assert second.status_code == 200
    assert second.json()["selected_provider"] == "cerebras"
    listing = client.get("/users/me/credentials", headers=headers).json()
    assert len(listing) == 2
    assert sum(1 for c in listing if c["is_active"]) == 1

    activated = client.patch("/users/me/credentials/active", headers=headers, json={"provider": "groq"})
    assert activated.status_code == 200
    assert activated.json()["selected_provider"] == "groq"

    removed = client.delete("/users/me/credentials/cerebras", headers=headers)
    assert removed.status_code == 200
    assert [c["provider"] for c in client.get("/users/me/credentials", headers=headers).json()] == ["groq"]

    last = client.delete("/users/me/credentials/groq", headers=headers)
    assert last.status_code == 409 and last.json()["code"] == "last_credential"


def test_legacy_hf_user_is_migrated(client, mongo):
    headers = sign_in(client, "legacy@example.com")
    mongo.users.update_one(
        {"email": "legacy@example.com"},
        {
            "$set": {
                "hf_token_encrypted": encrypt(HF_TOKEN),
                "selected_provider": "groq",
                "selected_model": "openai/gpt-oss-120b",
                "created_at": utcnow(),
            },
            "$unset": {"credentials": ""},
        },
    )
    me = client.get("/users/me", headers=headers)
    assert me.status_code == 200
    body = me.json()
    assert body["selected_provider"] == "groq"
    assert body["auth_mode"] == "hf_inference_providers"
    assert body["token_masked"] == "hf_****1234"
    assert HF_TOKEN not in me.text

    stored = mongo.users.find_one({"email": "legacy@example.com"})
    assert "hf_token_encrypted" not in stored
    assert stored["credentials"][0]["auth_mode"] == "hf_inference_providers"
    assert stored["credentials"][0]["is_active"] is True
    assert HF_TOKEN not in stored["credentials"][0]["token_encrypted"]
