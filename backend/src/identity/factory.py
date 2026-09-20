from src.config import settings
from src.log import logger

from .adapters.google import GoogleAuthAdapter, google_redirect_uri
from .adapters.local import LocalAuthAdapter
from .config import identity_settings
from .port import AuthPort


class LocalProviderNotAllowedError(RuntimeError):
    """Raised when the local adapter is selected outside development: the
    code it accepts isn't backed by anything a stranger couldn't also send,
    so it must never be reachable outside a developer's own machine."""


class MissingCredentialsError(RuntimeError):
    """Raised when the active identity provider requires credentials from an
    external system and they aren't configured. Evaluated only for the
    provider that's actually selected: a provider that isn't active never
    blocks startup over credentials nothing is going to use.
    """


def build_auth_port() -> AuthPort:
    """The application's single point of provider selection: the rest of the
    code depends on `AuthPort` and never branches on which provider is
    active.
    """
    if identity_settings.identity_provider == "local":
        if settings.environment != "development":
            raise LocalProviderNotAllowedError(
                "the 'local' identity provider only works when ENVIRONMENT=development"
            )
        return LocalAuthAdapter()
    if identity_settings.identity_provider == "google":
        missing = [
            name
            for name, value in (
                ("GOOGLE_CLIENT_ID", identity_settings.google_client_id),
                ("GOOGLE_CLIENT_SECRET", identity_settings.google_client_secret),
            )
            if not value
        ]
        if missing:
            raise MissingCredentialsError(
                f"the 'google' identity provider requires: {', '.join(missing)}"
            )
        # Our own redirect address, that Google's console needs to have
        # declared identically: logged where it can be compared by eye
        # instead of deduced from the code.
        logger.info(f"Google OAuth redirect URI: {google_redirect_uri()}")
        return GoogleAuthAdapter()
    raise AssertionError(f"unhandled identity provider {identity_settings.identity_provider!r}")


# Built at import time so an invalid selection fails the process's
# startup, not the first person who tries to log in.
auth_port: AuthPort = build_auth_port()
