from fastapi import APIRouter

from src.health import router as health_router
from src.identity.config import identity_settings
from src.packages.auth.router import router as auth_router

# The browser and the backend see the exact same path: the edge proxies
# `/api` without rewriting it (D2), so the prefix lives here instead of
# being stripped and re-added at the edge.
api_router = APIRouter(prefix="/api")
api_router.include_router(health_router)
api_router.include_router(auth_router)

# Only the active provider's own routes are mounted: a provider that
# isn't selected contributes nothing to the published schema.
if identity_settings.identity_provider == "local":
    from src.identity.adapters.local import router as local_dev_login_router

    api_router.include_router(local_dev_login_router)
