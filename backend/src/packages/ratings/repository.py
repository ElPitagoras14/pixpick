from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncConnection

from src.database.client import fetch_all, fetch_one, fetch_val
from src.packages.ratings.schemas import PendingPhotoRow, RatingRecord


async def list_pending_photos(
    connection: AsyncConnection, *, album_id: UUID, user_id: UUID
) -> list[PendingPhotoRow]:
    """The one comparison lo pendiente is (D2, photo-rating spec): the
    album's available photos that `user_id` hasn't rated yet, in the
    album's own order. Implemented once and used both for the rating
    sequence and, by `service.count_pending`, for the counter -- never a
    second implementation of the same comparison that could drift from
    this one. Compares against `available_photos` (add-albums-and-upload),
    so a photo that isn't available yet is never pending for anyone,
    without this query having to exclude it explicitly.
    """
    return await fetch_all(
        connection,
        """
        select p.id, p."position", p.width, p.height
        from available_photos p
        where p.album_id = :album_id
          and not exists (
              select 1 from photo_ratings r
              where r.photo_id = p.id and r.user_id = :user_id
          )
        order by p."position" asc
        """,
        PendingPhotoRow,
        {"album_id": album_id, "user_id": user_id},
    )


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
