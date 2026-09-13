from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncConnection

from src.exceptions import NotFoundError
from src.packages.ratings import repository
from src.packages.ratings.schemas import PendingPhotoRow, RatingRecord


async def list_pending(
    connection: AsyncConnection, *, album_id: UUID, user_id: UUID
) -> list[PendingPhotoRow]:
    return await repository.list_pending_photos(connection, album_id=album_id, user_id=user_id)


async def count_pending(connection: AsyncConnection, *, album_id: UUID, user_id: UUID) -> int:
    """The same comparison `list_pending` runs (D2, task 3.3): never its
    own query, so the counter and the sequence can never say two
    different things about the same person and album.
    """
    rows = await repository.list_pending_photos(connection, album_id=album_id, user_id=user_id)
    return len(rows)


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
    not-yet-available photo id SHALL respond exactly like a nonexistent
    one (photo-rating spec), and SHALL NOT register a rating.
    """
    if not await repository.photo_is_available_in_album(
        connection, album_id=album_id, photo_id=photo_id
    ):
        raise NotFoundError()
    return await repository.upsert_rating(
        connection, photo_id=photo_id, user_id=user_id, approved=approved
    )
