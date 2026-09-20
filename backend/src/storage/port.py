from collections.abc import Iterator
from typing import Protocol

from pydantic import BaseModel

# The S3 protocol's own ceiling on how many objects a single DeleteObjects
# request may name (object-storage spec, D7 in harden-local-profile's
# design) -- a property of the wire format both MinIO and Cloudflare R2
# speak, not of either provider, so it lives here once instead of being
# duplicated in each adapter that needs to respect it.
DELETE_BATCH_LIMIT = 1000


def batched(items: list[str], size: int) -> Iterator[list[str]]:
    """Splits `items` into consecutive chunks of at most `size`, the last
    one shorter if it doesn't divide evenly. What an adapter's own
    `delete_objects` uses to stay under `DELETE_BATCH_LIMIT` without its
    caller ever having to know that limit exists (D7)."""
    for start in range(0, len(items), size):
        yield items[start : start + size]


def object_key(*, album_id: str, photo_id: str) -> str:
    """The naming rule every provider follows (object-storage spec): the
    name comes from domain identifiers already known when the upload is
    granted, prefixed by the album so deleting an album's objects is
    deleting everything under this prefix. Never derived from the
    filename the client declares -- that's the client's own words, not a
    domain identifier, and the client doesn't control this name.
    """
    return f"albums/{album_id}/{photo_id}"


class UploadGrant(BaseModel):
    """What the client applies verbatim to perform the upload, without
    knowing which provider issued it (object-storage spec). The client
    SHALL send a `PUT` to `url` with the file's raw bytes as the body,
    and SHALL set every header in `headers` exactly as given -- they're
    signed into `url` itself, so a missing or altered one invalidates
    the request (D9 in add-cloud-media-adapters: no presigned URL, on
    any provider, can express a size range the way a POST policy can,
    which is why this describes a PUT and not a form).
    """

    url: str
    headers: dict[str, str]
    object_key: str


class ObjectMetadata(BaseModel):
    """What was actually verified about an object once it landed in the
    storage -- never what the client declared while uploading it."""

    size: int
    content_type: str


class StoragePort(Protocol):
    """The four operations any object storage provider offers
    (object-storage spec). Deliberately missing one that reads content:
    the transformer reads originals from the storage on its own, and no
    other consumer has a reason to hold an image in memory.
    """

    @property
    def bucket(self) -> str:
        """The name of the space this provider keeps this project's
        objects in (image-delivery spec, D10 in harden-local-profile's
        design): what a consumer that has to name it in an address --
        the transformer, building the `s3://bucket/key` it reads an
        original from -- reads instead of a fixed provider's own config,
        so that address always names whichever provider is actually
        active."""
        ...

    async def ensure_ready(self) -> None:
        """Leaves the space this project keeps its objects in ready to
        receive them, so nothing else has to create it (D1). Called once
        at startup, through the port, so the caller never asks which
        provider is active.

        A provider this project runs itself creates the space when it is
        missing; a provider this project only consumes checks that it is
        there and raises `StorageNotReadyError` when it is not (D2, D3).
        Repeating it on a space that is already there SHALL succeed and
        SHALL NOT touch what it holds.
        """
        ...

    def grant_upload(
        self,
        *,
        album_id: str,
        photo_id: str,
        content_type: str,
        ttl_seconds: int,
    ) -> UploadGrant:
        """Concedes a direct upload for a single object. Pure computation
        -- signing doesn't talk to anyone (D8) -- so this is synchronous.

        Takes no size limit: no presigned URL can bound one (D9 in
        add-cloud-media-adapters). The size the client declares is
        validated before this is even called, and the real object's size
        is verified again once it's confirmed (photo-upload spec) --
        this operation only ever bounds the object identity, the
        content type, and how long the grant is good for.
        """
        ...

    async def get_object(self, *, object_key: str) -> ObjectMetadata | None:
        """The real size and content type of an already-uploaded object,
        or `None` if it isn't there -- never confused with an object of
        size zero."""
        ...

    async def delete_objects(self, *, object_keys: list[str]) -> None:
        """Deletes several objects in one operation. Deleting something
        that doesn't exist SHALL NOT be an error."""
        ...
