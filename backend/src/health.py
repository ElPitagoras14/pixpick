from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def get_health() -> dict[str, str]:
    """Confirms the backend process is up. Does not check the database."""
    return {"status": "ok"}
