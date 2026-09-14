from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncConnection

from src.config import settings
from src.exceptions import NotFoundError
from src.packages.albums import repository as albums_repository

from . import repository
from .security import generate_share_token


def _build_link(token: str) -> str:
    """Built from the configured public address, never from the request's
    own scheme or host (album-sharing spec): nginx never sees TLS, the same
    reasoning `settings.public_url` already serves in `auth.router`.
    """
    return f"{settings.public_url.rstrip('/')}/a/{token}"


async def get_or_create_link(connection: AsyncConnection, *, album_id: UUID) -> str:
    """The album's current live link, generating the first one if it has
    none yet. Idempotent (task 2.1, D1): asking for it repeatedly -- as
    opening the share settings would -- never itself changes what's
    shared. Only `regenerate_link` and `revoke_link` do that.
    """
    existing = await repository.get_live_token(connection, album_id=album_id)
    if existing is not None:
        return _build_link(existing.token)
    token = generate_share_token()
    created = await repository.create_token(connection, album_id=album_id, token=token)
    return _build_link(created.token)


async def regenerate_link(connection: AsyncConnection, *, album_id: UUID) -> str:
    """Revokes the current live link, if any, and issues a new one in the
    same operation (album-sharing spec, D1): an album never sits without a
    live link, nor ever has two, between the two steps -- and neither
    changes who is already a member (see `repository.add_member`, never
    touched by revocation).
    """
    await repository.revoke_live_token(connection, album_id=album_id)
    token = generate_share_token()
    created = await repository.create_token(connection, album_id=album_id, token=token)
    return _build_link(created.token)


async def revoke_link(connection: AsyncConnection, *, album_id: UUID) -> None:
    await repository.revoke_live_token(connection, album_id=album_id)


async def enter(connection: AsyncConnection, *, token: str, user_id: UUID) -> UUID:
    """Validates the token and grants membership in the same operation
    (D4: this SHALL only ever be reached through a write, never a plain
    navigation -- see the router). A token that's unknown, revoked, or
    foreign to any album all raise the same `NotFoundError` (album-sharing
    spec). Entering twice with the same token is a no-op, not a second
    membership row (`repository.add_member` in the albums package is what
    makes that idempotent).
    """
    album_id = await repository.get_live_album_id_by_token(connection, token=token)
    if album_id is None:
        raise NotFoundError()
    await albums_repository.add_member(connection, album_id=album_id, user_id=user_id)
    return album_id
