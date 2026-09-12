"""Bundles a `StoragePort` with the one thing outside its contract that
the suite still needs: performing the direct write a browser makes
against a presigned grant (the port itself never accepts content, D2).
Both harnesses expose the same shape, so the contract suite in
test_contract.py is the same code regardless of which one it runs
against (D9).
"""

from dataclasses import dataclass, field
from typing import Protocol

import httpx

from src.storage.adapters.minio import MinioStorageAdapter
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
class MinioStorageHarness:
    port: MinioStorageAdapter
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
        fields = dict(grant.fields)
        if target_key is not None:
            fields["key"] = target_key
        content = b"\xff" * size
        response = httpx.post(grant.url, data=fields, files={"file": (key, content, content_type)})
        if response.status_code < 300:
            self.created_keys.append(key)
        return response.status_code
