"""Internal data shapes: how a rating and a pending photo look inside the
backend, in the schema's own naming. Never returned to a client as-is --
see responses.py for what crosses the API boundary (api-conventions spec).
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
    """One entry of the pending comparison (D2, photo-rating spec): enough
    to render the rating card and reserve its space before it loads --
    the same reasoning `photos.schemas.AvailablePhotoRow` applies to the
    grid.
    """

    id: UUID
    position: int
    width: int | None = None
    height: int | None = None
