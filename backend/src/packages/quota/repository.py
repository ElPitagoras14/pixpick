from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncConnection

from src.database.client import fetch_all, fetch_val

from .schemas import AlbumUsageRow, PhotoUsageRow

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
        where a.owner_id = :owner_id and {_COUNTED}
        """,
        {"owner_id": owner_id},
    )
    return int(total)


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
        where a.owner_id = :owner_id
        group by a.id
        order by a.created_at desc, a.id desc
        """,
        AlbumUsageRow,
        {"owner_id": owner_id},
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
