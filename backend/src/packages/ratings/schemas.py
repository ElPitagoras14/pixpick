"""Internal data shapes: how a rating and a pending photo look inside the
backend, in the schema's own naming. Never returned to a client as-is -- see
responses.py for what crosses the API boundary.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class RatingRecord(BaseModel):
    id: UUID
    photo_id: UUID
    user_id: UUID
    approved: bool
    created_at: datetime
    updated_at: datetime


class PendingPhotoRow(BaseModel):
    """One entry of the pending comparison: enough to render the rating card
    and reserve its space before it loads -- the same reasoning
    `photos.schemas.AvailablePhotoRow` applies to the grid.
    """

    id: UUID
    position: int
    width: int | None = None
    height: int | None = None


class AlbumRatingRow(BaseModel):
    """One rating cast on one of the album's available photos, by whoever
    cast it: the raw row the per-photo counts and the album summary are both
    built from, in the same single pass over these rows -- never a second
    query for either."""

    photo_id: UUID
    user_id: UUID
    approved: bool


class PhotoStats(BaseModel):
    """One photo's aggregate: present even at zero, for a photo nobody has
    rated yet."""

    photo_id: UUID
    approved_count: int
    rejected_count: int


class AlbumStats(BaseModel):
    """An album's statistics: every available photo's counts, plus a summary
    consistent with them by construction -- both come from the same pass
    over `AlbumRatingRow`s."""

    photos: list[PhotoStats]
    participant_count: int
    rating_count: int
