from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncConnection

from src.identity.port import ExternalIdentity

from . import repository
from .config import SESSION_LIFETIME
from .schemas import UserRecord
from .security import generate_session_token, hash_session_token


async def complete_login(
    connection: AsyncConnection, identity: ExternalIdentity
) -> tuple[UserRecord, str]:
    """Creates or refreshes the user, drops their expired sessions, and opens
    a fresh one. Returns the *raw* token: the only place it exists outside
    the cookie it becomes, since the table stores only its hash."""
    user = await repository.upsert_user(connection, identity)
    await repository.delete_expired_sessions_for_user(connection, user.id)

    token = generate_session_token()
    expires_at = datetime.now(UTC) + SESSION_LIFETIME
    await repository.create_session(
        connection,
        user_id=user.id,
        token_hash=hash_session_token(token),
        expires_at=expires_at,
    )
    return user, token


async def resolve_session(connection: AsyncConnection, token: str) -> UserRecord | None:
    """The user a raw session token authenticates, or `None`."""
    return await repository.get_user_by_session_token_hash(connection, hash_session_token(token))


async def end_session(connection: AsyncConnection, token: str) -> None:
    """Removes the session row, so the token stops being honored whether or
    not the browser still holds the cookie."""
    await repository.delete_session_by_token_hash(connection, hash_session_token(token))
