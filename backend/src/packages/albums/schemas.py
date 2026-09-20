"""Internal data shapes: how an album looks inside the backend, in the
schema's own naming. Never returned to a client as-is -- see responses.py
for what crosses the API boundary.
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
    """One entry of the list query: "mine" and "shared with me" are the same
    membership query, so this carries `is_owner` to tell them apart and
    `pending_count` -- how many of the album's available photos the caller
    hasn't rated yet -- resolved by the same lateral subquery that produced
    the rest of this row, never a second round trip per album. `renewed_at`
    is the instant its retention window runs from; `responses.py` is what turns it into
    `expires_at`, never this row itself.
    """

    id: UUID
    title: str
    description: str | None = None
    created_at: datetime
    renewed_at: datetime
    is_owner: bool
    photo_count: int
    cover_photo_id: UUID | None = None
    pending_count: int


class AlbumDetailRow(BaseModel):
    """A single album as seen by someone who can access it -- its owner or a
    member. Carries `owner_id` so the caller can tell whether the viewer
    owns it, and `pending_count` so the album page never needs a second
    request for what the album list already shows inline. `renewed_at` is
    the same retention anchor `AlbumListRow` carries.
    """

    id: UUID
    owner_id: UUID
    title: str
    description: str | None = None
    created_at: datetime
    updated_at: datetime
    renewed_at: datetime
    pending_count: int
