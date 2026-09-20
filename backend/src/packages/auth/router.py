import secrets
from urllib.parse import quote, unquote

from fastapi import APIRouter, Cookie, Depends, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncConnection

from src.config import settings
from src.database.dependencies import get_connection
from src.identity.factory import auth_port
from src.responses import Envelope

from . import service
from .config import (
    AUTH_COOKIE_PATH,
    RETURN_TO_COOKIE_NAME,
    SESSION_COOKIE_NAME,
    SESSION_LIFETIME,
    STATE_COOKIE_LIFETIME,
    STATE_COOKIE_NAME,
)
from .dependencies import get_current_user
from .exceptions import InvalidStateError
from .responses import CurrentUserResponse
from .return_to import sanitize_return_to
from .schemas import UserRecord
from .security import generate_state

router = APIRouter(prefix="/auth")

# The browser only ever sees this over plain HTTP in a native or
# container-local setup; requiring Secure there would silently drop the
# cookie. Production is reached through the public URL, always https.
_COOKIES_ARE_SECURE = settings.environment != "development"


def _set_auth_cookie(response: Response, name: str, value: str, max_age_seconds: int) -> None:
    response.set_cookie(
        key=name,
        value=value,
        max_age=max_age_seconds,
        httponly=True,
        samesite="lax",
        secure=_COOKIES_ARE_SECURE,
        path=AUTH_COOKIE_PATH,
    )


@router.get("/login")
async def login(return_to: str | None = None) -> RedirectResponse:
    """Sends the browser to the active provider, remembering the
    unpredictable state value and the validated return destination in two
    short-lived cookies so the callback can check the first and honor the
    second.
    """
    destination = sanitize_return_to(return_to)
    state = generate_state()

    redirect = RedirectResponse(url=auth_port.authorization_url(state=state), status_code=302)
    _set_auth_cookie(redirect, STATE_COOKIE_NAME, state, int(STATE_COOKIE_LIFETIME.total_seconds()))
    _set_auth_cookie(
        redirect,
        RETURN_TO_COOKIE_NAME,
        quote(destination, safe=""),
        int(STATE_COOKIE_LIFETIME.total_seconds()),
    )
    return redirect


@router.get("/callback")
async def callback(
    state: str,
    code: str,
    auth_state: str | None = Cookie(default=None, alias=STATE_COOKIE_NAME),
    auth_return_to: str | None = Cookie(default=None, alias=RETURN_TO_COOKIE_NAME),
    connection: AsyncConnection = Depends(get_connection),
) -> RedirectResponse:
    """Completes the cycle the provider's return carries: the state cookie
    must match and is consumed here whether it matches or not -- a value
    that already came back once never authenticates a second one.
    """
    if not auth_state or not secrets.compare_digest(auth_state, state):
        raise InvalidStateError()

    destination = unquote(auth_return_to) if auth_return_to else "/"

    identity = await auth_port.exchange_code(code=code)
    user, token = await service.complete_login(connection, identity)

    target = f"{settings.public_url.rstrip('/')}{destination}"
    redirect = RedirectResponse(url=target, status_code=302)
    redirect.delete_cookie(STATE_COOKIE_NAME, path=AUTH_COOKIE_PATH)
    redirect.delete_cookie(RETURN_TO_COOKIE_NAME, path=AUTH_COOKIE_PATH)
    redirect.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=int(SESSION_LIFETIME.total_seconds()),
        httponly=True,
        samesite="lax",
        secure=_COOKIES_ARE_SECURE,
        path="/",
    )
    return redirect


@router.post("/logout")
async def logout(
    response: Response,
    session: str | None = Cookie(default=None, alias=SESSION_COOKIE_NAME),
    connection: AsyncConnection = Depends(get_connection),
) -> Envelope[None]:
    """A write, not a read: with SameSite=Lax cookies, a read endpoint could
    be triggered by an embed on another site -- this can't be, because
    nothing but an explicit POST reaches it.
    """
    if session:
        await service.end_session(connection, session)
    response.delete_cookie(SESSION_COOKIE_NAME, path="/")
    return Envelope(data=None)


@router.get("/me")
async def me(user: UserRecord = Depends(get_current_user)) -> Envelope[CurrentUserResponse]:
    return Envelope(data=CurrentUserResponse.from_record(user))
