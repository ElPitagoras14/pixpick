from fastapi import FastAPI

from src.config import settings
from src.log import logger
from src.routes import api_router

app = FastAPI(title="pixpick")

app.include_router(api_router)

logger.info(f"pixpick backend starting in {settings.environment} mode")
