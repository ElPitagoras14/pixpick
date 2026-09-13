from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncConnection

from src.database.utils import transaction
from src.exceptions import ForbiddenError, NotFoundError
from src.packages.albums import repository
from src.storage.factory import storage_port
from src.storage.port import object_key

from .schemas import AlbumListRow, AlbumRecord


async def create_album(
    connection: AsyncConnection, *, owner_id: UUID, title: str, description: str | None
) -> AlbumRecord:
    album = await repository.insert_album(
        connection, owner_id=owner_id, title=title, description=description
    )
    # Crear un álbum hace miembro a su dueño (album-sharing spec): así el
    # dueño lo califica por el mismo camino que cualquier otra persona, y
    # es lo que hace de "mis álbumes" y "álbumes de los que soy miembro"
    # el mismo conjunto (D9).
    await repository.add_member(connection, album_id=album.id, user_id=owner_id)
    return album


async def list_albums(connection: AsyncConnection, *, user_id: UUID) -> list[AlbumListRow]:
    return await repository.list_member_albums(connection, user_id=user_id)


async def require_owned_album(
    connection: AsyncConnection, *, album_id: UUID, user_id: UUID
) -> AlbumRecord:
    """The album `user_id` owns, or raises (album-management spec, modified
    by add-share-and-swipe). An album that doesn't exist and one `user_id`
    has no relation to at all raise the same `NotFoundError` -- neither is
    distinguishable from the other. One `user_id` can see as a member, but
    doesn't own, raises `ForbiddenError` instead: a member already knows
    the album exists, so only ownership -- never mere visibility -- is
    what a 404 hides here.
    """
    album = await repository.get_owned_album(connection, album_id=album_id, owner_id=user_id)
    if album is not None:
        return album
    accessible = await repository.get_accessible_album(
        connection, album_id=album_id, user_id=user_id
    )
    if accessible is not None:
        raise ForbiddenError()
    raise NotFoundError()


async def rename_album(
    connection: AsyncConnection,
    *,
    album_id: UUID,
    user_id: UUID,
    title: str,
    description: str | None,
) -> AlbumRecord:
    await require_owned_album(connection, album_id=album_id, user_id=user_id)
    album = await repository.rename_owned_album(
        connection, album_id=album_id, owner_id=user_id, title=title, description=description
    )
    assert album is not None
    return album


async def delete_album(*, album_id: UUID, user_id: UUID) -> None:
    """Its own transaction, committed before anything talks to storage
    (D6): a failure to delete the objects afterward leaves orphans, never
    a row pointing at an object that no longer exists. Deliberately not
    given the request's own connection -- see `database.utils.transaction`.
    """
    async with transaction() as connection:
        await require_owned_album(connection, album_id=album_id, user_id=user_id)
        photo_ids = await repository.delete_owned_album_returning_photo_ids(
            connection, album_id=album_id, owner_id=user_id
        )
    assert photo_ids is not None
    if photo_ids:
        keys = [object_key(album_id=str(album_id), photo_id=str(pid)) for pid in photo_ids]
        await storage_port.delete_objects(object_keys=keys)
