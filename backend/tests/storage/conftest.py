from collections.abc import AsyncIterator

import pytest_asyncio

from src.storage.adapters.minio import MinioStorageAdapter
from tests.fakes import FakeStoragePort
from tests.storage.harness import FakeStorageHarness, MinioStorageHarness, StorageHarness


@pytest_asyncio.fixture(params=["fake", "minio"])
async def storage_harness(request) -> AsyncIterator[StorageHarness]:
    """The one fixture the contract suite depends on (D9): every test
    that takes it runs once per provider, with the exact same body.

    Requires the real storage to already be up (`docker compose up -d
    storage storage-init`) when the "minio" parametrization runs -- the
    same expectation the suite already has of Postgres.
    """
    harness: StorageHarness
    if request.param == "fake":
        harness = FakeStorageHarness(port=FakeStoragePort())
    else:
        harness = MinioStorageHarness(port=MinioStorageAdapter())
    yield harness
    await harness.port.delete_objects(object_keys=harness.created_keys)
