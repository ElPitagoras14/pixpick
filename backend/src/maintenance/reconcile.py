"""D8 in add-albums-and-upload, extended by D3 in album-retention: a
command, run whenever it's useful, not a permanent process. What it
discards is invisible to everyone until then (Risks in both changes'
designs), so there's no urgency that would justify a schedule.

    uv run python -m src.maintenance.reconcile

Also the migration check a storage provider change relies on (D6 in
add-cloud-media-adapters): run with `--against` to report which objects a
destination provider is still missing, instead of discarding anything.

    uv run python -m src.maintenance.reconcile --against r2

Lives in this package of its own, not inside `packages.photos` (D3 in
album-retention's design): what it discards now spans photos and whole
albums, and neither one is the other's to contain.
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
    """The storage providers `--against` accepts -- the same values
    `STORAGE_PROVIDER` does (object-storage spec)."""

    local = "local"
    r2 = "r2"


async def reconcile() -> None:
    """Discards what's expired and no longer needs to be kept around:
    every photo still not available whose upload grant has expired --
    an upload that will never complete -- and every album whose plazo
    has run out, together with the objects either one may have left
    behind (photo-upload spec, album-retention spec, D3). Two
    independent passes, each with its own transaction and its own
    storage cleanup after it, so a failure discarding albums never
    stops uploads from being discarded, or the other way around.
    """
    await _discard_expired_uploads()
    await _discard_expired_albums()


async def _discard_expired_uploads() -> None:
    """Rows are deleted and committed first, exactly like every other
    delete in this project (D6): the object for a row deleted here that
    never had one simply isn't found, which `delete_objects` treats as
    nothing to do, not an error.
    """
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
    """The same ordering as `_discard_expired_uploads` (D6, D3 in
    album-retention's design): the albums and their photos are gone
    from the database, committed, before their objects are asked for.
    """
    async with transaction() as connection:
        photo_keys = await albums_repository.delete_expired_albums_returning_photo_keys(connection)

    if not photo_keys:
        logger.info("reconciliation: no expired albums to discard")
        return

    keys = [object_key(album_id=str(row.album_id), photo_id=str(row.id)) for row in photo_keys]
    await storage_port.delete_objects(object_keys=keys)
    logger.info(f"reconciliation: discarded {len(photo_keys)} photo(s) from expired album(s)")


async def check_missing(*, provider: Provider) -> list[str]:
    """Every available photo's object key that `provider` doesn't have
    yet (object-storage spec, D6): the check a migration runs before
    switching the active provider, reusing the same query
    `confirm_batch` already relies on -- `get_object` -- against a port
    built for whichever provider is named, never the currently active
    one, so running this never changes what the running application
    actually serves from.
    """
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
            help=(
                "Report objects missing at this provider instead of discarding "
                "expired uploads (D6 in add-cloud-media-adapters)."
            )
        ),
    ] = None,
) -> None:
    # psycopg3's async mode can't run on Windows's default event loop
    # (src/loop.py's own docstring); reused here for the same reason
    # uvicorn is given it explicitly, since this command has no uvicorn
    # to do that for it.
    asyncio.run(_run(against), loop_factory=loop_factory)


if __name__ == "__main__":
    app()
