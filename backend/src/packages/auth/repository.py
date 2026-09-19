from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncConnection

from src.database.client import fetch_one, fetch_val, write
from src.identity.port import ExternalIdentity

from .schemas import SessionRecord, UserRecord


async def upsert_user(connection: AsyncConnection, identity: ExternalIdentity) -> UserRecord:
    """Creates the user on a first sign-in, or refreshes the descriptive
    data on every later one (identity-provider spec): identity is
    established by the (provider, provider_user_id) pair (D6), never by
    email, which is why that's the conflict target and not a column of
    its own.
    """
    row = await fetch_one(
        connection,
        """
        insert into users (provider, provider_user_id, email, name, avatar_url)
        values (:provider, :provider_user_id, :email, :name, :avatar_url)
        on conflict (provider, provider_user_id)
        do update set
            email = excluded.email,
            name = excluded.name,
            avatar_url = excluded.avatar_url
        returning id, provider, provider_user_id, email, name, avatar_url
        """,
        UserRecord,
        {
            "provider": identity.provider,
            "provider_user_id": identity.provider_user_id,
            "email": identity.email,
            "name": identity.name,
            "avatar_url": identity.avatar_url,
        },
    )
    assert row is not None
    return row


async def user_exists(connection: AsyncConnection, *, user_id: UUID) -> bool:
    """Without a lock (D1 in add-instance-quota): granting no longer
    serializes on this row -- the instance's own advisory lock covers
    that now -- so this only has to answer whether a session's account
    is still there, the same question `lock_user_id` used to answer
    while it locked the row for the rest of the transaction.
    """
    return await fetch_val(
        connection, "select exists(select 1 from users where id = :user_id)", {"user_id": user_id}
    )


async def delete_expired_sessions_for_user(connection: AsyncConnection, user_id: UUID) -> None:
    """Housekeeping, not correctness (D8): an expired row never
    authenticates regardless of whether it was ever deleted."""
    await write(
        connection,
        "delete from sessions where user_id = :user_id and expires_at <= now()",
        {"user_id": user_id},
    )


async def create_session(
    connection: AsyncConnection,
    *,
    user_id: UUID,
    token_hash: str,
    expires_at: datetime,
) -> SessionRecord:
    row = await fetch_one(
        connection,
        """
        insert into sessions (token_hash, user_id, expires_at)
        values (:token_hash, :user_id, :expires_at)
        returning id, user_id, expires_at
        """,
        SessionRecord,
        {"token_hash": token_hash, "user_id": user_id, "expires_at": expires_at},
    )
    assert row is not None
    return row


async def get_user_by_session_token_hash(
    connection: AsyncConnection, token_hash: str
) -> UserRecord | None:
    """A session that doesn't exist and one that expired come back the
    same way: nothing (session-management spec) -- the caller treats
    both identically."""
    return await fetch_one(
        connection,
        """
        select u.id, u.provider, u.provider_user_id, u.email, u.name, u.avatar_url
        from sessions s
        join users u on u.id = s.user_id
        where s.token_hash = :token_hash and s.expires_at > now()
        """,
        UserRecord,
        {"token_hash": token_hash},
    )


async def delete_session_by_token_hash(connection: AsyncConnection, token_hash: str) -> None:
    await write(
        connection,
        "delete from sessions where token_hash = :token_hash",
        {"token_hash": token_hash},
    )
