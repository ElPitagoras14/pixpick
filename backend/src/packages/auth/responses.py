from uuid import UUID

from src.models import ApiModel
from src.packages.auth.schemas import UserRecord


class CurrentUserResponse(ApiModel):
    """What `/auth/me` describes (session-management spec): the person's
    own descriptive data, and deliberately nothing about the session
    that authenticated the request -- no id, no hash.
    """

    id: UUID
    email: str | None = None
    name: str | None = None
    avatar_url: str | None = None

    @classmethod
    def from_record(cls, user: UserRecord) -> "CurrentUserResponse":
        return cls(id=user.id, email=user.email, name=user.name, avatar_url=user.avatar_url)
