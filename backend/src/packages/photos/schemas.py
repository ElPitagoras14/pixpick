"""How a photo looks inside the backend, in the schema's own naming.
Never returned to a client as-is -- see responses.py for that.
"""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

from src.storage.port import UploadGrant

# "all" is every available photo; the other three partition it. Shared, so
# the rating sequence, the pending counter and the gallery can never each
# define "unrated" their own way.
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
    """Enough to render a thumbnail and reserve its space before it loads."""

    id: UUID
    position: int
    width: int | None = None
    height: int | None = None


class GrantFileInput(BaseModel):
    """What `service.grant_batch` needs, with nothing of the HTTP shape it
    arrived in."""

    content_type: str
    size: int
    width: int | None = None
    height: int | None = None


# Not interchangeable: a full album is fixed by creating another, a full
# account by deleting something, and a full instance not by whoever is
# asking at all.
DenialReason = Literal["album_full", "account_full", "instance_full"]


class GrantedFile(BaseModel):
    """`index` is the file's position in the request. The request carries no
    filename, and a partly granted batch can't be matched up by order, so
    this is the only thing that names which file it answers for."""

    index: int
    photo_id: UUID
    position: int
    grant: UploadGrant


class DeniedFile(BaseModel):
    """Only the `remaining` field the reason is about is filled in: the two
    are counted in different units."""

    index: int
    reason: DenialReason
    remaining_photos: int | None = None
    remaining_bytes: int | None = None


class GrantBatchResult(BaseModel):
    """What a batch of grant requests produces: what was granted and what
    was not, never one flat list as long as the request. A file that does
    not fit is skipped and the walk continues, so a smaller one behind it
    can still be granted."""

    granted: list[GrantedFile]
    denied: list[DeniedFile]


class ConfirmationOutcome(BaseModel):
    """One photo's result of a confirmation batch: the three outcomes
    confirming can produce, never a fourth."""

    photo_id: UUID
    status: Literal["available", "rejected", "pending"]


class PhotoWithRatingRow(BaseModel):
    """One row of the single query behind the rating sequence, the pending
    counter and the gallery's four filters: an available photo of the album,
    together with the rating -- if any -- that one particular person gave
    it. `approved` is `None` exactly when unrated, never a stand-in for a
    rejection (the two never collapse into one)."""

    id: UUID
    position: int
    width: int | None = None
    height: int | None = None
    approved: bool | None = None


class GalleryCounts(BaseModel):
    """The four counts the gallery always returns, whatever filter was asked
    for: computed once, in the same pass that also selects the requested
    slice -- never four separate queries."""

    total: int
    approved: int
    rejected: int
    unrated: int


class GalleryResult(BaseModel):
    photos: list[PhotoWithRatingRow]
    counts: GalleryCounts
