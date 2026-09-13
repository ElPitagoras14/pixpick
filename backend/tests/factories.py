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

from src.database.client import fetch_one, fetch_val, write
from src.packages.auth.security import hash_session_token

DEFAULT_SESSION_LIFETIME = timedelta(days=30)
DEFAULT_UPLOAD_GRANT_LIFETIME = timedelta(minutes=15)


class UserRow(BaseModel):
    id: UUID


class SessionRow(BaseModel):
    id: UUID


class AlbumRow(BaseModel):
    id: UUID


class PhotoRow(BaseModel):
    id: UUID


class ShareTokenRow(BaseModel):
    id: UUID


class RatingRow(BaseModel):
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


async def create_album(
    connection: AsyncConnection,
    *,
    owner_id: UUID,
    title: str = "Test Album",
    description: str | None = None,
) -> AlbumRow:
    """Also makes `owner_id` a member (album-sharing spec: creating an
    album does this in production too), so a test that only cares about
    ownership never has to declare the membership its own invariants
    already assume.
    """
    row = await fetch_one(
        connection,
        """
        insert into albums (owner_id, title, description)
        values (:owner_id, :title, :description)
        returning id
        """,
        AlbumRow,
        {"owner_id": owner_id, "title": title, "description": description},
    )
    assert row is not None
    await create_membership(connection, album_id=row.id, user_id=owner_id)
    return row


async def create_photo(
    connection: AsyncConnection,
    *,
    album_id: UUID,
    position: int | None = None,
    available: bool = True,
    declared_content_type: str = "image/jpeg",
    declared_size: int = 1_000,
    size: int | None = None,
    width: int | None = None,
    height: int | None = None,
    upload_expires_at: datetime | None = None,
) -> PhotoRow:
    """Available by default -- most tests exercise a photo that already
    made it through the upload cycle. Pass `available=False` for the
    pending/abandoned variant the upload flow itself produces.
    """
    if position is None:
        position = await fetch_val(
            connection,
            'select coalesce(max("position"), 0) + 1 from photos where album_id = :album_id',
            {"album_id": album_id},
        )
    if available and size is None:
        size = declared_size
    if upload_expires_at is None:
        upload_expires_at = datetime.now(UTC) + DEFAULT_UPLOAD_GRANT_LIFETIME
    row = await fetch_one(
        connection,
        """
        insert into photos (
            album_id, "position", available, declared_content_type,
            declared_size, size, width, height, upload_expires_at
        )
        values (
            :album_id, :position, :available, :declared_content_type,
            :declared_size, :size, :width, :height, :upload_expires_at
        )
        returning id
        """,
        PhotoRow,
        {
            "album_id": album_id,
            "position": position,
            "available": available,
            "declared_content_type": declared_content_type,
            "declared_size": declared_size,
            "size": size,
            "width": width,
            "height": height,
            "upload_expires_at": upload_expires_at,
        },
    )
    assert row is not None
    return row


async def create_share_token(
    connection: AsyncConnection,
    *,
    album_id: UUID,
    token: str | None = None,
    revoked_at: datetime | None = None,
) -> tuple[ShareTokenRow, str]:
    """Returns the created row alongside the raw token, mirroring
    `create_session` -- unlike a session token, this one is stored in
    plain text (see the migration's own comment on `share_tokens`), but a
    test still gets it back this way for symmetry with the rest of this
    module and so it never has to know the storage detail either.
    """
    token = token or secrets.token_urlsafe(32)
    row = await fetch_one(
        connection,
        """
        insert into share_tokens (album_id, token, revoked_at)
        values (:album_id, :token, :revoked_at)
        returning id
        """,
        ShareTokenRow,
        {"album_id": album_id, "token": token, "revoked_at": revoked_at},
    )
    assert row is not None
    return row, token


async def create_membership(connection: AsyncConnection, *, album_id: UUID, user_id: UUID) -> None:
    """Idempotent, like the repository function it mirrors (album-sharing
    spec): declaring the same membership twice in a test's setup is
    harmless."""
    await write(
        connection,
        """
        insert into album_members (album_id, user_id)
        values (:album_id, :user_id)
        on conflict (album_id, user_id) do nothing
        """,
        {"album_id": album_id, "user_id": user_id},
    )


async def create_rating(
    connection: AsyncConnection, *, photo_id: UUID, user_id: UUID, approved: bool = True
) -> RatingRow:
    row = await fetch_one(
        connection,
        """
        insert into photo_ratings (photo_id, user_id, approved)
        values (:photo_id, :user_id, :approved)
        returning id
        """,
        RatingRow,
        {"photo_id": photo_id, "user_id": user_id, "approved": approved},
    )
    assert row is not None
    return row
