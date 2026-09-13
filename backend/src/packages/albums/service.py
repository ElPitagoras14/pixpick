from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncConnection

from src.database.utils import transaction
from src.exceptions import NotFoundError
from src.packages.albums import repository
from src.packages.albums.schemas import AlbumListRow, AlbumRecord
from src.storage.factory import storage_port
from src.storage.port import object_key


async def create_album(
    connection: AsyncConnection, *, owner_id: UUID, title: str, description: str | None
) -> AlbumRecord:
    return await repository.insert_album(
        connection, owner_id=owner_id, title=title, description=description
    )


async def list_albums(connection: AsyncConnection, *, owner_id: UUID) -> list[AlbumListRow]:
    return await repository.list_owned_albums(connection, owner_id=owner_id)


async def rename_album(
    connection: AsyncConnection,
    *,
    album_id: UUID,
    owner_id: UUID,
    title: str,
    description: str | None,
) -> AlbumRecord:
    album = await repository.rename_owned_album(
        connection, album_id=album_id, owner_id=owner_id, title=title, description=description
    )
    if album is None:
        raise NotFoundError()
    return album


async def delete_album(*, album_id: UUID, owner_id: UUID) -> None:
    """Its own transaction, committed before anything talks to storage
    (D6): a failure to delete the objects afterward leaves orphans, never
    a row pointing at an object that no longer exists. Deliberately not
    given the request's own connection -- see `database.utils.transaction`.
    """
    async with transaction() as connection:
        photo_ids = await repository.delete_owned_album_returning_photo_ids(
            connection, album_id=album_id, owner_id=owner_id
        )
    if photo_ids is None:
        raise NotFoundError()
    if photo_ids:
        keys = [object_key(album_id=str(album_id), photo_id=str(pid)) for pid in photo_ids]
        await storage_port.delete_objects(object_keys=keys)
