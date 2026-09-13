from uuid import UUID

from src.images.factory import image_port
from src.images.port import Variant
from src.models import ApiModel
from src.packages.albums.schemas import AlbumListRow, AlbumRecord
from src.storage.port import object_key


class AlbumResponse(ApiModel):
    """A single album (album-management spec): its own descriptive
    fields, and nothing about its photos -- the grid is `photos`' own
    endpoint, not folded in here.
    """

    id: UUID
    title: str
    description: str | None = None

    @classmethod
    def from_record(cls, album: AlbumRecord) -> "AlbumResponse":
        return cls(id=album.id, title=album.title, description=album.description)


class AlbumSummaryResponse(ApiModel):
    """One entry of the list (album-management spec): enough to
    recognize the album and decide whether to open it, with no further
    request needed per album (D9). `cover_url` is `None` exactly when the
    album has no available photo yet -- a state the client SHALL be able
    to represent, not an error.
    """

    id: UUID
    title: str
    description: str | None = None
    photo_count: int
    cover_url: str | None = None

    @classmethod
    def from_row(cls, row: AlbumListRow) -> "AlbumSummaryResponse":
        cover_url = None
        if row.cover_photo_id is not None:
            key = object_key(album_id=str(row.id), photo_id=str(row.cover_photo_id))
            cover_url = image_port.variant_url(object_key=key, variant=Variant.THUMBNAIL)
        return cls(
            id=row.id,
            title=row.title,
            description=row.description,
            photo_count=row.photo_count,
            cover_url=cover_url,
        )
