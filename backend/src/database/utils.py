from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine

from src.database.client import engine as _app_engine


@asynccontextmanager
async def transaction(engine: AsyncEngine | None = None) -> AsyncIterator[AsyncConnection]:
    """Opens a connection and a transaction, yields it, and commits on a
    clean exit or rolls back on an exception.

    Services call every write that must be atomic through the connection
    this yields, so the unit of work's boundary is exactly this `async
    with` block -- readable at the call site (D3, D9), without inspecting
    the call stack.

    `engine` defaults to the app's own (production callers never pass it);
    tests pass the test engine so this same helper is what they exercise.
    """
    async with (engine or _app_engine).begin() as connection:
        yield connection
