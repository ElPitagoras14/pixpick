from datetime import UTC, datetime, timedelta

from sqlalchemy import text

from src.identity.port import ExternalIdentity
from src.packages.auth import repository
from src.packages.auth.security import hash_session_token
from tests.factories import create_session, create_user


async def test_returning_with_the_same_provider_and_subject_is_the_same_user(connection):
    identity = ExternalIdentity(provider="local", provider_user_id="1", email="a@example.com")

    first = await repository.upsert_user(connection, identity)
    second = await repository.upsert_user(connection, identity)

    assert first.id == second.id


async def test_a_changed_email_updates_without_duplicating(connection):
    identity = ExternalIdentity(provider="local", provider_user_id="2", email="old@example.com")
    first = await repository.upsert_user(connection, identity)

    updated_identity = ExternalIdentity(
        provider="local", provider_user_id="2", email="new@example.com"
    )
    second = await repository.upsert_user(connection, updated_identity)

    assert first.id == second.id
    assert second.email == "new@example.com"


async def test_the_same_email_on_two_providers_is_two_users(connection):
    same_email = "shared@example.com"
    first = await repository.upsert_user(
        connection,
        ExternalIdentity(provider="local", provider_user_id="p1", email=same_email),
    )
    second = await repository.upsert_user(
        connection,
        ExternalIdentity(provider="other", provider_user_id="p1", email=same_email),
    )

    assert first.id != second.id


async def test_deleting_expired_sessions_only_touches_that_users_own(connection):
    user = await create_user(connection)
    other_user = await create_user(connection)

    expired, _ = await create_session(
        connection, user_id=user.id, expires_at=datetime.now(UTC) - timedelta(days=1)
    )
    active, _ = await create_session(
        connection, user_id=user.id, expires_at=datetime.now(UTC) + timedelta(days=1)
    )
    other_active, _ = await create_session(
        connection, user_id=other_user.id, expires_at=datetime.now(UTC) - timedelta(days=1)
    )

    await repository.delete_expired_sessions_for_user(connection, user.id)

    remaining_ids = {
        row[0] for row in (await connection.execute(text("select id from sessions"))).all()
    }
    assert expired.id not in remaining_ids
    assert active.id in remaining_ids
    # Another user's expired session is untouched by this call.
    assert other_active.id in remaining_ids


async def test_a_nonexistent_or_expired_session_returns_nothing(connection):
    user = await create_user(connection)
    _, expired_token = await create_session(
        connection, user_id=user.id, expires_at=datetime.now(UTC) - timedelta(days=1)
    )

    assert await repository.get_user_by_session_token_hash(connection, "not-a-real-hash") is None
    assert (
        await repository.get_user_by_session_token_hash(
            connection, hash_session_token(expired_token)
        )
        is None
    )
