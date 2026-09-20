from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.exc import TimeoutError as SATimeoutError
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine

from src.exceptions import InsufficientCapacityError

from . import client as _client_module

# How long a client is told to wait before retrying a request the pool had
# no connection for: shorter than the pool's own checkout timeout
# (client.py's engine default of 30s), so a retry lands after the pool has
# had a real chance to free something up, not before.
_POOL_EXHAUSTED_RETRY_AFTER_SECONDS = 5


@asynccontextmanager
async def transaction(engine: AsyncEngine | None = None) -> AsyncIterator[AsyncConnection]:
    """Commits on a clean exit, rolls back on an exception, so the unit of
    work's boundary is this `async with` block and not the call stack.

    `engine` is looked up on the module rather than imported by value, so a
    test session can repoint the default at the test database without every
    caller passing one."""
    try:
        async with (engine or _client_module.engine).begin() as connection:
            yield connection
    except SATimeoutError as exc:
        # The pool itself is exhausted -- every connection is checked out
        # and none freed up before the checkout timeout: a lack of capacity,
        # not a fallen-over database, so it SHALL NOT surface as an
        # unforeseen error.
        raise InsufficientCapacityError(_POOL_EXHAUSTED_RETRY_AFTER_SECONDS) from exc
