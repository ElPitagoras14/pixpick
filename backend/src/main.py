from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from src.database.client import check_connectivity, dispose_engine

from .config import settings
from .handlers import register_exception_handlers
from .log import logger
from .loop import loop_factory
from .routes import api_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Not caught here: an unreachable database SHALL fail startup with an
    # explicit error instead of letting the process serve requests that
    # would fail against the database anyway (database-access spec).
    await check_connectivity()
    yield
    await dispose_engine()


app = FastAPI(title="pixpick", lifespan=lifespan)

register_exception_handlers(app)
app.include_router(api_router)

logger.info(f"pixpick backend starting in {settings.environment} mode")

if __name__ == "__main__":
    # Runs uvicorn itself, instead of the `uvicorn` CLI, so this can pass
    # `loop_factory` as the actual callable it already imported rather
    # than a dotted path for uvicorn to resolve on its own -- the one way
    # to hand it a loop compatible with psycopg3's async mode on Windows
    # (src/loop.py) without a `--loop` flag on the command line. `app` has
    # to travel as the same import string uvicorn's own CLI would use,
    # and not this module's own `app` object, exactly when reload is on:
    # reload respawns worker processes that each need to import it fresh.
    #
    # Reload follows `ENVIRONMENT` rather than a CLI flag: the same
    # command works in every environment, and there's no flag to forget
    # -- or to leave on by accident outside development.
    reload = settings.environment == "development"
    uvicorn.run(
        "src.main:app" if reload else app,
        host="0.0.0.0",
        port=8000,
        loop=loop_factory,
        reload=reload,
    )
