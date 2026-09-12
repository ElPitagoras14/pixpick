from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, create_async_engine

from src.database.config import database_settings
from src.exceptions import DatabaseUnavailableError, QueryExecutionError

# Explicit pool limits (D2, D11): five permanent connections and fifteen of
# overflow, a ceiling of twenty per process. Not left to the access layer's
# defaults, and not configuration -- see D11 in add-backend-data-layer's
# design for the invariant these two numbers protect.
POOL_SIZE = 5
MAX_OVERFLOW = 15

engine: AsyncEngine = create_async_engine(
    database_settings.database_url,
    pool_size=POOL_SIZE,
    max_overflow=MAX_OVERFLOW,
)


async def check_connectivity() -> None:
    """Raises `DatabaseUnavailableError` if the database cannot be reached.

    Called during startup (main.py's lifespan) so the process fails fast
    and explicitly instead of starting and serving broken requests.
    """
    try:
        async with engine.connect() as connection:
            await connection.execute(text("select 1"))
    except SQLAlchemyError as exc:
        raise DatabaseUnavailableError("could not reach the database") from exc


async def dispose_engine() -> None:
    """Releases the pool's connections. Called on ordered shutdown."""
    await engine.dispose()


# --- The five functions every access to the database goes through (D3). ---
# Each receives the connection it runs on: none of them opens, closes, or
# obtains one from implicit shared state. The caller controls the
# transaction's scope by choosing which connection to pass in.


async def write(connection: AsyncConnection, query: str, params: dict | None = None) -> None:
    """Runs a single statement that writes and returns no rows."""
    try:
        await connection.execute(text(query), params or {})
    except SQLAlchemyError as exc:
        raise QueryExecutionError("failed to execute a write") from exc


async def write_many(connection: AsyncConnection, query: str, params: list[dict]) -> None:
    """Runs the same statement once per set of parameters, in one batch."""
    try:
        await connection.execute(text(query), params)
    except SQLAlchemyError as exc:
        raise QueryExecutionError("failed to execute a batch write") from exc


async def fetch_one[T: BaseModel](
    connection: AsyncConnection,
    query: str,
    model: type[T],
    params: dict | None = None,
) -> T | None:
    """Reads at most one row, validated against `model`.

    A query that stops returning a field the model declares fails here,
    at the boundary of the data layer, instead of downstream as a missing
    key (database-access spec).
    """
    try:
        result = await connection.execute(text(query), params or {})
        row = result.mappings().one_or_none()
    except SQLAlchemyError as exc:
        raise QueryExecutionError("failed to execute a read") from exc
    return model.model_validate(dict(row)) if row is not None else None


async def fetch_all[T: BaseModel](
    connection: AsyncConnection,
    query: str,
    model: type[T],
    params: dict | None = None,
) -> list[T]:
    """Reads every matching row, each validated against `model`."""
    try:
        result = await connection.execute(text(query), params or {})
        rows = result.mappings().all()
    except SQLAlchemyError as exc:
        raise QueryExecutionError("failed to execute a read") from exc
    return [model.model_validate(dict(row)) for row in rows]


async def fetch_val(connection: AsyncConnection, query: str, params: dict | None = None):
    """Reads a single scalar value (a count, an id, a boolean check)."""
    try:
        result = await connection.execute(text(query), params or {})
        return result.scalar_one()
    except SQLAlchemyError as exc:
        raise QueryExecutionError("failed to execute a read") from exc
