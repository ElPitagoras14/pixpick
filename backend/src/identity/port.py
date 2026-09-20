from typing import Protocol

from pydantic import BaseModel


class ExternalIdentity(BaseModel):
    """What a provider hands back once its code is exchanged. `provider` and
    `provider_user_id` are always present; the descriptive fields may be
    absent -- not every provider sends all of them, and their absence never
    blocks signing in.
    """

    provider: str
    provider_user_id: str
    email: str | None = None
    name: str | None = None
    avatar_url: str | None = None


class AuthPort(Protocol):
    """The two operations any identity provider offers. The rest of the
    application talks to this interface only, never to a concrete provider
    -- swapping the active one changes no endpoint and no consumer of the
    identity.
    """

    def authorization_url(self, *, state: str) -> str:
        """The address a person is sent to, to authenticate.

        `state` travels through the provider unmodified and comes back on
        the return leg: it's how the return is matched to the login that
        started it.
        """
        ...

    async def exchange_code(self, *, code: str) -> ExternalIdentity:
        """Exchanges the code the provider's return carries for an
        external identity."""
        ...
