from app.config import settings
from tests.conftest import PASSWORD, sign_in


def test_signup_creates_user_and_hashes_password(client, mongo):
    response = client.post("/auth/signup", json={"email": "Ada@Example.com", "password": PASSWORD})
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "ada@example.com"
    assert body["onboarding_completed"] is False
    assert body["onboarding"]["next_step"] == "upload"
    assert "password_hash" not in body and "token_encrypted" not in body
    assert body["token_masked"] is None and body["has_credential"] is False

    stored = mongo.users.find_one({"email": "ada@example.com"})
    assert stored["password_hash"].startswith("$2b$")
    assert stored["password_hash"] != PASSWORD


def test_signup_rejects_bad_email_short_password_and_duplicates(client):
    assert client.post("/auth/signup", json={"email": "nope", "password": PASSWORD}).status_code == 422
    short = client.post("/auth/signup", json={"email": "a@example.com", "password": "short1"})
    assert short.status_code == 422
    assert short.json()["code"] == "validation_error"

    assert client.post("/auth/signup", json={"email": "a@example.com", "password": PASSWORD}).status_code == 201
    dup = client.post("/auth/signup", json={"email": "A@example.com", "password": PASSWORD})
    assert dup.status_code == 409
    assert dup.json()["code"] == "email_taken"


def test_signin_sets_httponly_refresh_cookie(client):
    client.post("/auth/signup", json={"email": "b@example.com", "password": PASSWORD})
    response = client.post("/auth/signin", json={"email": "b@example.com", "password": PASSWORD})
    assert response.status_code == 200
    assert response.json()["access_token"]
    cookie = response.headers["set-cookie"]
    assert settings.refresh_cookie_name in cookie
    assert "HttpOnly" in cookie and "Path=/auth" in cookie


def test_signin_wrong_password(client):
    client.post("/auth/signup", json={"email": "c@example.com", "password": PASSWORD})
    response = client.post("/auth/signin", json={"email": "c@example.com", "password": "wrong-pass-9"})
    assert response.status_code == 401
    assert client.post("/auth/signin", json={"email": "ghost@example.com", "password": PASSWORD}).status_code == 401


def test_me_requires_valid_access_token(client):
    assert client.get("/users/me").status_code == 401
    assert client.get("/users/me", headers={"Authorization": "Bearer garbage"}).status_code == 401
    headers = sign_in(client, "d@example.com")
    me = client.get("/users/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["email"] == "d@example.com"
    assert me.json()["token_masked"] is None


def test_refresh_rotates_tokens_and_signout_clears_cookie(client):
    sign_in(client, "e@example.com")
    refreshed = client.post("/auth/refresh")
    assert refreshed.status_code == 200
    new_access = refreshed.json()["access_token"]
    assert client.get("/users/me", headers={"Authorization": f"Bearer {new_access}"}).status_code == 200

    # A refresh token must not be accepted as an access token.
    refresh_cookie = client.cookies.get(settings.refresh_cookie_name)
    assert client.get("/users/me", headers={"Authorization": f"Bearer {refresh_cookie}"}).status_code == 401

    assert client.post("/auth/signout").status_code == 204
    client.cookies.clear()
    assert client.post("/auth/refresh").status_code == 401
