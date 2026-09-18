from uuid import UUID

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncConnection

from src.database.client import fetch_all, fetch_one, fetch_val, write

from .config import albums_settings
from .schemas import AlbumDetailRow, AlbumListRow, AlbumRecord

# The one condition every read of `albums` composes (D2 in
# album-retention's design): true while the instant its last photo
# renewed it, plus the configured plazo, still lies in the future.
# `available_photos` solves the equivalent problem for photos with a
# view; a view can't do it here, since the plazo is a runtime setting
# and a view takes no parameters, so this string is the one place that
# gap is closed instead -- every query below, and every other package
# that reads `albums`, composes it from here rather than writing its
# own. `test_album_retention_condition.py` is what keeps a later query
# honest. Assumes the table is aliased `a`.
#
# The interval is built from a cast, not `make_interval`: that
# function's `days` parameter is an integer in Postgres, and the plazo
# is a `float` precisely so a real end-to-end test (task 6.1) can set
# it to a couple of minutes -- a fraction of a day. The interval
# literal parser accepts that fraction directly.
ACTIVE_CONDITION = "(a.renewed_at + (:album_retention_days || ' days')::interval > now())"


def retention_params() -> dict:
    """The bind parameter `ACTIVE_CONDITION` needs, merged into a
    query's own params wherever the condition is used."""
    return {"album_retention_days": albums_settings.album_retention_days}


async def insert_album(
    connection: AsyncConnection,
    *,
    owner_id: UUID,
    title: str,
    description: str | None,
) -> AlbumRecord:
    row = await fetch_one(
        connection,
        """
        insert into albums (owner_id, title, description)
        values (:owner_id, :title, :description)
        returning id, owner_id, title, description, created_at, updated_at
        """,
        AlbumRecord,
        {"owner_id": owner_id, "title": title, "description": description},
    )
    assert row is not None
    return row


async def get_owned_album(
    connection: AsyncConnection, *, album_id: UUID, owner_id: UUID
) -> AlbumRecord | None:
    """`None` both when the album doesn't exist and when it belongs to
    someone else (album-management spec): the caller can't tell the two
    apart from this result, which is the point -- an opaque id SHALL NOT
    confirm another person's album exists.
    """
    return await fetch_one(
        connection,
        f"""
        select a.id, a.owner_id, a.title, a.description, a.created_at, a.updated_at
        from albums a
        where a.id = :album_id and a.owner_id = :owner_id and {ACTIVE_CONDITION}
        """,
        AlbumRecord,
        {"album_id": album_id, "owner_id": owner_id, **retention_params()},
    )


async def list_member_albums(connection: AsyncConnection, *, user_id: UUID) -> list[AlbumListRow]:
    """One query for the whole list (D9, D10): "mine" and "shared with me"
    are the same set, since creating an album makes its owner a member of
    it (album-sharing spec) -- so the list is every album `user_id` is a
    member of, never a union of two separate queries. The same lateral
    subquery that resolves each album's available-photo count and cover
    also resolves how many of them `user_id` hasn't rated yet, all in the
    same round trip, never one query per album. `array_agg(... order by
    position)` picks the first available photo without a second subquery
    for the cover alone.
    """
    return await fetch_all(
        connection,
        f"""
        select
            a.id,
            a.title,
            a.description,
            a.created_at,
            a.renewed_at,
            (a.owner_id = :user_id) as is_owner,
            coalesce(agg.photo_count, 0) as photo_count,
            agg.cover_photo_id,
            coalesce(agg.pending_count, 0) as pending_count
        from albums a
        join album_members m on m.album_id = a.id and m.user_id = :user_id
        left join lateral (
            select
                count(*) as photo_count,
                (array_agg(p.id order by p."position" asc))[1] as cover_photo_id,
                count(*) filter (
                    where not exists (
                        select 1 from photo_ratings r
                        where r.photo_id = p.id and r.user_id = :user_id
                    )
                ) as pending_count
            from available_photos p
            where p.album_id = a.id
        ) agg on true
        where {ACTIVE_CONDITION}
        order by a.created_at desc, a.id desc
        """,
        AlbumListRow,
        {"user_id": user_id, **retention_params()},
    )


async def get_accessible_album(
    connection: AsyncConnection, *, album_id: UUID, user_id: UUID
) -> AlbumDetailRow | None:
    """An album `user_id` can see: its owner, or a member of it
    (album-management spec, modified by add-share-and-swipe). `None` both
    when the album doesn't exist and when `user_id` has no relation to it
    at all -- the same collapse `get_owned_album` already applies to
    ownership alone, so an opaque id SHALL NOT confirm to a stranger that
    the album exists.

    Resolves how many of the album's available photos `user_id` hasn't
    rated yet in the same round trip (D10): the pending count travels
    with the album wherever it's shown, never a query of its own.
    """
    return await fetch_one(
        connection,
        f"""
        select
            a.id, a.owner_id, a.title, a.description, a.created_at, a.updated_at, a.renewed_at,
            coalesce(pending.count, 0) as pending_count
        from albums a
        join album_members m on m.album_id = a.id and m.user_id = :user_id
        left join lateral (
            select count(*) as count
            from available_photos p
            where p.album_id = a.id
              and not exists (
                  select 1 from photo_ratings r
                  where r.photo_id = p.id and r.user_id = :user_id
              )
        ) pending on true
        where a.id = :album_id and {ACTIVE_CONDITION}
        """,
        AlbumDetailRow,
        {"album_id": album_id, "user_id": user_id, **retention_params()},
    )


async def add_member(connection: AsyncConnection, *, album_id: UUID, user_id: UUID) -> None:
    """Idempotent (album-sharing spec): creating an album, and entering
    its link more than once, both call this, and neither ever produces a
    duplicate row or an error -- the composite primary key on
    `album_members` is what actually enforces that.
    """
    await write(
        connection,
        """
        insert into album_members (album_id, user_id)
        values (:album_id, :user_id)
        on conflict (album_id, user_id) do nothing
        """,
        {"album_id": album_id, "user_id": user_id},
    )


async def album_exists(connection: AsyncConnection, *, album_id: UUID) -> bool:
    """Whether `album_id` names an album that hasn't expired -- the
    check a share link's token resolves against (album-retention spec):
    entering through a link to an expired album SHALL NOT grant access,
    the same rule every other read of `albums` already applies.
    """
    return await fetch_val(
        connection,
        f"select exists(select 1 from albums a where a.id = :album_id and {ACTIVE_CONDITION})",
        {"album_id": album_id, **retention_params()},
    )


async def touch_renewed_at(connection: AsyncConnection, *, album_id: UUID) -> None:
    """Restarts the album's plazo from now (D4 in album-retention's
    design): called only from the same transaction that marks a photo
    available, never on its own, so the two either both commit or both
    roll back together.
    """
    await write(
        connection,
        "update albums set renewed_at = now() where id = :album_id",
        {"album_id": album_id},
    )


async def is_member(connection: AsyncConnection, *, album_id: UUID, user_id: UUID) -> bool:
    return await fetch_val(
        connection,
        """
        select exists(
            select 1 from album_members where album_id = :album_id and user_id = :user_id
        )
        """,
        {"album_id": album_id, "user_id": user_id},
    )


async def rename_owned_album(
    connection: AsyncConnection,
    *,
    album_id: UUID,
    owner_id: UUID,
    title: str,
    description: str | None,
) -> AlbumRecord | None:
    """Touches only the two descriptive columns (album-management spec):
    the photos, their order and their availability are untouched because
    nothing here mentions them."""
    return await fetch_one(
        connection,
        """
        update albums
        set title = :title, description = :description
        where id = :album_id and owner_id = :owner_id
        returning id, owner_id, title, description, created_at, updated_at
        """,
        AlbumRecord,
        {
            "album_id": album_id,
            "owner_id": owner_id,
            "title": title,
            "description": description,
        },
    )


class _PhotoIdRow(BaseModel):
    id: UUID


async def delete_owned_album_returning_photo_ids(
    connection: AsyncConnection, *, album_id: UUID, owner_id: UUID
) -> list[UUID] | None:
    """Deletes the album -- and, via cascade, every one of its photos --
    if owned by `owner_id`. Returns the ids the album's photos had just
    before the delete, so the caller can compute their object keys and
    remove them from storage *after* this transaction commits (D6); or
    `None` if there was no such album to delete.
    """
    exists = await fetch_val(
        connection,
        f"""
        select exists(
            select 1 from albums a
            where a.id = :album_id and a.owner_id = :owner_id and {ACTIVE_CONDITION}
        )
        """,
        {"album_id": album_id, "owner_id": owner_id, **retention_params()},
    )
    if not exists:
        return None
    photo_rows = await fetch_all(
        connection,
        "select id from photos where album_id = :album_id",
        _PhotoIdRow,
        {"album_id": album_id},
    )
    await write(
        connection,
        "delete from albums where id = :album_id and owner_id = :owner_id",
        {"album_id": album_id, "owner_id": owner_id},
    )
    return [row.id for row in photo_rows]


class _ExpiredPhotoKey(BaseModel):
    """Just enough to derive an object key -- the same shape
    `photos.repository.expired_pending_photo_ids` returns for
    reconciliation's other half."""

    id: UUID
    album_id: UUID


async def delete_expired_albums_returning_photo_keys(
    connection: AsyncConnection,
) -> list[_ExpiredPhotoKey]:
    """Deletes every album whose plazo has run out, and with it --
    through the same cascade a manual delete already relies on -- every
    one of its photos (D3 in album-retention's design). Returns the
    keys their objects need to be removed under, so the caller can do
    that *after* this transaction commits (D6), the same ordering
    `delete_owned_album_returning_photo_ids` and reconciliation's own
    upload cleanup both already use.
    """
    photo_rows = await fetch_all(
        connection,
        f"""
        select p.id, p.album_id
        from photos p
        join albums a on a.id = p.album_id
        where not {ACTIVE_CONDITION}
        """,
        _ExpiredPhotoKey,
        retention_params(),
    )
    await write(
        connection, f"delete from albums a where not {ACTIVE_CONDITION}", retention_params()
    )
    return photo_rows
