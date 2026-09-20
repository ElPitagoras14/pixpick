from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncConnection

from src.database.client import fetch_all, fetch_val, write
from src.packages.albums.repository import ACTIVE_CONDITION, retention_params

from .schemas import AlbumUsageRow, PhotoUsageRow

# The value carries no meaning, only that every concession takes this same
# one. Advisory locks share a keyspace per database, so a collision would
# need another feature to pick this same number.
INSTANCE_LOCK_KEY = 727_100_002_017

# Its verified size once confirmed, its declared size while still waiting.
# The `coalesce` on the available branch is defensive: confirming sets both
# columns at once.
_COUNTED_BYTES = (
    "case when p.available then coalesce(p.size, p.declared_size) else p.declared_size end"
)

# The same condition the album's own maximum uses
# (`photos.repository.count_occupied_slots`): available photos, plus those
# waiting on a grant that hasn't expired.
_COUNTED = "(p.available or p.upload_expires_at > now())"


async def account_used_bytes(connection: AsyncConnection, *, owner_id: UUID) -> int:
    """Computed on the spot rather than kept as a running total, so there is
    no fourth place to forget to update. Walks `albums (owner_id)` and
    `photos (album_id)`, both already indexed."""
    total = await fetch_val(
        connection,
        f"""
        select coalesce(sum({_COUNTED_BYTES}), 0)
        from photos p
        join albums a on a.id = p.album_id
        where a.owner_id = :owner_id and {_COUNTED} and {ACTIVE_CONDITION}
        """,
        {"owner_id": owner_id, **retention_params()},
    )
    return int(total)


async def instance_used_bytes(connection: AsyncConnection) -> int:
    """`account_used_bytes` without its owner filter, reusing the same
    conditions so the two totals can never drift apart."""
    total = await fetch_val(
        connection,
        f"""
        select coalesce(sum({_COUNTED_BYTES}), 0)
        from photos p
        join albums a on a.id = p.album_id
        where {_COUNTED} and {ACTIVE_CONDITION}
        """,
        retention_params(),
    )
    return int(total)


async def acquire_instance_lock(connection: AsyncConnection) -> None:
    """A transaction-scoped advisory lock, released at commit or rollback.
    Global rather than per owner: the instance limit spans accounts, and one
    mutex for all three limits leaves no pair of locks to deadlock on."""
    await write(connection, "select pg_advisory_xact_lock(:key)", {"key": INSTANCE_LOCK_KEY})


async def account_usage_by_album(
    connection: AsyncConnection, *, owner_id: UUID
) -> list[AlbumUsageRow]:
    """`account_used_bytes` broken down by album. A `left join`, so an empty
    album is a zero row and the breakdown still adds up to the total."""
    return await fetch_all(
        connection,
        f"""
        select a.id as album_id, coalesce(sum({_COUNTED_BYTES}), 0) as used_bytes
        from albums a
        left join photos p on p.album_id = a.id and {_COUNTED}
        where a.owner_id = :owner_id and {ACTIVE_CONDITION}
        group by a.id
        order by a.created_at desc, a.id desc
        """,
        AlbumUsageRow,
        {"owner_id": owner_id, **retention_params()},
    )


async def album_usage(connection: AsyncConnection, *, album_id: UUID) -> list[PhotoUsageRow]:
    """One album's photos and what each occupies. The caller sums them
    rather than asking again: two passes over the same rows could differ."""
    return await fetch_all(
        connection,
        f"""
        select p.id as photo_id, {_COUNTED_BYTES} as size_bytes
        from photos p
        where p.album_id = :album_id and {_COUNTED}
        order by p."position" asc
        """,
        PhotoUsageRow,
        {"album_id": album_id},
    )
