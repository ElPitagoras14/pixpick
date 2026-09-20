"""Internal data shapes: how storage usage looks inside the backend, in the
schema's own naming. Never returned to a client as-is -- see responses.py
for what crosses the API boundary.
"""

from uuid import UUID

from pydantic import BaseModel


class AlbumUsageRow(BaseModel):
    """One album of the account's breakdown: what it occupies against its
    owner's limit. Every album the person owns is a row, an empty one
    included with zero, so the breakdown always adds up to the total rather
    than to "the total minus whatever was omitted"."""

    album_id: UUID
    used_bytes: int


class PhotoUsageRow(BaseModel):
    """One photo's own contribution, in the album it belongs to."""

    photo_id: UUID
    size_bytes: int


class InstanceUsage(BaseModel):
    """The instance level: the total over every account and the limit it is
    measured against, with no breakdown -- the instance isn't anyone's, so
    there is nothing to attribute it to. Internal only:
    `responses.InstanceUsageResponse` reduces these two numbers to a
    percentage before anything crosses the API boundary, so this shape never
    reaches a client as-is.
    """

    used_bytes: int
    limit_bytes: int


class AccountUsage(BaseModel):
    """The account level of the three: the total, the
    limit it is measured against, and the per-album breakdown. The three
    travel together because what a person decides with them -- whether to
    free space, and which album to free it from -- needs all three."""

    used_bytes: int
    limit_bytes: int
    albums: list[AlbumUsageRow]


class AlbumUsage(BaseModel):
    """The album level: what the album occupies and what each of its
    photos contributes. `used_bytes` always equals the sum of `photos`,
    since both come from the same rows."""

    used_bytes: int
    photos: list[PhotoUsageRow]
