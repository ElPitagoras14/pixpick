from fastapi import APIRouter

from src.database.client import check_connectivity

router = APIRouter()


@router.get("/health")
async def get_health() -> dict[str, str]:
    """Confirms the backend process is up and can reach the database.

    A `DatabaseUnavailableError` here isn't caught: it propagates to the
    registered handler (src/handlers.py), which turns it into a response
    that reports the outage without revealing any database detail.
    """
    await check_connectivity()
    return {"status": "ok"}
