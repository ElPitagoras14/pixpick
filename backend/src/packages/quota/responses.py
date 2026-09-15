from uuid import UUID

from src.models import ApiModel

from .schemas import AccountUsage, AlbumUsage, AlbumUsageRow, PhotoUsageRow


class AlbumUsageEntryResponse(ApiModel):
    album_id: UUID
    used_bytes: int

    @classmethod
    def from_row(cls, row: AlbumUsageRow) -> "AlbumUsageEntryResponse":
        return cls(album_id=row.album_id, used_bytes=row.used_bytes)


class PhotoUsageEntryResponse(ApiModel):
    photo_id: UUID
    size_bytes: int

    @classmethod
    def from_row(cls, row: PhotoUsageRow) -> "PhotoUsageEntryResponse":
        return cls(photo_id=row.photo_id, size_bytes=row.size_bytes)


class AccountUsageResponse(ApiModel):
    """The account's own resource (account-quota spec, D3): the total,
    the limit, and the breakdown by album. How much is left is the
    difference between the first two, which is why both travel together
    and neither is sent alone.
    """

    used_bytes: int
    limit_bytes: int
    albums: list[AlbumUsageEntryResponse]

    @classmethod
    def from_usage(cls, usage: AccountUsage) -> "AccountUsageResponse":
        return cls(
            used_bytes=usage.used_bytes,
            limit_bytes=usage.limit_bytes,
            albums=[AlbumUsageEntryResponse.from_row(row) for row in usage.albums],
        )


class AlbumUsageResponse(ApiModel):
    """The album's own resource (account-quota spec, D3): what it
    occupies and what each of its photos contributes. A resource of its
    own rather than fields added to the album's detail or its gallery,
    which a person the album was shared with can read too -- the rule of
    who sees this is written once, at the door, instead of once per field.
    """

    used_bytes: int
    photos: list[PhotoUsageEntryResponse]

    @classmethod
    def from_usage(cls, usage: AlbumUsage) -> "AlbumUsageResponse":
        return cls(
            used_bytes=usage.used_bytes,
            photos=[PhotoUsageEntryResponse.from_row(row) for row in usage.photos],
        )
