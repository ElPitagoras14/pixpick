from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncConnection

from src.database.dependencies import get_connection
from src.packages.albums.dependencies import get_owned_album
from src.packages.albums.schemas import AlbumRecord
from src.packages.auth.dependencies import get_current_user
from src.packages.auth.schemas import UserRecord
from src.packages.shares import service
from src.packages.shares.responses import EnterShareResponse, ShareLinkResponse
from src.responses import Envelope

# Administering the link: generating, regenerating, revoking. Owner-only
# (album-sharing spec) -- `get_owned_album` raises `ForbiddenError` for a
# member who isn't the owner, `NotFoundError` for anyone else.
router = APIRouter(prefix="/albums/{album_id}/share")


@router.get("")
async def get_share_link(
    album: AlbumRecord = Depends(get_owned_album),
    connection: AsyncConnection = Depends(get_connection),
) -> Envelope[ShareLinkResponse]:
    url = await service.get_or_create_link(connection, album_id=album.id)
    return Envelope(data=ShareLinkResponse(url=url))


@router.post("/regenerate")
async def regenerate_share_link(
    album: AlbumRecord = Depends(get_owned_album),
    connection: AsyncConnection = Depends(get_connection),
) -> Envelope[ShareLinkResponse]:
    url = await service.regenerate_link(connection, album_id=album.id)
    return Envelope(data=ShareLinkResponse(url=url))


@router.post("/revoke")
async def revoke_share_link(
    album: AlbumRecord = Depends(get_owned_album),
    connection: AsyncConnection = Depends(get_connection),
) -> Envelope[None]:
    await service.revoke_link(connection, album_id=album.id)
    return Envelope(data=None)


# Entering with a token: a write, deliberately never a GET (D4) -- a
# top-level navigation from another origin (a messaging app, a mail
# client) carries the session cookie under SameSite=Lax, so if this were a
# read, a bare link anywhere could enroll someone as a member without
# their app ever choosing to.
enter_router = APIRouter(prefix="/shares")


@enter_router.post("/{token}")
async def enter_share(
    token: str,
    user: UserRecord = Depends(get_current_user),
    connection: AsyncConnection = Depends(get_connection),
) -> Envelope[EnterShareResponse]:
    album_id = await service.enter(connection, token=token, user_id=user.id)
    return Envelope(data=EnterShareResponse(album_id=album_id))
