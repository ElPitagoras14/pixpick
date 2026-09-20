"""Bundles a `StoragePort` with the one thing outside its contract that the
suite still needs: performing the direct write a browser makes against a
presigned grant; the port itself never accepts content. Both harnesses
expose the same shape, so the contract suite in test_contract.py is the same
code regardless of which one it runs against.
"""

from dataclasses import dataclass, field
from typing import Protocol

import httpx

from src.storage.port import StoragePort, UploadGrant
from tests.fakes import FakeStoragePort


class StorageHarness(Protocol):
    port: StoragePort
    # Every key a test's uploads landed on, so the fixture can delete them
    # afterwards regardless of which provider actually stored them.
    created_keys: list[str]

    def upload(
        self,
        grant: UploadGrant,
        *,
        size: int,
        content_type: str = "image/jpeg",
        target_key: str | None = None,
    ) -> int:
        """Performs the write, returning an HTTP-like status code: below
        300 for an accepted write, otherwise a rejection. `target_key`
        lets a test write to a key other than the one the grant names,
        to exercise the "wrong object" rejection.
        """
        ...


@dataclass
class FakeStorageHarness:
    port: FakeStoragePort
    created_keys: list[str] = field(default_factory=list)

    def upload(
        self,
        grant: UploadGrant,
        *,
        size: int,
        content_type: str = "image/jpeg",
        target_key: str | None = None,
    ) -> int:
        key = target_key or grant.object_key
        accepted = self.port.upload(target_key=key, size=size, content_type=content_type)
        if accepted:
            self.created_keys.append(key)
        return 200 if accepted else 403


@dataclass
class S3StorageHarness:
    """Drives whichever real S3-compatible adapter is active: the same
    PUT-and-headers logic below is all any of them needs, since what differs
    between them is client configuration, never this."""

    port: StoragePort
    created_keys: list[str] = field(default_factory=list)

    def upload(
        self,
        grant: UploadGrant,
        *,
        size: int,
        content_type: str = "image/jpeg",
        target_key: str | None = None,
    ) -> int:
        # `target_key` exercises "a grant doesn't authorize writing a
        # different object": a PUT is signed against its own URL path, which
        # already names the object, so writing to a different key means
        # requesting a different URL entirely -- there's no separate field
        # to override.
        key = target_key or grant.object_key
        url = grant.url.replace(grant.object_key, key) if target_key is not None else grant.url
        content = b"\xff" * size
        response = httpx.put(url, content=content, headers=grant.headers)
        if response.status_code < 300:
            self.created_keys.append(key)
        return response.status_code
