import pytest

from src.exceptions import UnauthenticatedError
from src.identity.port import ExternalIdentity
from src.packages.auth import service
from src.packages.auth.dependencies import get_current_user, require_session_cookie


def test_no_cookie_raises_unauthenticated():
    with pytest.raises(UnauthenticatedError):
        require_session_cookie(session=None)


async def test_no_cookie_never_reaches_the_connection_dependency(client, monkeypatch):
    """Task 4.4: `get_current_user` declares `require_session_cookie`
    before `get_connection` in its own signature, so FastAPI's own
    dependency resolution -- which stops at the first one that raises --
    never calls `get_connection` at all for a cookie-less request against
    a real, protected route.
    """
    from src.database.dependencies import get_connection

    calls = []
    original = client.app.dependency_overrides[get_connection]

    async def _tracking_override():
        calls.append(1)
        async for value in original():
            yield value

    client.app.dependency_overrides[get_connection] = _tracking_override

    response = client.get("/api/albums")

    assert response.status_code == 401
    assert calls == []


async def test_an_invalid_token_raises_unauthenticated(connection):
    with pytest.raises(UnauthenticatedError):
        await get_current_user(session="not-a-real-token", connection=connection)


async def test_a_valid_session_resolves_to_its_user(connection):
    identity = ExternalIdentity(provider="local", provider_user_id="1", email="a@example.com")
    user, token = await service.complete_login(connection, identity)

    resolved = await get_current_user(session=token, connection=connection)

    assert resolved.id == user.id
