from uuid import UUID

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncConnection

from src.database.client import fetch_all, fetch_val, fetch_val_or_none, write, write_many
from src.packages.albums.repository import ACTIVE_CONDITION, retention_params

from .schemas import (
    AvailablePhotoRow,
    PhotoRecord,
    PhotoWithRatingRow,
    RatingFilter,
)

# What each filter adds to the left join with this person's rating. A key
# missing here is a programming error; `router.get_gallery` is where an
# unrecognized value from outside becomes the default instead.
_RATING_FILTER_CONDITIONS: dict[RatingFilter, str] = {
    "all": "",
    "approved": "and r.approved = true",
    "rejected": "and r.approved = false",
    "unrated": "and r.approved is null",
}


async def count_occupied_slots(connection: AsyncConnection, *, album_id: UUID) -> int:
    """Every available photo, plus every one waiting on a grant that hasn't
    expired. Without that exclusion, granting repeatedly and never
    confirming would walk past the maximum."""
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
    """One write for the whole grant. With the advisory lock granting takes
    first (`quota.repository.acquire_instance_lock`), this is what keeps two
    concurrent batches from claiming a position or a limit twice."""
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


async def list_photos_with_rating(
    connection: AsyncConnection,
    *,
    album_id: UUID,
    user_id: UUID,
    rating_filter: RatingFilter = "all",
) -> list[PhotoWithRatingRow]:
    """The one query behind the rating sequence, the pending counter and the
    gallery: available photos left-joined with `user_id`'s rating, plus the
    filter's own condition. Parameterized rather than written per consumer,
    so what "unrated" means can't drift between the three."""
    condition = _RATING_FILTER_CONDITIONS[rating_filter]
    return await fetch_all(
        connection,
        f"""
        select p.id, p."position", p.width, p.height, r.approved
        from available_photos p
        left join photo_ratings r on r.photo_id = p.id and r.user_id = :user_id
        where p.album_id = :album_id
        {condition}
        order by p."position" asc
        """,
        PhotoWithRatingRow,
        {"album_id": album_id, "user_id": user_id},
    )


async def get_owned_photos(
    connection: AsyncConnection, *, album_id: UUID, owner_id: UUID, photo_ids: list[UUID]
) -> list[PhotoRecord] | None:
    """`None` when the album isn't `owner_id`'s, the same rule the album
    itself follows. An id that isn't one of its photos is absent from the
    result rather than an error."""
    owner_id_of_album = await fetch_val_or_none(
        connection,
        f"select a.owner_id from albums a where a.id = :album_id and {ACTIVE_CONDITION}",
        {"album_id": album_id, **retention_params()},
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
    """`False` for both a foreign photo and a nonexistent one, the same rule
    the album itself follows."""
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


class _PhotoKey(BaseModel):
    """Just enough to derive an object key (`storage.port.object_key`)."""

    id: UUID
    album_id: UUID


async def expired_pending_photo_ids(connection: AsyncConnection) -> list[_PhotoKey]:
    """Uploads that will never complete: not available, grant expired."""
    return await fetch_all(
        connection,
        "select id, album_id from photos where not available and upload_expires_at <= now()",
        _PhotoKey,
    )


async def delete_photos_by_id(connection: AsyncConnection, *, photo_ids: list[UUID]) -> None:
    if not photo_ids:
        return
    await write(
        connection, "delete from photos where id = any(:photo_ids)", {"photo_ids": photo_ids}
    )


async def all_available_photo_keys(connection: AsyncConnection) -> list[_PhotoKey]:
    """Every photo whose object is expected to exist: what a provider
    migration has to have copied first. A pending upload has no confirmed
    object yet, so it is not counted here."""
    return await fetch_all(connection, "select id, album_id from available_photos", _PhotoKey)
