"""In-memory doubles used by the contract suites (D10): each behaves like
its real counterpart well enough to pass the exact same tests, not a
call recorder that only checks it was invoked correctly.
"""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from src.storage.port import ObjectMetadata, UploadGrant, object_key


@dataclass
class _PendingGrant:
    object_key: str
    expires_at: datetime


@dataclass
class _StoredObject:
    size: int
    content_type: str


class FakeStoragePort:
    """An in-memory object storage. Objects only exist once `upload` --
    the test-only stand-in for the direct write a real browser performs
    against a presigned grant, since the port itself never accepts
    content (D2) -- succeeds against a still-valid grant.
    """

    def __init__(self) -> None:
        self._grants: dict[str, _PendingGrant] = {}
        self._objects: dict[str, _StoredObject] = {}

    @property
    def bucket(self) -> str:
        return "fake-bucket"

    async def ensure_ready(self) -> None:
        """Nothing to create: this storage's space is the dictionary
        above, which exists from the moment the double does. It's still
        here, and still idempotent, because the contract suite calls it
        against this double exactly as it does against a real provider.
        """

    def grant_upload(
        self,
        *,
        album_id: str,
        photo_id: str,
        content_type: str,
        ttl_seconds: int,
    ) -> UploadGrant:
        key = object_key(album_id=album_id, photo_id=photo_id)
        self._grants[key] = _PendingGrant(
            object_key=key,
            expires_at=datetime.now(UTC) + timedelta(seconds=ttl_seconds),
        )
        # No real endpoint: the fake is never driven through HTTP, only
        # through `upload` below.
        return UploadGrant(
            url="fake://upload", headers={"Content-Type": content_type}, object_key=key
        )

    def upload(self, *, target_key: str, size: int, content_type: str) -> bool:
        """Test-only: what a browser writing directly against a grant
        would do. Returns whether the write was accepted, exactly the
        thing a real storage's HTTP response status tells the contract
        suite. No size check here (D9 in add-cloud-media-adapters): no
        presigned URL, on any real provider, can bound one either.
        """
        pending = self._grants.get(target_key)
        if pending is None or pending.expires_at < datetime.now(UTC):
            return False
        self._objects[target_key] = _StoredObject(size=size, content_type=content_type)
        return True

    async def get_object(self, *, object_key: str) -> ObjectMetadata | None:
        obj = self._objects.get(object_key)
        return None if obj is None else ObjectMetadata(size=obj.size, content_type=obj.content_type)

    async def delete_objects(self, *, object_keys: list[str]) -> None:
        for key in object_keys:
            self._objects.pop(key, None)
