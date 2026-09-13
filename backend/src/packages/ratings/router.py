from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncConnection

from src.database.dependencies import get_connection
from src.models import ApiModel
from src.packages.albums.dependencies import get_accessible_album
from src.packages.albums.schemas import AlbumDetailRow
from src.packages.auth.dependencies import get_current_user
from src.packages.auth.schemas import UserRecord
from src.packages.ratings import service
from src.packages.ratings.responses import PendingPhotoResponse, RatingResponse
from src.responses import Envelope

# Rating is open to any member, not only the owner (photo-rating spec):
# `get_accessible_album` is the same dependency `photos.router` uses for
# viewing the grid.
router = APIRouter(prefix="/albums/{album_id}")


class RatePhotoRequest(ApiModel):
    approved: bool


@router.get("/pending")
async def list_pending(
    album: AlbumDetailRow = Depends(get_accessible_album),
    user: UserRecord = Depends(get_current_user),
    connection: AsyncConnection = Depends(get_connection),
) -> Envelope[list[PendingPhotoResponse]]:
    rows = await service.list_pending(connection, album_id=album.id, user_id=user.id)
    return Envelope(data=[PendingPhotoResponse.from_row(row, album_id=album.id) for row in rows])


@router.post("/photos/{photo_id}/rating")
async def rate_photo(
    photo_id: UUID,
    body: RatePhotoRequest,
    album: AlbumDetailRow = Depends(get_accessible_album),
    user: UserRecord = Depends(get_current_user),
    connection: AsyncConnection = Depends(get_connection),
) -> Envelope[RatingResponse]:
    rating = await service.rate_photo(
        connection,
        album_id=album.id,
        photo_id=photo_id,
        user_id=user.id,
        approved=body.approved,
    )
    return Envelope(data=RatingResponse.from_record(rating))
