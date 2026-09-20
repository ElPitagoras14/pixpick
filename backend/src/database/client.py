from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, create_async_engine

from src.exceptions import DatabaseUnavailableError, QueryExecutionError

from .config import (
    IDLE_IN_TRANSACTION_TIMEOUT_MS,
    LOCK_TIMEOUT_MS,
    STATEMENT_TIMEOUT_MS,
    database_settings,
)

# Explicit pool limits: five permanent connections and fifteen of
# overflow, a ceiling of twenty per process. Not left to the access
# layer's defaults, and not configuration: the ceiling is what keeps a
# burst of requests from opening more connections than Postgres accepts.
POOL_SIZE = 5
MAX_OVERFLOW = 15

# A stale connection fails the next query with a driver error unless the
# pool checks it first. `pool_recycle` bounds how long one is trusted
# without that check at all.
POOL_PRE_PING = True
POOL_RECYCLE_SECONDS = 1_800

engine: AsyncEngine = create_async_engine(
    database_settings.database_url,
    pool_size=POOL_SIZE,
    max_overflow=MAX_OVERFLOW,
    pool_pre_ping=POOL_PRE_PING,
    pool_recycle=POOL_RECYCLE_SECONDS,
    connect_args={
        # Forwarded the same way `psql -c` would: no statement, lock wait or
        # idle transaction outlives what `database.config` declares.
        "options": (
            f"-c statement_timeout={STATEMENT_TIMEOUT_MS} "
            f"-c lock_timeout={LOCK_TIMEOUT_MS} "
            f"-c idle_in_transaction_session_timeout="
            f"{IDLE_IN_TRANSACTION_TIMEOUT_MS}"
        )
    },
)


async def check_connectivity() -> None:
    """Called at startup, so the process fails fast instead of serving
    broken requests."""
    try:
        async with engine.connect() as connection:
            await connection.execute(text("select 1"))
    except SQLAlchemyError as exc:
        raise DatabaseUnavailableError("could not reach the database") from exc


async def dispose_engine() -> None:
    """Releases the pool's connections. Called on ordered shutdown."""
    await engine.dispose()


# --- The five functions every access to the database goes through. ---
# Each receives the connection it runs on, so the caller controls the
# transaction's scope by choosing which one to pass in.


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
    """Reads at most one row, validated against `model`, so a query that
    stops returning a declared field fails here and not downstream."""
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
    """For a query that always produces exactly one row -- a count, an
    aggregate, a check. One that can match nothing wants `fetch_val_or_none`."""
    try:
        result = await connection.execute(text(query), params or {})
        return result.scalar_one()
    except SQLAlchemyError as exc:
        raise QueryExecutionError("failed to execute a read") from exc


async def fetch_val_or_none(connection: AsyncConnection, query: str, params: dict | None = None):
    """For a query that may match no row -- a lookup that can miss, a
    `delete ... returning` that found nothing. `None` instead of raising."""
    try:
        result = await connection.execute(text(query), params or {})
        return result.scalar_one_or_none()
    except SQLAlchemyError as exc:
        raise QueryExecutionError("failed to execute a read") from exc
