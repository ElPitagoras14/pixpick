from fastapi import Cookie, Depends
from sqlalchemy.ext.asyncio import AsyncConnection

from src.database.dependencies import get_connection
from src.exceptions import UnauthenticatedError

from .config import SESSION_COOKIE_NAME
from .schemas import UserRecord
from .service import resolve_session


def require_session_cookie(
    session: str | None = Cookie(default=None, alias=SESSION_COOKIE_NAME),
) -> str:
    """A sub-dependency of its own, not a plain check inside
    `get_current_user`'s body (request-throttling spec, D9 in harden-
    local-profile's design): FastAPI resolves a function's own
    dependencies in the order they're declared and stops at the first
    one that raises, so declaring this one before `get_connection` below
    is what keeps a cookie-less request from ever taking a connection.
    """
    if session is None:
        raise UnauthenticatedError()
    return session


async def get_current_user(
    session: str = Depends(require_session_cookie),
    connection: AsyncConnection = Depends(get_connection),
) -> UserRecord:
    """The declared way any endpoint requires a session (session-management
    spec): without a valid one, this raises before the endpoint's own
    code ever runs -- an expired session is treated exactly like a
    missing one.
    """
    user = await resolve_session(connection, session)
    if user is None:
        raise UnauthenticatedError()
    return user
