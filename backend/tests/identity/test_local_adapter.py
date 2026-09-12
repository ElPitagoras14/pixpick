from urllib.parse import parse_qs, urlparse

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.identity.adapters.local import LocalAuthAdapter, router
from src.identity.exceptions import InvalidCodeError


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(router, prefix="/api")
    return TestClient(app, follow_redirects=False)


async def test_the_cycle_produces_an_identity_with_provider_and_subject():
    adapter = LocalAuthAdapter()

    authorization_url = adapter.authorization_url(state="the-state")
    assert "state=the-state" in authorization_url

    response = _client().post(
        "/api/auth/local/dev-login",
        data={"state": "the-state", "email": "person@example.com", "name": "Person"},
    )
    assert response.status_code == 303

    redirect = urlparse(response.headers["location"])
    query = parse_qs(redirect.query)
    assert query["state"] == ["the-state"]
    code = query["code"][0]

    identity = await adapter.exchange_code(code=code)

    assert identity.provider == "local"
    assert identity.provider_user_id == "person@example.com"
    assert identity.email == "person@example.com"


async def test_a_code_cannot_be_exchanged_twice():
    adapter = LocalAuthAdapter()
    response = _client().post(
        "/api/auth/local/dev-login",
        data={"state": "s", "email": "once@example.com", "name": ""},
    )
    code = parse_qs(urlparse(response.headers["location"]).query)["code"][0]

    await adapter.exchange_code(code=code)

    with pytest.raises(InvalidCodeError):
        await adapter.exchange_code(code=code)
