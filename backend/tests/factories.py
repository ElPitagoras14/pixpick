"""Shared constructors for the entities this project has (backend-testing
spec): a test declares only the fields its verification involves, and the
rest take valid defaults, so a new required column is absorbed here once
instead of in every test that builds a user or a session.
"""

import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncConnection

from src.database.client import fetch_one
from src.packages.auth.security import hash_session_token

DEFAULT_SESSION_LIFETIME = timedelta(days=30)


class UserRow(BaseModel):
    id: UUID


class SessionRow(BaseModel):
    id: UUID


async def create_user(
    connection: AsyncConnection,
    *,
    provider: str = "local",
    provider_user_id: str | None = None,
    email: str | None = "person@example.com",
    name: str | None = "Test Person",
    avatar_url: str | None = None,
) -> UserRow:
    row = await fetch_one(
        connection,
        """
        insert into users (provider, provider_user_id, email, name, avatar_url)
        values (:provider, :provider_user_id, :email, :name, :avatar_url)
        returning id
        """,
        UserRow,
        {
            "provider": provider,
            # Random by default: two users created in the same test would
            # otherwise collide on the (provider, provider_user_id) key.
            "provider_user_id": provider_user_id or secrets.token_hex(8),
            "email": email,
            "name": name,
            "avatar_url": avatar_url,
        },
    )
    assert row is not None
    return row


async def create_session(
    connection: AsyncConnection,
    *,
    user_id: UUID,
    token: str | None = None,
    expires_at: datetime | None = None,
) -> tuple[SessionRow, str]:
    """Returns the created row alongside the raw token: the table only
    ever stores its hash (session-management spec), so a test that needs
    to present the session as a cookie has nowhere else to get it from.
    """
    token = token or secrets.token_urlsafe(32)
    expires_at = expires_at or (datetime.now(UTC) + DEFAULT_SESSION_LIFETIME)
    row = await fetch_one(
        connection,
        """
        insert into sessions (token_hash, user_id, expires_at)
        values (:token_hash, :user_id, :expires_at)
        returning id
        """,
        SessionRow,
        {
            "token_hash": hash_session_token(token),
            "user_id": user_id,
            "expires_at": expires_at,
        },
    )
    assert row is not None
    return row, token
