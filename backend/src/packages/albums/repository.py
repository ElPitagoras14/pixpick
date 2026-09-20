from uuid import UUID

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncConnection

from src.database.client import fetch_all, fetch_one, fetch_val, write

from .config import albums_settings
from .schemas import AlbumDetailRow, AlbumListRow, AlbumRecord

# The one condition every read of `albums` composes: true while the last
# photo's renewal, plus the configured retention window, still lies in the
# future. `available_photos` does this for photos with a view, which can't
# work here -- the window is a runtime setting and a view takes no
# parameters. Assumes the table is aliased `a`;
# `test_album_retention_condition.py` keeps a later query honest.
#
# A cast, not `make_interval`, whose `days` parameter is an integer: the
# window is a `float` so a test can set it to a couple of minutes.
ACTIVE_CONDITION = "(a.renewed_at + (:album_retention_days || ' days')::interval > now())"


def retention_params() -> dict:
    """The bind parameter `ACTIVE_CONDITION` needs."""
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
    someone else: an opaque id must not confirm another person's album
    exists."""
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
    """One query for the whole list. "Mine" and "shared with me" are the
    same set, since creating an album makes its owner a member, so this is
    every album `user_id` belongs to. The lateral resolves the photo count,
    the cover and the pending count in the same round trip."""
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
    """An album `user_id` owns or is a member of. `None` for both a missing
    album and one they have no relation to, the same collapse
    `get_owned_album` applies. The pending count comes back in the same
    round trip, since it travels with the album wherever it is shown."""
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
    """Idempotent, enforced by the composite primary key on `album_members`:
    creating an album and entering its link both call this."""
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
    """What a share link's token resolves against: entering through a link
    to an expired album grants nothing."""
    return await fetch_val(
        connection,
        f"select exists(select 1 from albums a where a.id = :album_id and {ACTIVE_CONDITION})",
        {"album_id": album_id, **retention_params()},
    )


async def touch_renewed_at(connection: AsyncConnection, *, album_id: UUID) -> None:
    """Restarts the album's retention window. Called only from the same
    transaction that marks a photo available, so the two commit together."""
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
    """Only the two descriptive columns: nothing here mentions the photos."""
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
    """Deletes the album and, by cascade, its photos. Returns the ids those
    photos had, so the caller can remove their objects *after* this commits;
    `None` when there was no such album."""
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
    """Just enough to derive an object key."""

    id: UUID
    album_id: UUID


async def delete_expired_albums_returning_photo_keys(
    connection: AsyncConnection,
) -> list[_ExpiredPhotoKey]:
    """Deletes every album whose retention window has run out, and by cascade
    its photos. Returns their object keys, to be removed *after* this
    commits."""
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
