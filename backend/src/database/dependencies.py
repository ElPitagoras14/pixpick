from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncConnection

from src.database.utils import transaction


async def get_connection() -> AsyncIterator[AsyncConnection]:
    """A connection scoped to one request, inside its own transaction
    (D3, D9 in add-backend-data-layer): every write an endpoint makes
    commits together when it returns normally, and rolls back together
    if it raises. Tests override this dependency to reuse the
    already-open, rollback-only connection their own fixture provides.
    """
    async with transaction() as connection:
        yield connection
