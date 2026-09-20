from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncConnection

from src.database.dependencies import get_connection
from src.exceptions import NotFoundError
from src.packages.auth.dependencies import get_current_user
from src.packages.auth.schemas import UserRecord

from . import repository, service
from .schemas import AlbumDetailRow, AlbumRecord


async def get_owned_album(
    album_id: UUID,
    user: UserRecord = Depends(get_current_user),
    connection: AsyncConnection = Depends(get_connection),
) -> AlbumRecord:
    """How an endpoint requires an album the caller *owns*. A missing album
    and one the caller has no relation to both raise `NotFoundError`; one
    they can see as a member raises `ForbiddenError`, since hiding what a
    member already knows exists protects nothing."""
    return await service.require_owned_album(connection, album_id=album_id, user_id=user.id)


async def get_accessible_album(
    album_id: UUID,
    user: UserRecord = Depends(get_current_user),
    connection: AsyncConnection = Depends(get_connection),
) -> AlbumDetailRow:
    """How an endpoint requires an album the caller can merely *see*: its
    owner, or any member. A missing album and one they have no relation to
    both raise `NotFoundError`."""
    album = await repository.get_accessible_album(connection, album_id=album_id, user_id=user.id)
    if album is None:
        raise NotFoundError()
    return album
