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

# The condition each filter adds on top of "available photos of this
# album, left-joined with this person's own rating" (D1): "all" adds
# nothing, and the other three each pick one of the three states a
# rating column can be in. A key not in here is a programming error, not
# a request to handle leniently -- see `router.get_gallery` for where an
# unrecognized value from outside is turned into the default instead.
_RATING_FILTER_CONDITIONS: dict[RatingFilter, str] = {
    "all": "",
    "approved": "and r.approved = true",
    "rejected": "and r.approved = false",
    "unrated": "and r.approved is null",
}


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
    """One batch write for the whole grant (D12): together with the
    instance-wide advisory lock granting takes first (D1 in
    add-instance-quota, `quota.repository.acquire_instance_lock`), this
    is what keeps two batches granted at once -- for the same person or
    for two different ones -- from claiming the same position or, combined
    with the occupancy count and the account's and instance's usage, from
    slipping past any of the three limits together.
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


async def list_photos_with_rating(
    connection: AsyncConnection,
    *,
    album_id: UUID,
    user_id: UUID,
    rating_filter: RatingFilter = "all",
) -> list[PhotoWithRatingRow]:
    """The single query behind the rating sequence, the pending counter
    and the gallery's four filters (D1, rating-gallery spec): the
    album's available photos left-joined with the rating -- if any --
    that `user_id` gave each one, with one condition appended for the
    requested filter. Implemented once and parameterized instead of once
    per consumer, so what "pending" or "rejected" means can't drift
    between the sequence, the counter and the gallery (task 1.1, 1.2).
    """
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
    """The photos among `photo_ids` that belong to this album, if the
    album itself belongs to `owner_id` -- `None` if it doesn't, the same
    rule `album-management` uses (photo-upload spec). An id that isn't
    among the album's own photos is silently absent from the result
    rather than an error: there is nothing to verify a photo that was
    never granted against (D4).
    """
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


class _PhotoKey(BaseModel):
    """Just enough to derive an object key (`storage.port.object_key`) --
    shared by every query in this module that only needs to name an
    object, never the photo's other columns."""

    id: UUID
    album_id: UUID


async def expired_pending_photo_ids(connection: AsyncConnection) -> list[_PhotoKey]:
    """What reconciliation discards (D8): rows still not available whose
    grant has already expired -- an upload that will never complete."""
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
    """Every photo whose object is expected to exist, across every album
    (object-storage spec, D6 in add-cloud-media-adapters): what a
    provider migration has to have copied before the active provider
    changes. A pending upload has no confirmed object yet -- it's not
    this query's concern, reconciliation's own cleanup already handles
    it separately."""
    return await fetch_all(connection, "select id, album_id from available_photos", _PhotoKey)
