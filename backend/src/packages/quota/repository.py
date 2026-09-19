from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncConnection

from src.database.client import fetch_all, fetch_val, write
from src.packages.albums.repository import ACTIVE_CONDITION, retention_params

from .schemas import AlbumUsageRow, PhotoUsageRow

# A fixed key (D1 in add-instance-quota): the exact value carries no
# meaning, only that it is always this same one, taken by every
# concession and by nothing else. Postgres advisory locks share one
# keyspace per database, so this constant colliding with another
# feature's own lock would need that feature to pick this same number
# on purpose.
INSTANCE_LOCK_KEY = 727_100_002_017

# What a photo contributes to its owner's usage (account-quota spec):
# its real size once confirmed -- the one verified against the object
# itself -- and the size declared when the grant was issued while it is
# still waiting. `coalesce` on the available branch is defensive only:
# confirming is what sets both columns at once.
_COUNTED_BYTES = (
    "case when p.available then coalesce(p.size, p.declared_size) else p.declared_size end"
)

# Which photos count at all, the same condition the album's own maximum
# uses (`photos.repository.count_occupied_slots`): every available photo,
# plus every one still waiting on a grant that hasn't expired. A wait
# whose grant already expired can never complete, so it occupies nothing
# -- without that exclusion, granting repeatedly without ever confirming
# would let an account past its limit.
_COUNTED = "(p.available or p.upload_expires_at > now())"


async def account_used_bytes(connection: AsyncConnection, *, owner_id: UUID) -> int:
    """The whole account's usage, over every album `owner_id` owns
    (D2): computed on the spot rather than read from a running total, so
    there is no fifth place to forget to update. The limit is what bounds
    the size of this sum, and `albums (owner_id)` and `photos (album_id)`
    are the two indexes it walks -- both already there.
    """
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
    """The whole instance's usage, over every account (D2 in
    add-instance-quota): the same sum as `account_used_bytes`, without
    its owner filter, reusing the very same conditions -- so the two
    totals can never come to count different things by one of them
    drifting out of step with the other.
    """
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
    """Serializes the rest of this transaction against every other
    concession in the instance (D1 in add-instance-quota): a
    transaction-scoped advisory lock on a fixed key, released
    automatically at commit or rollback, with nothing to remember to
    release. Takes the place of the lock granting used to take on the
    owner's own row: serializing globally already serializes by person,
    and a single mutex for all three limits leaves no pair of locks
    that two transactions could ever take in opposite orders.
    """
    await write(connection, "select pg_advisory_xact_lock(:key)", {"key": INSTANCE_LOCK_KEY})


async def account_usage_by_album(
    connection: AsyncConnection, *, owner_id: UUID
) -> list[AlbumUsageRow]:
    """The same total as `account_used_bytes`, broken down by album -- a
    `left join`, so an album holding nothing is a row with zero instead
    of an absent one. That is what makes the breakdown add up to the
    total the account resource reports beside it.
    """
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
    """One album's photos and what each occupies. The album's own total
    is their sum, computed by the caller rather than asked for again:
    two queries over the same rows could disagree, one pass can't.
    """
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
