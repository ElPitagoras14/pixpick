from typing import Protocol

from pydantic import BaseModel


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
    knowing which provider issued it (object-storage spec). `fields`
    SHALL be submitted as a multipart form together with the file itself
    under the "file" field, which SHALL be the last one in the form.
    """

    url: str
    fields: dict[str, str]
    object_key: str


class ObjectMetadata(BaseModel):
    """What was actually verified about an object once it landed in the
    storage -- never what the client declared while uploading it."""

    size: int
    content_type: str


class StoragePort(Protocol):
    """The three operations any object storage provider offers
    (object-storage spec). Deliberately missing a fourth that reads
    content: the transformer reads originals from the storage on its own,
    and no other consumer has a reason to hold an image in memory.
    """

    def grant_upload(
        self,
        *,
        album_id: str,
        photo_id: str,
        content_type: str,
        max_size: int,
        ttl_seconds: int,
    ) -> UploadGrant:
        """Concedes a direct upload for a single object. Pure computation
        -- signing doesn't talk to anyone (D8) -- so this is synchronous.
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
