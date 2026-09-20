from collections.abc import AsyncIterator

import pytest_asyncio

from src.storage.factory import build_storage_port
from tests.fakes import FakeStoragePort
from tests.storage.harness import FakeStorageHarness, S3StorageHarness, StorageHarness


@pytest_asyncio.fixture(params=["fake", "active"])
async def storage_harness(request) -> AsyncIterator[StorageHarness]:
    """The one fixture the contract suite depends on: every test that takes
    it runs once per provider, with the exact same body.

    "active" builds through the same factory the application itself uses
    (`build_storage_port`), so it exercises whichever provider
    `STORAGE_PROVIDER` currently names -- MinIO by default, requiring the
    real storage to already be up (`docker compose -f compose.dev.yaml up -d
    storage`), the same expectation the suite already has of Postgres. To
    run this against the other provider, point `STORAGE_*` at it and run the
    suite again; there's no way to exercise both in the same run, since both
    providers share this one set of settings.
    """
    harness: StorageHarness
    if request.param == "fake":
        harness = FakeStorageHarness(port=FakeStoragePort())
    else:
        harness = S3StorageHarness(port=build_storage_port())
    yield harness
    await harness.port.delete_objects(object_keys=harness.created_keys)
