from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.config import settings
from src.database.client import check_connectivity, dispose_engine
from src.handlers import register_exception_handlers
from src.log import logger
from src.routes import api_router


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
