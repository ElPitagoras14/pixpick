from uuid import UUID

from src.images.factory import image_port
from src.images.port import Variant
from src.models import ApiModel
from src.packages.ratings.schemas import PendingPhotoRow, RatingRecord
from src.storage.port import object_key


class PendingPhotoResponse(ApiModel):
    """One photo of the rating sequence (photo-rating spec): its declared
    dimensions, used only to reserve its space before it loads, and the
    `rating` variant -- never `thumbnail`, which is the grid's own size
    (image-delivery spec).
    """

    id: UUID
    position: int
    width: int | None = None
    height: int | None = None
    rating_url: str

    @classmethod
    def from_row(cls, row: PendingPhotoRow, *, album_id: UUID) -> "PendingPhotoResponse":
        key = object_key(album_id=str(album_id), photo_id=str(row.id))
        return cls(
            id=row.id,
            position=row.position,
            width=row.width,
            height=row.height,
            rating_url=image_port.variant_url(object_key=key, variant=Variant.RATING),
        )


class RatingResponse(ApiModel):
    photo_id: UUID
    approved: bool

    @classmethod
    def from_record(cls, rating: RatingRecord) -> "RatingResponse":
        return cls(photo_id=rating.photo_id, approved=rating.approved)
