from fastapi import APIRouter

from src.database.client import check_connectivity
from src.models import ApiModel
from src.responses import Envelope

router = APIRouter()


class HealthData(ApiModel):
    status: str


@router.get("/health")
async def get_health() -> Envelope[HealthData]:
    """Confirms the backend process is up and can reach the database.

    A `DatabaseUnavailableError` here isn't caught: it propagates to the
    registered handler (src/handlers.py), which turns it into a response
    that reports the outage without revealing any database detail.
    """
    await check_connectivity()
    return Envelope(data=HealthData(status="ok"))
