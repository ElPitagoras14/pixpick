from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from .config import settings
from .database.client import check_connectivity, dispose_engine
from .handlers import register_exception_handlers
from .log import logger
from .loop import loop_factory
from .routes import api_router
from .storage.factory import storage_port


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Not caught: an unreachable database fails startup explicitly instead
    # of serving requests that would fail anyway.
    await check_connectivity()
    # Not caught either: a storage that can't be left ready fails startup
    # naming the problem, rather than letting the first upload find it.
    await storage_port.ensure_ready()
    yield
    await dispose_engine()


# In containers the only peer that connects to this process is nginx, so
# this is the one range trusted to declare a client's address through
# X-Forwarded-For. It has to stay equal to the `ip_range` the compose files
# give that network, and to nginx/nginx.conf.template's own
# `set_real_ip_from`. Unused in native mode, where nothing sits in front.
_TRUSTED_PROXY_NETWORK = "172.30.238.128/25"

app = FastAPI(title="pixpick", lifespan=lifespan)

register_exception_handlers(app)
app.include_router(api_router)

logger.info(f"pixpick backend starting in {settings.environment} mode")

if __name__ == "__main__":
    # uvicorn is run here rather than through its CLI so `loop_factory` can
    # travel as the callable itself -- the only way to hand it a loop
    # compatible with psycopg3 on Windows (src/loop.py) without a `--loop`
    # flag. `app` travels as an import string, not this module's object,
    # because reload respawns workers that each import it fresh. Reload
    # follows `ENVIRONMENT`, so there is no flag to leave on by accident.
    reload = settings.environment == "development"
    uvicorn.run(
        "src.main:app" if reload else app,
        host="0.0.0.0",
        port=8000,
        loop=loop_factory,
        reload=reload,
        forwarded_allow_ips=_TRUSTED_PROXY_NETWORK,
    )
