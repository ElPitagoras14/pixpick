from typing import Literal
from uuid import UUID

from src.images.factory import image_port
from src.images.port import Variant
from src.models import ApiModel
from src.packages.photos.schemas import AvailablePhotoRow, ConfirmationOutcome
from src.storage.port import UploadGrant, object_key


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
    back at confirmation time."""

    photo_id: UUID
    position: int
    upload_url: str
    upload_fields: dict[str, str]

    @classmethod
    def from_grant(
        cls, *, photo_id: UUID, position: int, grant: UploadGrant
    ) -> "PhotoGrantResponse":
        return cls(
            photo_id=photo_id,
            position=position,
            upload_url=grant.url,
            upload_fields=grant.fields,
        )


class ConfirmationResultResponse(ApiModel):
    photo_id: UUID
    status: Literal["available", "rejected", "pending"]

    @classmethod
    def from_outcome(cls, outcome: ConfirmationOutcome) -> "ConfirmationResultResponse":
        return cls(photo_id=outcome.photo_id, status=outcome.status)
