"""Internal data shapes: how a photo looks inside the backend, in the
schema's own naming. Never returned to a client as-is -- see responses.py
for what crosses the API boundary (api-conventions spec).
"""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

# The four ways the gallery can be sliced, and the one lo-pendiente
# consumes (rating-gallery spec): "all" is every available photo, the
# other three partition it. Shared by `repository.list_photos_with_rating`
# so the rating sequence, the pending counter and the gallery can never
# each define "pending" or "rejected" their own way (D1).
RatingFilter = Literal["all", "approved", "rejected", "unrated"]


class PhotoRecord(BaseModel):
    id: UUID
    album_id: UUID
    position: int
    available: bool
    declared_content_type: str
    declared_size: int
    size: int | None = None
    width: int | None = None
    height: int | None = None
    upload_expires_at: datetime


class AvailablePhotoRow(BaseModel):
    """What the grid needs (task 6.4): enough to render a thumbnail and
    reserve its space before it loads."""

    id: UUID
    position: int
    width: int | None = None
    height: int | None = None


class GrantFileInput(BaseModel):
    """One file of a batch request for upload grants, already validated
    by the request body's own schema -- everything `service.grant_batch`
    needs and nothing about the HTTP shape it arrived in."""

    content_type: str
    size: int
    width: int | None = None
    height: int | None = None


class ConfirmationOutcome(BaseModel):
    """One photo's result of a confirmation batch (photo-upload spec):
    the three outcomes confirming can produce, never a fourth."""

    photo_id: UUID
    status: Literal["available", "rejected", "pending"]


class PhotoWithRatingRow(BaseModel):
    """One row of the single query behind the rating sequence, the
    pending counter and the gallery's four filters (D1, rating-gallery
    spec): an available photo of the album, together with the rating --
    if any -- that one particular person gave it. `approved` is `None`
    exactly when unrated, never a stand-in for a rejection (photo-rating
    spec: the two SHALL NOT collapse into one)."""

    id: UUID
    position: int
    width: int | None = None
    height: int | None = None
    approved: bool | None = None


class GalleryCounts(BaseModel):
    """The four counts the gallery always returns, whatever filter was
    asked for (D2): computed once, in the same pass that also selects
    the requested slice -- never four separate queries."""

    total: int
    approved: int
    rejected: int
    unrated: int


class GalleryResult(BaseModel):
    photos: list[PhotoWithRatingRow]
    counts: GalleryCounts
