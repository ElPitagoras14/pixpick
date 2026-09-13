from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import field_validator
from sqlalchemy.ext.asyncio import AsyncConnection

from src.database.dependencies import get_connection
from src.models import ApiModel
from src.packages.albums import service
from src.packages.auth.dependencies import get_current_user
from src.packages.auth.schemas import UserRecord
from src.responses import Envelope

from .dependencies import get_accessible_album
from .responses import AlbumDetailResponse, AlbumResponse, AlbumSummaryResponse
from .schemas import AlbumDetailRow

router = APIRouter(prefix="/albums")


def _validate_title(value: str) -> str:
    """Shared by create and rename (album-management spec): a value made
    only of whitespace carries no content and SHALL be rejected exactly
    like an absent one, naming the same field either way.
    """
    if not value.strip():
        raise ValueError("title is required")
    return value


class CreateAlbumRequest(ApiModel):
    title: str
    description: str | None = None

    _validate_title = field_validator("title")(_validate_title)


class RenameAlbumRequest(ApiModel):
    title: str
    description: str | None = None

    _validate_title = field_validator("title")(_validate_title)


@router.post("")
async def create_album(
    body: CreateAlbumRequest,
    user: UserRecord = Depends(get_current_user),
    connection: AsyncConnection = Depends(get_connection),
) -> Envelope[AlbumResponse]:
    album = await service.create_album(
        connection, owner_id=user.id, title=body.title, description=body.description
    )
    return Envelope(data=AlbumResponse.from_record(album))


@router.get("")
async def list_albums(
    user: UserRecord = Depends(get_current_user),
    connection: AsyncConnection = Depends(get_connection),
) -> Envelope[list[AlbumSummaryResponse]]:
    rows = await service.list_albums(connection, user_id=user.id)
    return Envelope(data=[AlbumSummaryResponse.from_row(row) for row in rows])


@router.get("/{album_id}")
async def get_album(
    album: AlbumDetailRow = Depends(get_accessible_album),
    user: UserRecord = Depends(get_current_user),
) -> Envelope[AlbumDetailResponse]:
    return Envelope(data=AlbumDetailResponse.from_row(album, viewer_id=user.id))


@router.patch("/{album_id}")
async def rename_album(
    album_id: UUID,
    body: RenameAlbumRequest,
    user: UserRecord = Depends(get_current_user),
    connection: AsyncConnection = Depends(get_connection),
) -> Envelope[AlbumResponse]:
    album = await service.rename_album(
        connection,
        album_id=album_id,
        user_id=user.id,
        title=body.title,
        description=body.description,
    )
    return Envelope(data=AlbumResponse.from_record(album))


@router.delete("/{album_id}")
async def delete_album(
    album_id: UUID,
    user: UserRecord = Depends(get_current_user),
) -> Envelope[None]:
    # Deliberately not `Depends(get_connection)`: deleting an album also
    # deletes its photos' objects, a network call that SHALL happen only
    # once the row deletion has already committed (D6) -- see
    # `service.delete_album`.
    await service.delete_album(album_id=album_id, user_id=user.id)
    return Envelope(data=None)
