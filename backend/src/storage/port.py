from collections.abc import Iterator
from typing import Protocol

from pydantic import BaseModel

# The S3 protocol's own ceiling, so every adapter shares this one.
DELETE_BATCH_LIMIT = 1000


def batched(items: list[str], size: int) -> Iterator[list[str]]:
    for start in range(0, len(items), size):
        yield items[start : start + size]


def object_key(*, album_id: str, photo_id: str) -> str:
    """Built from domain identifiers, never from the filename the client
    declares. Prefixed by the album, so deleting an album's objects is
    deleting a prefix."""
    return f"albums/{album_id}/{photo_id}"


class UploadGrant(BaseModel):
    """A `PUT` to `url` with the raw bytes as the body. Every header in
    `headers` travels exactly as given: they are signed into `url`, so a
    missing or altered one invalidates the request."""

    url: str
    headers: dict[str, str]
    object_key: str


class ObjectMetadata(BaseModel):
    """What was verified about the object, never what the client declared."""

    size: int
    content_type: str


class StoragePort(Protocol):
    """Deliberately missing an operation that reads content: the transformer
    reads originals from the storage itself, and nothing else has a reason
    to hold an image in memory."""

    @property
    def bucket(self) -> str:
        """Read by whoever has to name the bucket in an address -- the
        transformer's `s3://bucket/key` -- so it always names the active
        provider."""
        ...

    async def ensure_ready(self) -> None:
        """Called once at startup. A provider this project runs itself
        creates the bucket when missing; one it only consumes raises
        `StorageNotReadyError`. Idempotent, and never touches what is there."""
        ...

    def grant_upload(
        self,
        *,
        album_id: str,
        photo_id: str,
        content_type: str,
        ttl_seconds: int,
    ) -> UploadGrant:
        """Synchronous: signing talks to no one. Takes no size limit, since
        no presigned URL can bound one -- the declared size is validated
        before this, and the real one verified at confirmation."""
        ...

    async def get_object(self, *, object_key: str) -> ObjectMetadata | None:
        """`None` when the object isn't there -- never confused with one of
        size zero."""
        ...

    async def delete_objects(self, *, object_keys: list[str]) -> None:
        """Deleting something that isn't there is not an error."""
        ...
