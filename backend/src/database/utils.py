from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine

from . import client as _client_module


@asynccontextmanager
async def transaction(engine: AsyncEngine | None = None) -> AsyncIterator[AsyncConnection]:
    """Opens a connection and a transaction, yields it, and commits on a
    clean exit or rolls back on an exception.

    Services call every write that must be atomic through the connection
    this yields, so the unit of work's boundary is exactly this `async
    with` block -- readable at the call site (D3, D9), without inspecting
    the call stack.

    `engine` defaults to the app's own, looked up on the module rather
    than imported by value, so a test session can point the default
    itself at the test database (see `backend/tests/conftest.py`) instead
    of every caller having to pass one -- production callers never do.
    This matters beyond the request-scoped connection `get_connection`
    hands out: a service that must commit its own writes before an
    external call (D6 in add-albums-and-upload) opens its own transaction
    through this same helper, deliberately outside any request's.
    """
    async with (engine or _client_module.engine).begin() as connection:
        yield connection
