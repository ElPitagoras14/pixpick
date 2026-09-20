from typing import Literal
from uuid import UUID

from src.images.factory import image_port
from src.images.port import Variant
from src.models import ApiModel
from src.storage.port import object_key

from .schemas import (
    AvailablePhotoRow,
    ConfirmationOutcome,
    DenialReason,
    DeniedFile,
    GalleryCounts,
    GalleryResult,
    GrantBatchResult,
    GrantedFile,
    PhotoWithRatingRow,
)


class PhotoResponse(ApiModel):
    """The declared dimensions reserve the photo's space before the
    thumbnail loads, and mean nothing else."""

    id: UUID
    position: int
    width: int | None = None
    height: int | None = None
    thumbnail_url: str

    @classmethod
    def from_row(cls, row: AvailablePhotoRow, *, album_id: UUID) -> "PhotoResponse":
        key = object_key(album_id=str(album_id), photo_id=str(row.id))
        return cls(
            id=row.id,
            position=row.position,
            width=row.width,
            height=row.height,
            thumbnail_url=image_port.variant_url(object_key=key, variant=Variant.THUMBNAIL),
        )


class PhotoGrantResponse(ApiModel):
    """The grant, the id to present back at confirmation, and the index the
    file had in the request -- a batch granted only in part can't be matched
    up by position."""

    index: int
    photo_id: UUID
    position: int
    upload_url: str
    upload_headers: dict[str, str]

    @classmethod
    def from_granted(cls, granted: GrantedFile) -> "PhotoGrantResponse":
        return cls(
            index=granted.index,
            photo_id=granted.photo_id,
            position=granted.position,
            upload_url=granted.grant.url,
            upload_headers=granted.grant.headers,
        )


class PhotoDenialResponse(ApiModel):
    """Which limit stopped the file, and how much was left of it. Exactly
    one `remaining` field is filled in: slots and bytes are not the same
    unit."""

    index: int
    reason: DenialReason
    remaining_photos: int | None = None
    remaining_bytes: int | None = None

    @classmethod
    def from_denied(cls, denied: DeniedFile) -> "PhotoDenialResponse":
        return cls(
            index=denied.index,
            reason=denied.reason,
            remaining_photos=denied.remaining_photos,
            remaining_bytes=denied.remaining_bytes,
        )


class GrantBatchResponse(ApiModel):
    """Two lists, never one as long as the request: a client reads what it
    got and what it didn't, instead of assuming."""

    granted: list[PhotoGrantResponse]
    denied: list[PhotoDenialResponse]

    @classmethod
    def from_result(cls, result: GrantBatchResult) -> "GrantBatchResponse":
        return cls(
            granted=[PhotoGrantResponse.from_granted(item) for item in result.granted],
            denied=[PhotoDenialResponse.from_denied(item) for item in result.denied],
        )


class ConfirmationResultResponse(ApiModel):
    photo_id: UUID
    status: Literal["available", "rejected", "pending"]

    @classmethod
    def from_outcome(cls, outcome: ConfirmationOutcome) -> "ConfirmationResultResponse":
        return cls(photo_id=outcome.photo_id, status=outcome.status)


class GalleryPhotoResponse(ApiModel):
    """`rating` is `None` exactly when this viewer hasn't rated the photo,
    never the value a rejection produces.

    `viewer_url` travels alongside the thumbnail, never instead of it: the
    grid keeps drawing the thumbnail and only the viewer requests this one.
    It costs another signed address and no extra query."""

    id: UUID
    position: int
    width: int | None = None
    height: int | None = None
    thumbnail_url: str
    viewer_url: str
    rating: Literal["approved", "rejected"] | None = None

    @classmethod
    def from_row(cls, row: PhotoWithRatingRow, *, album_id: UUID) -> "GalleryPhotoResponse":
        key = object_key(album_id=str(album_id), photo_id=str(row.id))
        rating: Literal["approved", "rejected"] | None = None
        if row.approved is True:
            rating = "approved"
        elif row.approved is False:
            rating = "rejected"
        return cls(
            id=row.id,
            position=row.position,
            width=row.width,
            height=row.height,
            thumbnail_url=image_port.variant_url(object_key=key, variant=Variant.THUMBNAIL),
            viewer_url=image_port.variant_url(object_key=key, variant=Variant.VIEWER),
            rating=rating,
        )


class GalleryCountsResponse(ApiModel):
    """Always present, so the four tabs need no request of their own."""

    total: int
    approved: int
    rejected: int
    unrated: int

    @classmethod
    def from_counts(cls, counts: GalleryCounts) -> "GalleryCountsResponse":
        return cls(
            total=counts.total,
            approved=counts.approved,
            rejected=counts.rejected,
            unrated=counts.unrated,
        )


class GalleryResponse(ApiModel):
    """The requested slice, and the four counts whatever the slice. Carries
    nothing aggregated across viewers: that is the album's stats."""

    photos: list[GalleryPhotoResponse]
    counts: GalleryCountsResponse

    @classmethod
    def from_result(cls, result: GalleryResult, *, album_id: UUID) -> "GalleryResponse":
        return cls(
            photos=[GalleryPhotoResponse.from_row(row, album_id=album_id) for row in result.photos],
            counts=GalleryCountsResponse.from_counts(result.counts),
        )
