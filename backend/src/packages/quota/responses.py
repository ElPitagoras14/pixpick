from uuid import UUID

from src.models import ApiModel

from .schemas import AccountUsage, AlbumUsage, AlbumUsageRow, InstanceUsage, PhotoUsageRow


class InstanceUsageResponse(ApiModel):
    """The instance's own resource: the percentage occupied, rounded, and
    nothing more. Never the total or the limit in bytes -- that's the
    installation's real capacity, and publishing it to any signed-in session
    describes whoever hosts it for no benefit to whoever is asking, since
    the percentage already says everything they can act on. Never a
    breakdown by account either, since what any one account occupies is that
    account's own and not this resource's to expose.
    """

    used_percent: int

    @classmethod
    def from_usage(cls, usage: InstanceUsage) -> "InstanceUsageResponse":
        percent = (
            0
            if usage.limit_bytes <= 0
            else min(round(usage.used_bytes / usage.limit_bytes * 100), 100)
        )
        return cls(used_percent=percent)


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
    """The account's own resource: the total, the limit, and the breakdown
    by album. How much is left is the difference between the first two,
    which is why both travel together and neither is sent alone.
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
    """The album's own resource: what it occupies and what each of its
    photos contributes. A resource of its own rather than fields added to
    the album's detail or its gallery, which a person the album was shared
    with can read too -- the rule of who sees this is written once, at the
    door, instead of once per field.
    """

    used_bytes: int
    photos: list[PhotoUsageEntryResponse]

    @classmethod
    def from_usage(cls, usage: AlbumUsage) -> "AlbumUsageResponse":
        return cls(
            used_bytes=usage.used_bytes,
            photos=[PhotoUsageEntryResponse.from_row(row) for row in usage.photos],
        )
