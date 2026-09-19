from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncConnection

from src.database.dependencies import get_connection
from src.packages.albums.dependencies import get_owned_album
from src.packages.albums.schemas import AlbumRecord
from src.packages.auth.dependencies import get_current_user
from src.packages.auth.schemas import UserRecord
from src.responses import Envelope

from . import service
from .responses import AccountUsageResponse, AlbumUsageResponse, InstanceUsageResponse

# The instance's own consumption (instance-quota spec, D3): a resource of
# its own and not a field on the account's, because it belongs to no one
# in particular -- any signed-in person reads the same answer.
instance_router = APIRouter(prefix="/instance")

# The account's own consumption, at a path that names no person
# (account-quota spec): the answer is always about whoever is signed in,
# so there is no identifier here anyone could put someone else's in.
account_router = APIRouter(prefix="/account")

# The album level, under the album it is about -- the same shape
# `album-stats` already uses for the other owner-only resource of an album.
album_router = APIRouter(prefix="/albums/{album_id}")


@instance_router.get("/usage")
async def get_instance_usage(
    # Any signed-in person, and nothing more (instance-quota spec): no
    # ownership to check, since the instance's space belongs to no one
    # account.
    _user: UserRecord = Depends(get_current_user),
    connection: AsyncConnection = Depends(get_connection),
) -> Envelope[InstanceUsageResponse]:
    usage = await service.get_instance_usage(connection)
    return Envelope(data=InstanceUsageResponse.from_usage(usage))


@account_router.get("/usage")
async def get_account_usage(
    user: UserRecord = Depends(get_current_user),
    connection: AsyncConnection = Depends(get_connection),
) -> Envelope[AccountUsageResponse]:
    usage = await service.get_account_usage(connection, owner_id=user.id)
    return Envelope(data=AccountUsageResponse.from_usage(usage))


@album_router.get("/usage")
async def get_album_usage(
    # Owner-only (account-quota spec): a member who isn't the owner gets
    # `ForbiddenError`, a stranger gets `NotFoundError`. What an album
    # occupies is its owner's space and nobody else's -- the endpoint is
    # what decides that, never a condition inside the response (D3).
    album: AlbumRecord = Depends(get_owned_album),
    connection: AsyncConnection = Depends(get_connection),
) -> Envelope[AlbumUsageResponse]:
    usage = await service.get_album_usage(connection, album_id=album.id)
    return Envelope(data=AlbumUsageResponse.from_usage(usage))
