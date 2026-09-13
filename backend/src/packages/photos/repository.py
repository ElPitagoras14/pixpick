from uuid import UUID

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncConnection

from src.database.client import fetch_all, fetch_val, fetch_val_or_none, write, write_many
from src.packages.photos.schemas import AvailablePhotoRow, PhotoRecord


async def count_occupied_slots(connection: AsyncConnection, *, album_id: UUID) -> int:
    """What counts against the album's maximum (D14): every available
    photo, plus every one still waiting on a grant that hasn't expired.
    A wait whose grant already expired can never complete, so it no
    longer holds a place -- without that exclusion, granting repeatedly
    without ever confirming would let a lot pass the maximum.
    """
    count = await fetch_val(
        connection,
        """
        select count(*) from photos
        where album_id = :album_id and (available or upload_expires_at > now())
        """,
        {"album_id": album_id},
    )
    return int(count)


async def next_position(connection: AsyncConnection, *, album_id: UUID) -> int:
    value = await fetch_val(
        connection,
        'select coalesce(max("position"), 0) from photos where album_id = :album_id',
        {"album_id": album_id},
    )
    return int(value) + 1


async def insert_pending_photos(connection: AsyncConnection, rows: list[dict]) -> None:
    """One batch write for the whole grant (D12): together with the lock
    `albums.repository.lock_owned_album_id` takes first, this is what
    keeps two batches granted for the same album at once from claiming
    the same position or, combined with the occupancy count, from
    slipping past the maximum together.
    """
    await write_many(
        connection,
        """
        insert into photos (
            id, album_id, "position", declared_content_type, declared_size,
            width, height, upload_expires_at
        )
        values (
            :id, :album_id, :position, :declared_content_type, :declared_size,
            :width, :height, :upload_expires_at
        )
        """,
        rows,
    )


async def list_available_photos(
    connection: AsyncConnection, *, album_id: UUID
) -> list[AvailablePhotoRow]:
    return await fetch_all(
        connection,
        """
        select id, "position", width, height
        from available_photos
        where album_id = :album_id
        order by "position" asc
        """,
        AvailablePhotoRow,
        {"album_id": album_id},
    )


async def get_owned_photos(
    connection: AsyncConnection, *, album_id: UUID, owner_id: UUID, photo_ids: list[UUID]
) -> list[PhotoRecord] | None:
    """The photos among `photo_ids` that belong to this album, if the
    album itself belongs to `owner_id` -- `None` if it doesn't, the same
    rule `album-management` uses (photo-upload spec). An id that isn't
    among the album's own photos is silently absent from the result
    rather than an error: there is nothing to verify a photo that was
    never granted against (D4).
    """
    owner_id_of_album = await fetch_val_or_none(
        connection, "select owner_id from albums where id = :album_id", {"album_id": album_id}
    )
    if owner_id_of_album is None or owner_id_of_album != owner_id:
        return None
    return await fetch_all(
        connection,
        """
        select id, album_id, "position", available, declared_content_type,
               declared_size, size, width, height, upload_expires_at
        from photos
        where album_id = :album_id and id = any(:photo_ids)
        """,
        PhotoRecord,
        {"album_id": album_id, "photo_ids": photo_ids},
    )


async def mark_photo_available(connection: AsyncConnection, *, photo_id: UUID, size: int) -> None:
    await write(
        connection,
        "update photos set available = true, size = :size where id = :photo_id",
        {"photo_id": photo_id, "size": size},
    )


async def delete_owned_photo(
    connection: AsyncConnection, *, album_id: UUID, owner_id: UUID, photo_id: UUID
) -> bool:
    """`True` if a photo owned (through its album) by `owner_id` was
    deleted; `False` for a foreign or nonexistent one -- both answered
    identically by the caller, the same rule `album-management` uses for
    the album itself."""
    deleted_id = await fetch_val_or_none(
        connection,
        """
        delete from photos
        using albums
        where photos.album_id = albums.id
          and photos.id = :photo_id
          and photos.album_id = :album_id
          and albums.owner_id = :owner_id
        returning photos.id
        """,
        {"photo_id": photo_id, "album_id": album_id, "owner_id": owner_id},
    )
    return deleted_id is not None


class _ExpiredPhotoRow(BaseModel):
    id: UUID
    album_id: UUID


async def expired_pending_photo_ids(connection: AsyncConnection) -> list[_ExpiredPhotoRow]:
    """What reconciliation discards (D8): rows still not available whose
    grant has already expired -- an upload that will never complete."""
    return await fetch_all(
        connection,
        "select id, album_id from photos where not available and upload_expires_at <= now()",
        _ExpiredPhotoRow,
    )


async def delete_photos_by_id(connection: AsyncConnection, *, photo_ids: list[UUID]) -> None:
    if not photo_ids:
        return
    await write(
        connection, "delete from photos where id = any(:photo_ids)", {"photo_ids": photo_ids}
    )
