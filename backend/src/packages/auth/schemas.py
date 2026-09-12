"""Internal data shapes: how a user or a session look inside the backend,
in the schema's own naming. Never returned to a client as-is -- see
responses.py for what crosses the API boundary (api-conventions spec).
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class UserRecord(BaseModel):
    id: UUID
    provider: str
    provider_user_id: str
    email: str | None = None
    name: str | None = None
    avatar_url: str | None = None


class SessionRecord(BaseModel):
    id: UUID
    user_id: UUID
    expires_at: datetime
