from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.exceptions import DatabaseError


async def _database_error_handler(request: Request, exc: DatabaseError) -> JSONResponse:
    """Translates any data-layer failure into a response with no trace of
    the query, the driver, or table/column names (database-access spec).
    The scope is intentionally minimal: today only the healthcheck can
    raise one of these.
    """
    return JSONResponse(status_code=503, content={"status": "unavailable"})


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(DatabaseError, _database_error_handler)
