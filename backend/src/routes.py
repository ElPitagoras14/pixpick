from fastapi import APIRouter

from src.health import router as health_router

# The browser and the backend see the exact same path: the edge proxies
# `/api` without rewriting it (D2), so the prefix lives here instead of
# being stripped and re-added at the edge.
api_router = APIRouter(prefix="/api")
api_router.include_router(health_router)
