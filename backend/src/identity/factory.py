from src.config import settings
from src.identity.adapters.local import LocalAuthAdapter
from src.identity.config import identity_settings
from src.identity.port import AuthPort


class LocalProviderNotAllowedError(RuntimeError):
    """Raised when the local adapter is selected outside development
    (D2): the code it accepts isn't backed by anything a stranger
    couldn't also send, so it must never be reachable outside a
    developer's own machine."""


def build_auth_port() -> AuthPort:
    """The application's single point of provider selection: the rest of
    the code depends on `AuthPort` and never branches on which provider
    is active (identity-provider spec).
    """
    if identity_settings.identity_provider == "local":
        if settings.environment != "development":
            raise LocalProviderNotAllowedError(
                "the 'local' identity provider only works when ENVIRONMENT=development"
            )
        return LocalAuthAdapter()
    raise AssertionError(f"unhandled identity provider {identity_settings.identity_provider!r}")


# Built at import time so an invalid selection fails the process's
# startup, not the first person who tries to log in.
auth_port: AuthPort = build_auth_port()
