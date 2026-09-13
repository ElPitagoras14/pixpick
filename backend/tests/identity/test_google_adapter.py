import base64
import json
from urllib.parse import parse_qs, urlparse

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.identity.adapters.google import GoogleAuthAdapter, router
from src.identity.exceptions import InvalidCodeError


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(router, prefix="/api")
    return TestClient(app, follow_redirects=False)


def _fake_id_token(payload: dict) -> str:
    """A JWT-shaped string carrying `payload`, with no real signature --
    this project never checks one (D1), so tests don't need to produce
    one either.
    """

    def _segment(data: bytes) -> str:
        return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

    header = _segment(b'{"alg":"none"}')
    body = _segment(json.dumps(payload).encode())
    return f"{header}.{body}.unverified"


def _patch_credentials(
    monkeypatch, client_id: str = "client-id", client_secret: str = "client-secret"
):
    monkeypatch.setattr(
        "src.identity.adapters.google.identity_settings.google_client_id", client_id
    )
    monkeypatch.setattr(
        "src.identity.adapters.google.identity_settings.google_client_secret", client_secret
    )
    monkeypatch.setattr("src.identity.adapters.google.settings.public_url", "http://localhost:8080")


def test_authorization_url_carries_the_minimal_scopes_and_no_more(monkeypatch):
    _patch_credentials(monkeypatch)

    authorization_url = GoogleAuthAdapter().authorization_url(state="the-state")

    parsed = urlparse(authorization_url)
    query = parse_qs(parsed.query)
    assert parsed.scheme == "https"
    assert parsed.netloc == "accounts.google.com"
    assert query["scope"] == ["openid email profile"]
    assert query["state"] == ["the-state"]
    assert query["client_id"] == ["client-id"]
    assert query["redirect_uri"] == ["http://localhost:8080/api/auth/google/callback"]


async def test_the_exchange_produces_an_identity_with_provider_and_subject(monkeypatch):
    _patch_credentials(monkeypatch)
    id_token = _fake_id_token(
        {
            "iss": "https://accounts.google.com",
            "aud": "client-id",
            "sub": "10769150350006150715113082367",
            "email": "person@example.com",
            "name": "Person",
            "picture": "https://example.com/avatar.png",
        }
    )

    async def _fake_post(self, url, *, data):
        assert url == "https://oauth2.googleapis.com/token"
        assert data["code"] == "a-code"
        return httpx.Response(200, json={"id_token": id_token})

    monkeypatch.setattr(httpx.AsyncClient, "post", _fake_post)

    identity = await GoogleAuthAdapter().exchange_code(code="a-code")

    assert identity.provider == "google"
    assert identity.provider_user_id == "10769150350006150715113082367"
    assert identity.email == "person@example.com"


async def test_a_missing_avatar_does_not_block_the_identity(monkeypatch):
    _patch_credentials(monkeypatch)
    id_token = _fake_id_token(
        {"iss": "https://accounts.google.com", "aud": "client-id", "sub": "1"}
    )

    async def _fake_post(self, url, *, data):
        return httpx.Response(200, json={"id_token": id_token})

    monkeypatch.setattr(httpx.AsyncClient, "post", _fake_post)

    identity = await GoogleAuthAdapter().exchange_code(code="a-code")

    assert identity.provider_user_id == "1"
    assert identity.avatar_url is None


async def test_a_token_issued_for_another_application_is_rejected(monkeypatch):
    _patch_credentials(monkeypatch)
    id_token = _fake_id_token(
        {"iss": "https://accounts.google.com", "aud": "someone-elses-client-id", "sub": "1"}
    )

    async def _fake_post(self, url, *, data):
        return httpx.Response(200, json={"id_token": id_token})

    monkeypatch.setattr(httpx.AsyncClient, "post", _fake_post)

    with pytest.raises(InvalidCodeError):
        await GoogleAuthAdapter().exchange_code(code="a-code")


async def test_a_failed_exchange_produces_no_identity(monkeypatch):
    _patch_credentials(monkeypatch)

    async def _fake_post(self, url, *, data):
        return httpx.Response(400, json={"error": "invalid_grant"})

    monkeypatch.setattr(httpx.AsyncClient, "post", _fake_post)

    with pytest.raises(InvalidCodeError):
        await GoogleAuthAdapter().exchange_code(code="a-bad-code")


def test_a_successful_return_forwards_only_state_and_code_to_the_shared_callback(monkeypatch):
    monkeypatch.setattr("src.identity.adapters.google.settings.public_url", "http://localhost:8080")

    response = _client().get(
        "/api/auth/google/callback", params={"state": "the-state", "code": "the-code"}
    )

    assert response.status_code == 302
    assert response.headers["location"] == "/api/auth/callback?state=the-state&code=the-code"


def test_a_rejected_consent_returns_to_the_sign_in_screen_without_alarm(monkeypatch):
    monkeypatch.setattr("src.identity.adapters.google.settings.public_url", "http://localhost:8080")

    response = _client().get(
        "/api/auth/google/callback", params={"state": "the-state", "error": "access_denied"}
    )

    assert response.status_code == 302
    assert response.headers["location"] == "http://localhost:8080/login"


def test_a_provider_error_other_than_a_rejection_is_a_failure():
    with pytest.raises(InvalidCodeError):
        _client().get(
            "/api/auth/google/callback", params={"state": "the-state", "error": "server_error"}
        )


def test_neither_a_rejection_nor_a_failure_reaches_the_shared_login_service(monkeypatch):
    """Neither outcome calls the code that would create a user or a
    session (identity-provider spec, established by
    `add-auth-port-and-local-provider`): both return, or raise, before the
    shared `/api/auth/callback` -- the only caller of that service -- is
    ever reached.
    """
    calls = []
    monkeypatch.setattr("src.packages.auth.service.complete_login", lambda *a, **k: calls.append(1))

    _client().get("/api/auth/google/callback", params={"state": "s", "error": "access_denied"})
    with pytest.raises(InvalidCodeError):
        _client().get("/api/auth/google/callback", params={"state": "s", "error": "server_error"})

    assert calls == []
