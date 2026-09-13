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

# Google's own addresses (D8 in add-google-oauth-provider): declared here,
# taken from Google's OAuth 2.0 documentation, rather than read from its
# discovery document at
# https://accounts.google.com/.well-known/openid-configuration. That would
# add a network dependency to every startup, to stay current with values
# that change very rarely and are announced when they do.
_AUTHORIZATION_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
_ISSUERS = ("https://accounts.google.com", "accounts.google.com")

# The three minimal scopes (D2, D9): identity, basic profile, and email --
# nothing that reads as sensitive on the consent screen.
_SCOPES = "openid email profile"

# The address registered as this application's redirect URI in Google's
# console (D5). Its own route, not the shared `/api/auth/callback`: that
# lets a rejected consent (D7) be told apart from Google's code before
# either ever reaches the shared endpoint (see `google_callback` below).
_REDIRECT_PATH = "/api/auth/google/callback"


def google_redirect_uri() -> str:
    return f"{settings.public_url.rstrip('/')}{_REDIRECT_PATH}"


def _decode_id_token_payload(id_token: str) -> dict:
    """Decodes, without verifying, the identity token's payload. Safe only
    because this token arrives through the direct, credential-authenticated
    exchange in `exchange_code` below (D1 in add-google-oauth-provider) --
    the channel is the guarantee, not a signature check performed here. It
    would stop being safe the moment this token traveled anywhere else.
    """
    payload_segment = id_token.split(".")[1]
    padding = "=" * (-len(payload_segment) % 4)
    decoded = base64.urlsafe_b64decode(payload_segment + padding)
    return json.loads(decoded)


class GoogleAuthAdapter:
    """Recorre el mismo ciclo que el adapter local (D1 en
    add-google-oauth-provider): produce una dirección de autorización, la
    persona llega a una pantalla -- la de consentimiento de Google, ajena a
    este sistema -- y el retorno trae un código que se canjea por una
    identidad.
    """

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

        # Configuration checks, not security controls (D1): without a
        # verified signature these don't authenticate anything, but they
        # catch credentials cross-wired between two registered
        # applications, which would otherwise show up as sessions created
        # against the wrong project.
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
    """The address registered as this application's redirect URI (D5, D8).
    Separate from the shared `/api/auth/callback` so a rejected consent
    (D7) can be recognized here, before the code either adapter's cycle
    ends with -- session-management spec -- ever comes into play: a
    rejection carries no code and must never be treated as a failed
    exchange.
    """
    if error is not None:
        if error != "access_denied":
            # Any other error is Google refusing the request itself --
            # misconfiguration on our side, not a decision by the person
            # signing in -- and gets an actionable error with the detail
            # in the logs (D7), the same as a failed exchange does.
            logger.warning(f"Google's callback reported an error: {error}")
            raise InvalidCodeError(f"Google reported an error: {error}")
        # A rejected consent is a normal outcome, not a failure (D7): back
        # to the sign-in screen, with no alarming message and no session.
        return RedirectResponse(url=f"{settings.public_url.rstrip('/')}/login", status_code=302)

    if code is None:
        raise InvalidCodeError("Google's callback carried neither a code nor an error")

    query = urlencode({"state": state, "code": code})
    return RedirectResponse(url=f"/api/auth/callback?{query}", status_code=302)
