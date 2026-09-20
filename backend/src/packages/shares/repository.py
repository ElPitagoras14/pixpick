from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncConnection

from src.database.client import fetch_one, fetch_val_or_none, write

from .schemas import ShareTokenRecord


async def get_live_token(connection: AsyncConnection, *, album_id: UUID) -> ShareTokenRecord | None:
    """The album's current live link, or `None` if it has none: a revoked
    row is not live, and an album has at most one live row at a time.
    """
    return await fetch_one(
        connection,
        """
        select id, album_id, token, revoked_at, created_at, updated_at
        from share_tokens
        where album_id = :album_id and revoked_at is null
        """,
        ShareTokenRecord,
        {"album_id": album_id},
    )


async def revoke_live_token(connection: AsyncConnection, *, album_id: UUID) -> None:
    """A no-op if the album already has no live link -- revoking twice is
    not an error, it just leaves things as they already were."""
    await write(
        connection,
        """
        update share_tokens set revoked_at = now()
        where album_id = :album_id and revoked_at is null
        """,
        {"album_id": album_id},
    )


async def create_token(
    connection: AsyncConnection, *, album_id: UUID, token: str
) -> ShareTokenRecord:
    row = await fetch_one(
        connection,
        """
        insert into share_tokens (album_id, token)
        values (:album_id, :token)
        returning id, album_id, token, revoked_at, created_at, updated_at
        """,
        ShareTokenRecord,
        {"album_id": album_id, "token": token},
    )
    assert row is not None
    return row


async def get_live_album_id_by_token(connection: AsyncConnection, *, token: str) -> UUID | None:
    """The album a token currently grants entry to, or `None` for a token
    that's unknown, revoked, or well-formed but foreign to any album. The
    three answer identically on purpose: the caller can't tell them apart
    from this result, and shouldn't be able to.
    """
    return await fetch_val_or_none(
        connection,
        "select album_id from share_tokens where token = :token and revoked_at is null",
        {"token": token},
    )
