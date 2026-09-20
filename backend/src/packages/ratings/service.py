from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncConnection

from src.exceptions import NotFoundError
from src.packages.photos import repository as photos_repository

from . import repository
from .schemas import AlbumStats, PendingPhotoRow, PhotoStats, RatingRecord


async def list_pending(
    connection: AsyncConnection, *, album_id: UUID, user_id: UUID
) -> list[PendingPhotoRow]:
    return await repository.list_pending_photos(connection, album_id=album_id, user_id=user_id)


async def count_pending(connection: AsyncConnection, *, album_id: UUID, user_id: UUID) -> int:
    """The same comparison `list_pending` runs: never its own query, so the
    counter and the sequence can never say two different things about the
    same person and album.
    """
    rows = await repository.list_pending_photos(connection, album_id=album_id, user_id=user_id)
    return len(rows)


async def get_album_stats(connection: AsyncConnection, *, album_id: UUID) -> AlbumStats:
    """Starts from the album's available photos, not from its ratings: a
    photo nobody rated yet still has to appear, at zero, and starting from
    ratings would leave it out. The summary is built from the very same rows
    the per-photo counts are, in one pass, so it can never disagree with
    their sum.
    """
    available = await photos_repository.list_available_photos(connection, album_id=album_id)
    ratings = await repository.list_album_ratings(connection, album_id=album_id)

    counts = {photo.id: {"approved": 0, "rejected": 0} for photo in available}
    participants: set[UUID] = set()
    for rating in ratings:
        participants.add(rating.user_id)
        bucket = counts[rating.photo_id]
        bucket["approved" if rating.approved else "rejected"] += 1

    photos = [
        PhotoStats(
            photo_id=photo.id,
            approved_count=counts[photo.id]["approved"],
            rejected_count=counts[photo.id]["rejected"],
        )
        for photo in available
    ]
    return AlbumStats(photos=photos, participant_count=len(participants), rating_count=len(ratings))


async def rate_photo(
    connection: AsyncConnection,
    *,
    album_id: UUID,
    photo_id: UUID,
    user_id: UUID,
    approved: bool,
) -> RatingRecord:
    """Membership is already checked by the router's own
    `get_accessible_album` dependency; what's left here is that the photo
    itself belongs to this album and is actually available -- a foreign or
    not-yet-available photo id SHALL respond exactly like a nonexistent one,
    and SHALL NOT register a rating.
    """
    if not await repository.photo_is_available_in_album(
        connection, album_id=album_id, photo_id=photo_id
    ):
        raise NotFoundError()
    return await repository.upsert_rating(
        connection, photo_id=photo_id, user_id=user_id, approved=approved
    )
