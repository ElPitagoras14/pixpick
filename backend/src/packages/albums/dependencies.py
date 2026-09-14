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
    """The declared way any endpoint -- in this package, or in `photos` and
    `shares`, which import this same dependency -- requires an album the
    caller *owns* (album-management spec, modified by add-share-and-swipe):
    an album that doesn't exist and one the caller has no relation to at
    all raise the same `NotFoundError`; one the caller can see as a member,
    but doesn't own, raises `ForbiddenError` instead -- its existence is
    already known to a member, so hiding it here protects nothing.
    """
    return await service.require_owned_album(connection, album_id=album_id, user_id=user.id)


async def get_accessible_album(
    album_id: UUID,
    user: UserRecord = Depends(get_current_user),
    connection: AsyncConnection = Depends(get_connection),
) -> AlbumDetailRow:
    """The declared way any endpoint -- in this package, or in `photos` and
    `ratings`, which import this same dependency -- requires an album the
    caller can merely *see*: its owner, or any member (album-management
    spec, modified by add-share-and-swipe). An album that doesn't exist
    and one the caller has no relation to at all raise the same
    `NotFoundError`.
    """
    album = await repository.get_accessible_album(connection, album_id=album_id, user_id=user.id)
    if album is None:
        raise NotFoundError()
    return album
