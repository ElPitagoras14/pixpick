from uuid import UUID

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncConnection

from src.database.client import fetch_all, fetch_one, fetch_val, write

from .schemas import AlbumDetailRow, AlbumListRow, AlbumRecord


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
        """
        select id, owner_id, title, description, created_at, updated_at
        from albums
        where id = :album_id and owner_id = :owner_id
        """,
        AlbumRecord,
        {"album_id": album_id, "owner_id": owner_id},
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
        """
        select
            a.id,
            a.title,
            a.description,
            a.created_at,
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
        order by a.created_at desc, a.id desc
        """,
        AlbumListRow,
        {"user_id": user_id},
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
        """
        select
            a.id, a.owner_id, a.title, a.description, a.created_at, a.updated_at,
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
        where a.id = :album_id
        """,
        AlbumDetailRow,
        {"album_id": album_id, "user_id": user_id},
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
        "select exists(select 1 from albums where id = :album_id and owner_id = :owner_id)",
        {"album_id": album_id, "owner_id": owner_id},
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
