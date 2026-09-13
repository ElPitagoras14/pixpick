"""Internal data shapes: how a share link looks inside the backend, in the
schema's own naming. Never returned to a client as-is -- see responses.py
for what crosses the API boundary (api-conventions spec).
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ShareTokenRecord(BaseModel):
    id: UUID
    album_id: UUID
    token: str
    revoked_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
