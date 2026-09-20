import base64
import json
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter
from fastapi.responses import RedirectResponse

from src.config import settings
from src.identity.config import identity_settings
from src.identity.exceptions import InvalidCodeError
from src.identity.port import ExternalIdentity
from src.log import logger

router = APIRouter()

# Declared, not read from Google's discovery document: that would add a
# network call to every startup for values that change very rarely.
_AUTHORIZATION_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
_ISSUERS = ("https://accounts.google.com", "accounts.google.com")

# The three minimal scopes -- nothing that reads as sensitive on the
# consent screen.
_SCOPES = "openid email profile"

# Registered as this application's redirect URI in Google's console. Its
# own route, not the shared `/api/auth/callback`, so a rejected consent is
# told apart before it reaches the shared endpoint.
_REDIRECT_PATH = "/api/auth/google/callback"


def google_redirect_uri() -> str:
    return f"{settings.public_url.rstrip('/')}{_REDIRECT_PATH}"


def _decode_id_token_payload(id_token: str) -> dict:
    """Decodes the payload without verifying it. Safe only because the token
    arrives through the credential-authenticated exchange in
    `exchange_code`: the channel is the guarantee, not a signature check.
    It would stop being safe the moment the token came from anywhere else."""
    payload_segment = id_token.split(".")[1]
    padding = "=" * (-len(payload_segment) % 4)
    decoded = base64.urlsafe_b64decode(payload_segment + padding)
    return json.loads(decoded)


class GoogleAuthAdapter:
    """The same cycle as the local adapter: an authorization address, a
    screen outside this system, and a return trip carrying a code to
    exchange for an identity."""

    def authorization_url(self, *, state: str) -> str:
        query = urlencode(
            {
                "client_id": identity_settings.google_client_id,
                "redirect_uri": google_redirect_uri(),
                "response_type": "code",
                "scope": _SCOPES,
                "state": state,
            }
        )
        return f"{_AUTHORIZATION_ENDPOINT}?{query}"

    async def exchange_code(self, *, code: str) -> ExternalIdentity:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                _TOKEN_ENDPOINT,
                data={
                    "code": code,
                    "client_id": identity_settings.google_client_id,
                    "client_secret": identity_settings.google_client_secret,
                    "redirect_uri": google_redirect_uri(),
                    "grant_type": "authorization_code",
                },
            )
        if response.status_code != 200:
            logger.warning(
                f"Google's token exchange failed: {response.status_code} {response.text}"
            )
            raise InvalidCodeError("Google could not exchange the code for an identity")

        id_token = response.json().get("id_token")
        if not id_token:
            raise InvalidCodeError("Google's response carried no identity token")
        payload = _decode_id_token_payload(id_token)

        # Configuration checks, not security controls: with no verified
        # signature they authenticate nothing, but they catch credentials
        # cross-wired between two registered applications.
        if payload.get("aud") != identity_settings.google_client_id:
            raise InvalidCodeError("the identity token's audience does not match this application")
        if payload.get("iss") not in _ISSUERS:
            raise InvalidCodeError("the identity token's issuer is not Google")

        return ExternalIdentity(
            provider="google",
            provider_user_id=payload["sub"],
            email=payload.get("email"),
            name=payload.get("name"),
            avatar_url=payload.get("picture"),
        )


@router.get("/auth/google/callback")
async def google_callback(
    state: str, code: str | None = None, error: str | None = None
) -> RedirectResponse:
    """Separate from the shared `/api/auth/callback` so a rejected consent
    is recognized here: it carries no code, and must never be treated as a
    failed exchange."""
    if error is not None:
        if error != "access_denied":
            # Any other error is Google refusing the request itself:
            # misconfiguration here, not a decision by whoever is signing in.
            logger.warning(f"Google's callback reported an error: {error}")
            raise InvalidCodeError(f"Google reported an error: {error}")
        # A rejected consent is a normal outcome: back to the sign-in screen,
        # with no alarming message and no session.
        return RedirectResponse(url=f"{settings.public_url.rstrip('/')}/login", status_code=302)

    if code is None:
        raise InvalidCodeError("Google's callback carried neither a code nor an error")

    query = urlencode({"state": state, "code": code})
    return RedirectResponse(url=f"/api/auth/callback?{query}", status_code=302)
