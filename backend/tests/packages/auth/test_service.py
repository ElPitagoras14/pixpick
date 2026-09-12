from sqlalchemy import text

from src.identity.port import ExternalIdentity
from src.packages.auth import service


async def test_complete_login_returns_a_token_no_stored_value_matches(connection):
    identity = ExternalIdentity(provider="local", provider_user_id="1", email="a@example.com")

    _, token = await service.complete_login(connection, identity)

    stored_hashes = {
        row[0] for row in (await connection.execute(text("select token_hash from sessions"))).all()
    }
    assert token not in stored_hashes


async def test_complete_login_lets_resolve_session_find_the_user_back(connection):
    identity = ExternalIdentity(provider="local", provider_user_id="2", email="b@example.com")

    user, token = await service.complete_login(connection, identity)

    resolved = await service.resolve_session(connection, token)
    assert resolved is not None
    assert resolved.id == user.id


async def test_a_second_login_clears_the_first_users_expired_sessions(connection):
    identity = ExternalIdentity(provider="local", provider_user_id="3", email="c@example.com")

    _, first_token = await service.complete_login(connection, identity)
    # Force the first session to already be expired.
    await connection.execute(text("update sessions set expires_at = now() - interval '1 day'"))

    await service.complete_login(connection, identity)

    assert await service.resolve_session(connection, first_token) is None


async def test_end_session_makes_the_token_stop_authenticating(connection):
    identity = ExternalIdentity(provider="local", provider_user_id="4", email="d@example.com")
    _, token = await service.complete_login(connection, identity)

    await service.end_session(connection, token)

    assert await service.resolve_session(connection, token) is None


async def test_ending_one_session_leaves_the_users_other_sessions_active(connection):
    """D8's cleanup only removes *expired* sessions on login -- it must
    not be confused with what a logout does, which only ever removes
    the one session it names."""
    identity = ExternalIdentity(provider="local", provider_user_id="5", email="e@example.com")
    user, first_token = await service.complete_login(connection, identity)
    # A second sign-in for the same identity opens a second, independent
    # session (e.g. a second browser) without touching the first.
    _, second_token = await service.complete_login(connection, identity)

    await service.end_session(connection, first_token)

    assert await service.resolve_session(connection, first_token) is None
    resolved = await service.resolve_session(connection, second_token)
    assert resolved is not None
    assert resolved.id == user.id
