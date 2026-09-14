from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Query
from pydantic import Field
from sqlalchemy.ext.asyncio import AsyncConnection

from src.database.dependencies import get_connection
from src.models import ApiModel
from src.packages.albums.dependencies import get_accessible_album, get_owned_album
from src.packages.albums.schemas import AlbumDetailRow, AlbumRecord
from src.packages.auth.dependencies import get_current_user
from src.packages.auth.schemas import UserRecord
from src.responses import Envelope

from . import service
from .config import MAX_BATCH_SIZE
from .responses import (
    ConfirmationResultResponse,
    GalleryResponse,
    PhotoGrantResponse,
    PhotoResponse,
)
from .schemas import GrantFileInput, RatingFilter
from .warmup import warm_up_variants

router = APIRouter(prefix="/albums/{album_id}/photos")


class GrantPhotoRequest(ApiModel):
    content_type: str
    size: int
    width: int | None = None
    height: int | None = None

    def to_input(self) -> GrantFileInput:
        return GrantFileInput(
            content_type=self.content_type,
            size=self.size,
            width=self.width,
            height=self.height,
        )


class GrantPhotosRequest(ApiModel):
    # The batch ceiling (D13) is enforced here, before anything reaches
    # the service: a bigger selection is the client's own job to split
    # into successive batches, never this endpoint's to accept.
    files: Annotated[list[GrantPhotoRequest], Field(min_length=1, max_length=MAX_BATCH_SIZE)]


class ConfirmPhotosRequest(ApiModel):
    photo_ids: Annotated[list[UUID], Field(min_length=1)]


@router.get("")
async def list_photos(
    # A member can view the grid too, not only the owner (album-management
    # spec, modified by add-share-and-swipe) -- unlike granting, confirming
    # or deleting a photo below, which stay owner-only.
    album: AlbumDetailRow = Depends(get_accessible_album),
    connection: AsyncConnection = Depends(get_connection),
) -> Envelope[list[PhotoResponse]]:
    rows = await service.list_photos(connection, album_id=album.id)
    return Envelope(data=[PhotoResponse.from_row(row, album_id=album.id) for row in rows])


@router.get("/gallery")
async def get_gallery(
    # A closed set of four values (rating-gallery spec): an out-of-set
    # value is a malformed request from something other than this
    # project's own frontend, which never sends one -- its own route
    # already resolved an unrecognized filter to the default before this
    # was ever called (D9). This dependency SHALL NOT be leniently
    # coerced the same way.
    rating_filter: RatingFilter = Query("all", alias="filter"),
    album: AlbumDetailRow = Depends(get_accessible_album),
    user: UserRecord = Depends(get_current_user),
    connection: AsyncConnection = Depends(get_connection),
) -> Envelope[GalleryResponse]:
    result = await service.get_gallery(
        connection, album_id=album.id, user_id=user.id, rating_filter=rating_filter
    )
    return Envelope(data=GalleryResponse.from_result(result, album_id=album.id))


@router.post("/grants")
async def grant_photos(
    body: GrantPhotosRequest,
    album: AlbumRecord = Depends(get_owned_album),
    connection: AsyncConnection = Depends(get_connection),
) -> Envelope[list[PhotoGrantResponse]]:
    grants = await service.grant_batch(
        connection,
        album_id=album.id,
        owner_id=album.owner_id,
        files=[file.to_input() for file in body.files],
    )
    return Envelope(
        data=[
            PhotoGrantResponse.from_grant(photo_id=photo_id, position=position, grant=grant)
            for photo_id, position, grant in grants
        ]
    )


@router.post("/confirm")
async def confirm_photos(
    album_id: UUID,
    body: ConfirmPhotosRequest,
    background_tasks: BackgroundTasks,
    user: UserRecord = Depends(get_current_user),
) -> Envelope[list[ConfirmationResultResponse]]:
    # Deliberately not `Depends(get_connection)`: confirming verifies
    # each photo against its real object in storage, a network call that
    # SHALL NOT happen while any transaction sits open (D6) -- see
    # `service.confirm_batch`.
    results, warm_up_keys = await service.confirm_batch(
        album_id=album_id, user_id=user.id, photo_ids=body.photo_ids
    )
    if warm_up_keys:
        # After responding, never before (D7, task 4.5): scheduled here
        # so it runs once the response is on its way, not folded into
        # the awaited work above.
        background_tasks.add_task(warm_up_variants, warm_up_keys)
    return Envelope(data=[ConfirmationResultResponse.from_outcome(r) for r in results])


@router.delete("/{photo_id}")
async def delete_photo(
    album_id: UUID,
    photo_id: UUID,
    user: UserRecord = Depends(get_current_user),
) -> Envelope[None]:
    # Deliberately not `Depends(get_connection)`: see `service.delete_photo`.
    await service.delete_photo(album_id=album_id, user_id=user.id, photo_id=photo_id)
    return Envelope(data=None)
