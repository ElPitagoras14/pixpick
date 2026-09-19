"""Internal data shapes: how a photo looks inside the backend, in the
schema's own naming. Never returned to a client as-is -- see responses.py
for what crosses the API boundary (api-conventions spec).
"""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

from src.storage.port import UploadGrant

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


# Which of the three capacity limits kept a file from getting a grant
# (photo-upload spec, modified by add-instance-quota). Not interchangeable
# and not resolved the same way: running out of room in the album is
# resolved by creating another album, running out of space in the account
# by deleting something, and running out of space in the instance is not
# resolved by whoever is asking at all -- the space that's missing may not
# be theirs.
DenialReason = Literal["album_full", "account_full", "instance_full"]


class GrantedFile(BaseModel):
    """One file of a batch that did get a grant. `index` is the position
    the file had in the request (D4): the request carries no filename --
    only a type, a size and dimensions -- so the index is the only thing
    that names which file this answers for, and a partly granted batch
    no longer lets the client match them up by order alone.
    """

    index: int
    photo_id: UUID
    position: int
    grant: UploadGrant


class DeniedFile(BaseModel):
    """One file of a batch that did not get a grant, with which limit
    stopped it and how much was left of that limit. Only the field the
    reason is about is filled in: the two are counted in different units,
    and one `remaining` standing for either would leave the unit implied.
    """

    index: int
    reason: DenialReason
    remaining_photos: int | None = None
    remaining_bytes: int | None = None


class GrantBatchResult(BaseModel):
    """What a batch of grant requests produces (D4, D5): what was granted
    and what was not, never one flat list as long as the request. A file
    that does not fit is skipped and the walk continues, so a smaller one
    behind it can still be granted."""

    granted: list[GrantedFile]
    denied: list[DeniedFile]


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
