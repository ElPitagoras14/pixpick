from uuid import UUID

from src.images.factory import image_port
from src.images.port import Variant
from src.models import ApiModel
from src.packages.albums.schemas import AlbumDetailRow, AlbumListRow, AlbumRecord
from src.storage.port import object_key


class AlbumResponse(ApiModel):
    """A single album, right after the owner creates or renames it
    (album-management spec): its own descriptive fields, and nothing about
    its photos -- the grid is `photos`' own endpoint, not folded in here.
    """

    id: UUID
    title: str
    description: str | None = None

    @classmethod
    def from_record(cls, album: AlbumRecord) -> "AlbumResponse":
        return cls(id=album.id, title=album.title, description=album.description)


class AlbumDetailResponse(ApiModel):
    """A single album as seen by whoever is viewing it (album-management
    spec, modified by add-share-and-swipe): `is_owner` is what the client
    uses to show or hide the owner-only controls -- renaming, deleting,
    uploading, administering the share link -- and `pending_count` is what
    it shows the viewer, including the owner, still has left to rate.
    """

    id: UUID
    title: str
    description: str | None = None
    is_owner: bool
    pending_count: int

    @classmethod
    def from_row(cls, row: AlbumDetailRow, *, viewer_id: UUID) -> "AlbumDetailResponse":
        return cls(
            id=row.id,
            title=row.title,
            description=row.description,
            is_owner=row.owner_id == viewer_id,
            pending_count=row.pending_count,
        )


class AlbumSummaryResponse(ApiModel):
    """One entry of the list (album-management spec, modified by
    add-share-and-swipe): enough to recognize the album, tell an owned one
    from a shared one, and decide whether to open it, with no further
    request needed per album (D9, D10). `cover_url` is `None` exactly when
    the album has no available photo yet -- a state the client SHALL be
    able to represent, not an error.
    """

    id: UUID
    title: str
    description: str | None = None
    is_owner: bool
    photo_count: int
    cover_url: str | None = None
    pending_count: int

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
            is_owner=row.is_owner,
            photo_count=row.photo_count,
            cover_url=cover_url,
            pending_count=row.pending_count,
        )
