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
    """One photo of the grid (task 6.4): its declared dimensions, used
    only to reserve its space before the thumbnail loads, and never a
    signal of anything else (photo-upload spec).
    """

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
    """What the client applies verbatim to perform its direct upload
    (object-storage spec): the grant, plus the id the client presents
    back at confirmation time, plus the index the file had in the request
    (D4) -- with a batch that can be granted only in part, position in
    the response no longer identifies which file this answers for."""

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
    """One file the batch asked for and did not get (photo-upload spec):
    which of the two capacity limits stopped it, and how much was left of
    that one. Exactly one of the two `remaining` fields is filled in --
    the one the reason is about -- because slots and bytes are not the
    same unit and a single number would leave which one implied."""

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
    """The answer to a batch of grant requests (D4): two lists, never one
    as long as the request. A client that asked for N reads what it got
    and what it didn't, instead of assuming it got N."""

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
    """One photo of the gallery (rating-gallery spec): the grid's own
    thumbnail, plus `rating` -- `None` exactly when this viewer hasn't
    rated it yet, and never the same value a rejection would produce
    (photo-rating spec).
    """

    id: UUID
    position: int
    width: int | None = None
    height: int | None = None
    thumbnail_url: str
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
            rating=rating,
        )


class GalleryCountsResponse(ApiModel):
    """The four counts (D2), always present so the four tabs can show
    their count without a request of their own."""

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
    """What the gallery endpoint returns: the requested slice of photos,
    and the four counts regardless of which slice was asked for.
    Deliberately carries nothing aggregated across viewers -- that's
    `album-stats`'s own, separate resource (album-stats spec)."""

    photos: list[GalleryPhotoResponse]
    counts: GalleryCountsResponse

    @classmethod
    def from_result(cls, result: GalleryResult, *, album_id: UUID) -> "GalleryResponse":
        return cls(
            photos=[GalleryPhotoResponse.from_row(row, album_id=album_id) for row in result.photos],
            counts=GalleryCountsResponse.from_counts(result.counts),
        )
