"""A command, not a permanent process: what it discards is invisible to
everyone until it runs.

uv run python -m src.maintenance.reconcile

With `--against`, reports which objects a destination provider is still
missing instead of discarding anything -- the check a storage provider
change relies on.

uv run python -m src.maintenance.reconcile --against r2

Its own package, not `packages.photos`: what it discards spans photos and
whole albums.
"""

import asyncio
from enum import StrEnum
from typing import Annotated

import typer

from src.database.utils import transaction
from src.log import logger
from src.loop import loop_factory
from src.packages.albums import repository as albums_repository
from src.packages.photos import repository as photos_repository
from src.storage.factory import build_storage_port, storage_port
from src.storage.port import object_key


class Provider(StrEnum):
    """The same values `STORAGE_PROVIDER` accepts."""

    local = "local"
    r2 = "r2"


async def reconcile() -> None:
    """Discards uploads that will never complete and albums whose retention
    window has run out, with the objects either left behind. Two independent
    passes, so a failure in one never stops the other."""
    await _discard_expired_uploads()
    await _discard_expired_albums()


async def _discard_expired_uploads() -> None:
    """Rows are deleted and committed first. An object that never existed is
    simply not found, which `delete_objects` treats as nothing to do."""
    async with transaction() as connection:
        expired = await photos_repository.expired_pending_photo_ids(connection)
        await photos_repository.delete_photos_by_id(
            connection, photo_ids=[row.id for row in expired]
        )

    if not expired:
        logger.info("reconciliation: nothing to discard")
        return

    keys = [object_key(album_id=str(row.album_id), photo_id=str(row.id)) for row in expired]
    await storage_port.delete_objects(object_keys=keys)
    logger.info(f"reconciliation: discarded {len(expired)} expired pending photo(s)")


async def _discard_expired_albums() -> None:
    """The same ordering as `_discard_expired_uploads`: committed first,
    objects after."""
    async with transaction() as connection:
        photo_keys = await albums_repository.delete_expired_albums_returning_photo_keys(connection)

    if not photo_keys:
        logger.info("reconciliation: no expired albums to discard")
        return

    keys = [object_key(album_id=str(row.album_id), photo_id=str(row.id)) for row in photo_keys]
    await storage_port.delete_objects(object_keys=keys)
    logger.info(f"reconciliation: discarded {len(photo_keys)} photo(s) from expired album(s)")


async def check_missing(*, provider: Provider) -> list[str]:
    """Every object key `provider` is still missing. Built against a port
    for the named provider, never the active one, so running this never
    changes what the application serves from."""
    target = build_storage_port(provider)
    async with transaction() as connection:
        rows = await photos_repository.all_available_photo_keys(connection)

    missing: list[str] = []
    for row in rows:
        key = object_key(album_id=str(row.album_id), photo_id=str(row.id))
        metadata = await target.get_object(object_key=key)
        if metadata is None:
            missing.append(key)
    return missing


async def _run(against: Provider | None) -> None:
    if against is None:
        await reconcile()
        return

    missing = await check_missing(provider=against)
    if not missing:
        logger.info(f"reconciliation check: every object is already present at {against.value!r}")
        return
    logger.warning(f"reconciliation check: {len(missing)} object(s) missing at {against.value!r}:")
    for key in missing:
        logger.warning(f"  {key}")


app = typer.Typer(add_completion=False)


@app.command()
def main(
    against: Annotated[
        Provider | None,
        typer.Option(
            help=("Report objects missing at this provider instead of discarding expired uploads.")
        ),
    ] = None,
) -> None:
    # psycopg3's async mode can't run on Windows's default event loop; see
    # src/loop.py. uvicorn is handed the same policy explicitly, and this
    # command has no uvicorn to do it.
    asyncio.run(_run(against), loop_factory=loop_factory)


if __name__ == "__main__":
    app()
