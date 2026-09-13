"""D8: a command, run whenever it's useful, not a permanent process --
what it discards is invisible to everyone until then (Risks in this
change's design), so there's no urgency that would justify a schedule.

    uv run python -m src.packages.photos.reconcile
"""

import asyncio

from src.database.utils import transaction
from src.log import logger
from src.loop import loop_factory
from src.packages.photos import repository
from src.storage.factory import storage_port
from src.storage.port import object_key


async def reconcile() -> None:
    """Discards every photo still not available whose upload grant has
    expired -- an upload that will never complete -- together with the
    object it may have left behind despite that (photo-upload spec). Rows
    are deleted and committed first, exactly like every other delete in
    this project (D6): the object for a row deleted here that never had
    one simply isn't found, which `delete_objects` treats as nothing to
    do, not an error.
    """
    async with transaction() as connection:
        expired = await repository.expired_pending_photo_ids(connection)
        await repository.delete_photos_by_id(connection, photo_ids=[row.id for row in expired])

    if not expired:
        logger.info("reconciliation: nothing to discard")
        return

    keys = [object_key(album_id=str(row.album_id), photo_id=str(row.id)) for row in expired]
    await storage_port.delete_objects(object_keys=keys)
    logger.info(f"reconciliation: discarded {len(expired)} expired pending photo(s)")


def main() -> None:
    # psycopg3's async mode can't run on Windows's default event loop
    # (src/loop.py's own docstring); reused here for the same reason
    # uvicorn is given it explicitly, since this command has no uvicorn
    # to do that for it.
    asyncio.run(reconcile(), loop_factory=loop_factory)


if __name__ == "__main__":
    main()
