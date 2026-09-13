from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncConnection

from src.database.dependencies import get_connection
from src.exceptions import NotFoundError
from src.packages.albums import repository
from src.packages.albums.schemas import AlbumRecord
from src.packages.auth.dependencies import get_current_user
from src.packages.auth.schemas import UserRecord


async def get_owned_album(
    album_id: UUID,
    user: UserRecord = Depends(get_current_user),
    connection: AsyncConnection = Depends(get_connection),
) -> AlbumRecord:
    """The declared way any endpoint -- in this package or in `photos`,
    which imports this same dependency -- requires an album the caller
    owns (album-management spec): an album that doesn't exist and one
    that belongs to someone else raise the exact same `NotFoundError`, so
    neither confirms the other to the caller.
    """
    album = await repository.get_owned_album(connection, album_id=album_id, owner_id=user.id)
    if album is None:
        raise NotFoundError()
    return album
