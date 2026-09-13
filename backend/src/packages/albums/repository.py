from uuid import UUID

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncConnection

from src.database.client import fetch_all, fetch_one, fetch_val, fetch_val_or_none, write
from src.packages.albums.schemas import AlbumListRow, AlbumRecord


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


async def list_owned_albums(connection: AsyncConnection, *, owner_id: UUID) -> list[AlbumListRow]:
    """One query for the whole list (D9): a lateral subquery resolves each
    album's available-photo count and cover in the same round trip, never
    one query per album. `array_agg(... order by position)` picks the
    first available photo without a second subquery for the cover alone.
    """
    return await fetch_all(
        connection,
        """
        select
            a.id,
            a.title,
            a.description,
            a.created_at,
            coalesce(agg.photo_count, 0) as photo_count,
            agg.cover_photo_id
        from albums a
        left join lateral (
            select
                count(*) as photo_count,
                (array_agg(p.id order by p."position" asc))[1] as cover_photo_id
            from available_photos p
            where p.album_id = a.id
        ) agg on true
        where a.owner_id = :owner_id
        order by a.created_at desc, a.id desc
        """,
        AlbumListRow,
        {"owner_id": owner_id},
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


async def lock_owned_album_id(
    connection: AsyncConnection, *, album_id: UUID, owner_id: UUID
) -> UUID | None:
    """Locks the album row for the rest of the transaction (D12, D14):
    concurrent batches granted for the same album serialize on this lock,
    so the position each assigns and the occupancy each counts can never
    be computed from a stale, about-to-change view of the other.
    """
    return await fetch_val_or_none(
        connection,
        "select id from albums where id = :album_id and owner_id = :owner_id for update",
        {"album_id": album_id, "owner_id": owner_id},
    )


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
