from fastapi import Cookie, Depends
from sqlalchemy.ext.asyncio import AsyncConnection

from src.database.dependencies import get_connection
from src.exceptions import UnauthenticatedError
from src.packages.auth.config import SESSION_COOKIE_NAME
from src.packages.auth.schemas import UserRecord
from src.packages.auth.service import resolve_session


async def get_current_user(
    session: str | None = Cookie(default=None, alias=SESSION_COOKIE_NAME),
    connection: AsyncConnection = Depends(get_connection),
) -> UserRecord:
    """The declared way any endpoint requires a session (session-management
    spec): without a valid one, this raises before the endpoint's own
    code ever runs -- an expired session is treated exactly like a
    missing one.
    """
    if session is None:
        raise UnauthenticatedError()
    user = await resolve_session(connection, session)
    if user is None:
        raise UnauthenticatedError()
    return user
