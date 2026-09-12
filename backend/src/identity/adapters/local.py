import secrets
from urllib.parse import urlencode

from fastapi import APIRouter, Form
from fastapi.responses import HTMLResponse, RedirectResponse

from src.identity.exceptions import InvalidCodeError
from src.identity.port import ExternalIdentity

router = APIRouter()

# One-time codes, kept in memory: acceptable only because this adapter
# refuses to run outside development (D2, enforced by the factory) and
# never needs to survive a process restart.
_pending_codes: dict[str, ExternalIdentity] = {}


@router.get("/auth/local/dev-login")
async def dev_login_screen(state: str) -> HTMLResponse:
    """A password-less form: the whole point of this adapter is letting
    a developer become any identity without a third party (D1). Served
    by the backend itself, not a frontend route -- from the interface's
    point of view this is an external place it's sent to and returns
    from, exactly like Google will be.
    """
    return HTMLResponse(f"""<!doctype html>
<html>
<head><title>Local development sign-in</title></head>
<body>
  <h1>Local development sign-in</h1>
  <p>No password: whatever you enter here becomes the signed-in identity.</p>
  <form method="post" action="/api/auth/local/dev-login">
    <input type="hidden" name="state" value="{state}">
    <label>Email <input type="email" name="email" value="dev@example.com" required></label><br>
    <label>Name <input type="text" name="name" value="Dev User"></label><br>
    <button type="submit">Continue</button>
  </form>
</body>
</html>""")


@router.post("/auth/local/dev-login")
async def dev_login_submit(
    state: str = Form(...),
    email: str = Form(...),
    name: str = Form(""),
) -> RedirectResponse:
    """Issues a one-time code and sends the browser back to the generic
    callback endpoint (D1), the same way a real provider's redirect
    would.
    """
    code = secrets.token_urlsafe(16)
    _pending_codes[code] = ExternalIdentity(
        provider="local",
        # The local provider has no real subject of its own; the email
        # the developer typed stands in for it.
        provider_user_id=email,
        email=email,
        name=name or None,
    )
    query = urlencode({"state": state, "code": code})
    return RedirectResponse(url=f"/api/auth/callback?{query}", status_code=303)


class LocalAuthAdapter:
    """Recorre el mismo ciclo que recorrerá Google (D1): produce una
    dirección de autorización, la persona llega a una pantalla, y el
    retorno trae un código que se canjea por una identidad.
    """

    def authorization_url(self, *, state: str) -> str:
        query = urlencode({"state": state})
        return f"/api/auth/local/dev-login?{query}"

    async def exchange_code(self, *, code: str) -> ExternalIdentity:
        identity = _pending_codes.pop(code, None)
        if identity is None:
            raise InvalidCodeError("the code is invalid, expired, or already used")
        return identity
