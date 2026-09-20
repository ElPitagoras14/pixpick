from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncConnection

from src.database.client import fetch_all, fetch_one, fetch_val
from src.packages.photos import repository as photos_repository

from .schemas import AlbumRatingRow, PendingPhotoRow, RatingRecord


async def list_pending_photos(
    connection: AsyncConnection, *, album_id: UUID, user_id: UUID
) -> list[PendingPhotoRow]:
    """The album's available photos `user_id` hasn't rated yet, in album
    order. Delegates to the query the gallery's "unrated" filter uses, so
    the sequence, the counter and the gallery can't drift apart on what
    unrated means."""
    rows = await photos_repository.list_photos_with_rating(
        connection, album_id=album_id, user_id=user_id, rating_filter="unrated"
    )
    return [
        PendingPhotoRow(id=row.id, position=row.position, width=row.width, height=row.height)
        for row in rows
    ]


async def photo_is_available_in_album(
    connection: AsyncConnection, *, album_id: UUID, photo_id: UUID
) -> bool:
    """What lets `rate_photo` answer a foreign or unavailable photo exactly
    like a nonexistent one."""
    return await fetch_val(
        connection,
        """
        select exists(
            select 1 from available_photos where id = :photo_id and album_id = :album_id
        )
        """,
        {"photo_id": photo_id, "album_id": album_id},
    )


async def list_album_ratings(
    connection: AsyncConnection, *, album_id: UUID
) -> list[AlbumRatingRow]:
    """One row per person's decision on one photo. Joined against
    `available_photos`, so a rating on a photo whose upload never completed
    can't surface. `service.get_album_stats` builds both the per-photo
    counts and the album summary from this one pass."""
    return await fetch_all(
        connection,
        """
        select r.photo_id, r.user_id, r.approved
        from photo_ratings r
        join available_photos p on p.id = r.photo_id
        where p.album_id = :album_id
        """,
        AlbumRatingRow,
        {"album_id": album_id},
    )


async def upsert_rating(
    connection: AsyncConnection, *, photo_id: UUID, user_id: UUID, approved: bool
) -> RatingRecord:
    """One statement resolving the conflict on the schema's unique key,
    never a read that decides between insert and update first: that leaves
    no window for two concurrent requests to both decide on an insert."""
    row = await fetch_one(
        connection,
        """
        insert into photo_ratings (photo_id, user_id, approved)
        values (:photo_id, :user_id, :approved)
        on conflict (photo_id, user_id) do update set approved = excluded.approved
        returning id, photo_id, user_id, approved, created_at, updated_at
        """,
        RatingRecord,
        {"photo_id": photo_id, "user_id": user_id, "approved": approved},
    )
    assert row is not None
    return row
