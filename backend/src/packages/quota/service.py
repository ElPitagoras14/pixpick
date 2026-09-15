from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncConnection

from src.packages.photos.config import photos_settings

from . import repository
from .schemas import AccountUsage, AlbumUsage


async def get_account_usage(connection: AsyncConnection, *, owner_id: UUID) -> AccountUsage:
    """The account level (account-quota spec): the total, the limit it is
    measured against, and the per-album breakdown. The limit lives beside
    the album's own maximum in `photos.config`, where granting reads both
    -- one value, read from one place, whether it is being enforced or
    merely reported.
    """
    return AccountUsage(
        used_bytes=await repository.account_used_bytes(connection, owner_id=owner_id),
        limit_bytes=photos_settings.account_max_bytes,
        albums=await repository.account_usage_by_album(connection, owner_id=owner_id),
    )


async def get_album_usage(connection: AsyncConnection, *, album_id: UUID) -> AlbumUsage:
    """The album level: its photos' own sizes, and the total as their
    sum. Summed here rather than asked of the database a second time, so
    the total and the breakdown can never come from different reads."""
    photos = await repository.album_usage(connection, album_id=album_id)
    return AlbumUsage(used_bytes=sum(photo.size_bytes for photo in photos), photos=photos)
