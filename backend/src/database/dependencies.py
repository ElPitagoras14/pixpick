from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncConnection

from .utils import transaction


async def get_connection() -> AsyncIterator[AsyncConnection]:
    """A connection scoped to one request, inside its own transaction: every
    write an endpoint makes commits together when it returns normally, and
    rolls back together if it raises. Tests override this dependency to
    reuse the already-open, rollback-only connection their own fixture
    provides.
    """
    async with transaction() as connection:
        yield connection
