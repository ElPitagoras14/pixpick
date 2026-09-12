import pytest

from src.exceptions import UnauthenticatedError
from src.identity.port import ExternalIdentity
from src.packages.auth import service
from src.packages.auth.dependencies import get_current_user


async def test_no_cookie_raises_unauthenticated(connection):
    with pytest.raises(UnauthenticatedError):
        await get_current_user(session=None, connection=connection)


async def test_an_invalid_token_raises_unauthenticated(connection):
    with pytest.raises(UnauthenticatedError):
        await get_current_user(session="not-a-real-token", connection=connection)


async def test_a_valid_session_resolves_to_its_user(connection):
    identity = ExternalIdentity(provider="local", provider_user_id="1", email="a@example.com")
    user, token = await service.complete_login(connection, identity)

    resolved = await get_current_user(session=token, connection=connection)

    assert resolved.id == user.id
