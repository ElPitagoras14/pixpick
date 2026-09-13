"""Internal data shapes: how an album looks inside the backend, in the
schema's own naming. Never returned to a client as-is -- see responses.py
for what crosses the API boundary (api-conventions spec).
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class AlbumRecord(BaseModel):
    id: UUID
    owner_id: UUID
    title: str
    description: str | None = None
    created_at: datetime
    updated_at: datetime


class AlbumListRow(BaseModel):
    """One entry of the list query (D9, D10): count and cover resolved by
    the same lateral subquery that produced this row, never a second
    round trip per album.
    """

    id: UUID
    title: str
    description: str | None = None
    created_at: datetime
    photo_count: int
    cover_photo_id: UUID | None = None
