from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncConnection

from src.config import settings
from src.exceptions import NotFoundError
from src.packages.albums import repository as albums_repository

from . import repository
from .security import generate_share_token


def _build_link(token: str) -> str:
    """From the configured public address, never the request's own scheme or
    host: nginx never sees TLS."""
    return f"{settings.public_url.rstrip('/')}/a/{token}"


async def get_or_create_link(connection: AsyncConnection, *, album_id: UUID) -> str:
    """The album's live link, generating the first one if there is none.
    Idempotent: only `regenerate_link` and `revoke_link` change what is
    shared."""
    existing = await repository.get_live_token(connection, album_id=album_id)
    if existing is not None:
        return _build_link(existing.token)
    token = generate_share_token()
    created = await repository.create_token(connection, album_id=album_id, token=token)
    return _build_link(created.token)


async def regenerate_link(connection: AsyncConnection, *, album_id: UUID) -> str:
    """Revoke and reissue in one operation, so an album never sits without a
    live link or with two. Neither step touches who is already a member."""
    await repository.revoke_live_token(connection, album_id=album_id)
    token = generate_share_token()
    created = await repository.create_token(connection, album_id=album_id, token=token)
    return _build_link(created.token)


async def revoke_link(connection: AsyncConnection, *, album_id: UUID) -> None:
    await repository.revoke_live_token(connection, album_id=album_id)


async def enter(connection: AsyncConnection, *, token: str, user_id: UUID) -> UUID:
    """Validates the token and grants membership in one operation. Unknown,
    revoked, foreign and expired all raise the same `NotFoundError`.
    Entering twice is a no-op, not a second membership row."""
    album_id = await repository.get_live_album_id_by_token(connection, token=token)
    if album_id is None:
        raise NotFoundError()
    # An expired album's row and token can both still exist, so the token
    # alone isn't enough: expired has to answer like never-existed.
    if not await albums_repository.album_exists(connection, album_id=album_id):
        raise NotFoundError()
    await albums_repository.add_member(connection, album_id=album_id, user_id=user_id)
    return album_id
