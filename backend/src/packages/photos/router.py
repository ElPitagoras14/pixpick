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
from .config import MAX_BATCH_SIZE, MAX_DIMENSION, MAX_FILE_SIZE
from .responses import (
    ConfirmationResultResponse,
    GalleryResponse,
    GrantBatchResponse,
    PhotoResponse,
)
from .schemas import GrantFileInput, RatingFilter
from .warmup import warm_up_variants

router = APIRouter(prefix="/albums/{album_id}/photos")


class GrantPhotoRequest(ApiModel):
    content_type: str
    # A non-positive size would grow what's available instead of consuming
    # it.
    size: Annotated[int, Field(gt=0, le=MAX_FILE_SIZE)]
    width: Annotated[int, Field(gt=0, le=MAX_DIMENSION)] | None = None
    height: Annotated[int, Field(gt=0, le=MAX_DIMENSION)] | None = None

    def to_input(self) -> GrantFileInput:
        return GrantFileInput(
            content_type=self.content_type,
            size=self.size,
            width=self.width,
            height=self.height,
        )


class GrantPhotosRequest(ApiModel):
    # Enforced before anything reaches the service: splitting a bigger
    # selection into batches is the client's job.
    files: Annotated[list[GrantPhotoRequest], Field(min_length=1, max_length=MAX_BATCH_SIZE)]


class ConfirmPhotosRequest(ApiModel):
    # Same ceiling as granting: each confirmation costs a storage lookup, so
    # the work one request triggers stays bounded.
    photo_ids: Annotated[list[UUID], Field(min_length=1, max_length=MAX_BATCH_SIZE)]


@router.get("")
async def list_photos(
    # A member can view the grid too, unlike granting, confirming and
    # deleting below.
    album: AlbumDetailRow = Depends(get_accessible_album),
    connection: AsyncConnection = Depends(get_connection),
) -> Envelope[list[PhotoResponse]]:
    rows = await service.list_photos(connection, album_id=album.id)
    return Envelope(data=[PhotoResponse.from_row(row, album_id=album.id) for row in rows])


@router.get("/gallery")
async def get_gallery(
    # Not coerced the way the route does it: by the time a request reaches
    # here the frontend has already resolved an unrecognized filter to the
    # default, so an out-of-set value is a malformed request.
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
) -> Envelope[GrantBatchResponse]:
    # Succeeds even when nothing was granted: running out of room is a fact
    # about state, not a malformed request, so the answer is per file.
    result = await service.grant_batch(
        connection,
        album_id=album.id,
        owner_id=album.owner_id,
        files=[file.to_input() for file in body.files],
    )
    return Envelope(data=GrantBatchResponse.from_result(result))


@router.post("/confirm")
async def confirm_photos(
    album_id: UUID,
    body: ConfirmPhotosRequest,
    background_tasks: BackgroundTasks,
    user: UserRecord = Depends(get_current_user),
) -> Envelope[list[ConfirmationResultResponse]]:
    # Deliberately not `Depends(get_connection)`: confirming makes a network
    # call per photo, which must not happen with a transaction open.
    results, warm_up_keys = await service.confirm_batch(
        album_id=album_id, user_id=user.id, photo_ids=body.photo_ids
    )
    if warm_up_keys:
        # Scheduled, so it runs once the response is on its way.
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
