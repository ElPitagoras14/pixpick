from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncConnection

from src.database.client import fetch_all, fetch_one, fetch_val
from src.packages.photos import repository as photos_repository

from .schemas import AlbumRatingRow, PendingPhotoRow, RatingRecord


async def list_pending_photos(
    connection: AsyncConnection, *, album_id: UUID, user_id: UUID
) -> list[PendingPhotoRow]:
    """The one comparison lo pendiente is (D1, D2, photo-rating and
    rating-gallery specs): the album's available photos that `user_id`
    hasn't rated yet, in the album's own order. Delegates to the same
    query the gallery's own "unrated" filter uses, filtered here in SQL
    rather than fetched whole and filtered in Python -- this endpoint
    only ever needs the unrated ones, never the other three. Used both
    for the rating sequence and, by `service.count_pending`, for the
    counter -- never a second implementation of the same comparison that
    could drift from this one or from the gallery's.
    """
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
    """Whether `photo_id` is one of `album_id`'s available photos -- the
    same check `rate_photo` needs to answer a foreign or unavailable photo
    exactly like a nonexistent one (photo-rating spec)."""
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
    """Every rating cast on one of the album's available photos (D3,
    album-stats spec), one row per person's decision on one photo. Joins
    against `available_photos` and not `photos` directly, so a rating on
    a photo whose upload never completed -- which the schema's own
    cascade never leaves behind anyway -- still couldn't surface here.
    `service.get_album_stats` builds both the per-photo counts and the
    album summary from this one query, in a single pass over these rows.
    """
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
    """A single statement that resolves the conflict on the schema's own
    unique key (D3, photo-rating spec): never a read that decides between
    insert and update first. That's what makes retrying safe under a race
    between two requests from the same person -- there's no window in
    which both could decide an insert is the right thing to do.
    """
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
