from uuid import UUID

from src.images.factory import image_port
from src.images.port import Variant
from src.models import ApiModel
from src.storage.port import object_key

from .schemas import AlbumStats, PendingPhotoRow, PhotoStats, RatingRecord


class PendingPhotoResponse(ApiModel):
    """The `rating` variant, never `thumbnail`, which is the grid's size.
    The declared dimensions reserve the photo's space before it loads.

    `viewer_url` is here for the same reason it is on the gallery's photo:
    the viewer opens from the rating card too, and shows the same variant."""

    id: UUID
    position: int
    width: int | None = None
    height: int | None = None
    rating_url: str
    viewer_url: str

    @classmethod
    def from_row(cls, row: PendingPhotoRow, *, album_id: UUID) -> "PendingPhotoResponse":
        key = object_key(album_id=str(album_id), photo_id=str(row.id))
        return cls(
            id=row.id,
            position=row.position,
            width=row.width,
            height=row.height,
            rating_url=image_port.variant_url(object_key=key, variant=Variant.RATING),
            viewer_url=image_port.variant_url(object_key=key, variant=Variant.VIEWER),
        )


class RatingResponse(ApiModel):
    photo_id: UUID
    approved: bool

    @classmethod
    def from_record(cls, rating: RatingRecord) -> "RatingResponse":
        return cls(photo_id=rating.photo_id, approved=rating.approved)


class PhotoStatsResponse(ApiModel):
    """One photo's aggregate: counts only, never who cast them -- there is
    no field here that could attribute a rating to a particular person.
    """

    photo_id: UUID
    approved_count: int
    rejected_count: int

    @classmethod
    def from_stats(cls, stats: PhotoStats) -> "PhotoStatsResponse":
        return cls(
            photo_id=stats.photo_id,
            approved_count=stats.approved_count,
            rejected_count=stats.rejected_count,
        )


class AlbumStatsResponse(ApiModel):
    """The owner-only resource: every available photo's counts, plus a
    summary whose total always equals their sum, computed fresh on every
    request rather than served from anything stored."""

    photos: list[PhotoStatsResponse]
    participant_count: int
    rating_count: int

    @classmethod
    def from_stats(cls, stats: AlbumStats) -> "AlbumStatsResponse":
        return cls(
            photos=[PhotoStatsResponse.from_stats(photo) for photo in stats.photos],
            participant_count=stats.participant_count,
            rating_count=stats.rating_count,
        )
