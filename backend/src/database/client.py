from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, create_async_engine

from src.exceptions import DatabaseUnavailableError, QueryExecutionError

from .config import database_settings

# Explicit pool limits (D2, D11): five permanent connections and fifteen of
# overflow, a ceiling of twenty per process. Not left to the access layer's
# defaults, and not configuration -- see D11 in add-backend-data-layer's
# design for the invariant these two numbers protect.
POOL_SIZE = 5
MAX_OVERFLOW = 15

# A connection that's gone stale -- the network dropped it, or Postgres
# closed it -- fails the next query with a driver error instead of a
# clean retry, unless the pool checks it first (D11 in harden-local-
# profile's design: "la validación y el reciclado de conexiones del
# pool"). `pool_recycle` bounds how long any one connection is trusted
# without that check at all, so a connection killed from the server side
# for being older than that never gets the chance to fail a query first.
POOL_PRE_PING = True
POOL_RECYCLE_SECONDS = 1_800

engine: AsyncEngine = create_async_engine(
    database_settings.database_url,
    pool_size=POOL_SIZE,
    max_overflow=MAX_OVERFLOW,
    pool_pre_ping=POOL_PRE_PING,
    pool_recycle=POOL_RECYCLE_SECONDS,
    connect_args={
        # Three session-level ceilings (database-access spec), forwarded
        # to Postgres the same way `psql`'s own `-c` flag would: no
        # statement runs, no lock is waited on, and no transaction sits
        # idle, past what `database.config` declares.
        "options": (
            f"-c statement_timeout={database_settings.statement_timeout_ms} "
            f"-c lock_timeout={database_settings.lock_timeout_ms} "
            f"-c idle_in_transaction_session_timeout="
            f"{database_settings.idle_in_transaction_timeout_ms}"
        )
    },
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
    """Reads a single scalar value that the query always produces exactly
    one row for (a count, an aggregate, a boolean check) -- never a query
    that can legitimately match nothing, which is what `fetch_val_or_none`
    is for.
    """
    try:
        result = await connection.execute(text(query), params or {})
        return result.scalar_one()
    except SQLAlchemyError as exc:
        raise QueryExecutionError("failed to execute a read") from exc


async def fetch_val_or_none(connection: AsyncConnection, query: str, params: dict | None = None):
    """Reads a single scalar value from a query that may legitimately
    match no row (an id looked up by a filter that can miss, a `delete
    ... returning` that found nothing to delete) -- `None` in that case,
    instead of `fetch_val`'s `scalar_one()` raising (added by
    add-albums-and-upload, for exactly that shape of query).
    """
    try:
        result = await connection.execute(text(query), params or {})
        return result.scalar_one_or_none()
    except SQLAlchemyError as exc:
        raise QueryExecutionError("failed to execute a read") from exc
