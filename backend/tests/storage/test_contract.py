"""The object-storage contract (D9): every test here runs once against
`FakeStoragePort` and once against `MinioStorageAdapter` talking to the
real MinIO the local environment provides, through the exact same body.
A provider that fails any of these isn't acceptable (object-storage spec).
"""

import asyncio
import uuid

from src.storage.port import object_key


def _domain_ids() -> tuple[str, str]:
    return str(uuid.uuid4()), str(uuid.uuid4())


async def test_a_granted_upload_can_be_queried_back(storage_harness):
    album_id, photo_id = _domain_ids()
    grant = storage_harness.port.grant_upload(
        album_id=album_id,
        photo_id=photo_id,
        content_type="image/jpeg",
        ttl_seconds=60,
    )
    assert grant.object_key == object_key(album_id=album_id, photo_id=photo_id)

    status = storage_harness.upload(grant, size=100)
    assert status < 300

    metadata = await storage_harness.port.get_object(object_key=grant.object_key)
    assert metadata is not None
    assert metadata.size == 100
    assert metadata.content_type == "image/jpeg"


async def test_an_absent_object_is_distinguished_from_an_empty_one(storage_harness):
    album_id, photo_id = _domain_ids()
    grant = storage_harness.port.grant_upload(
        album_id=album_id,
        photo_id=photo_id,
        content_type="image/jpeg",
        ttl_seconds=60,
    )

    assert await storage_harness.port.get_object(object_key=grant.object_key) is None

    status = storage_harness.upload(grant, size=0)
    assert status < 300

    empty = await storage_harness.port.get_object(object_key=grant.object_key)
    assert empty is not None
    assert empty.size == 0


async def test_an_expired_grant_no_longer_authorizes_the_write(storage_harness):
    album_id, photo_id = _domain_ids()
    grant = storage_harness.port.grant_upload(
        album_id=album_id,
        photo_id=photo_id,
        content_type="image/jpeg",
        ttl_seconds=1,
    )
    await asyncio.sleep(2)

    status = storage_harness.upload(grant, size=100)
    assert status >= 300


async def test_a_grant_does_not_authorize_writing_a_different_object(storage_harness):
    album_id, photo_id = _domain_ids()
    grant = storage_harness.port.grant_upload(
        album_id=album_id,
        photo_id=photo_id,
        content_type="image/jpeg",
        ttl_seconds=60,
    )
    other_key = object_key(album_id=album_id, photo_id=str(uuid.uuid4()))

    status = storage_harness.upload(grant, size=100, target_key=other_key)
    assert status >= 300
    assert await storage_harness.port.get_object(object_key=other_key) is None


async def test_deleting_something_absent_is_not_an_error(storage_harness):
    await storage_harness.port.delete_objects(object_keys=["albums/does-not/exist"])


async def test_several_objects_are_deleted_in_one_operation(storage_harness):
    keys = []
    for _ in range(2):
        album_id, photo_id = _domain_ids()
        grant = storage_harness.port.grant_upload(
            album_id=album_id,
            photo_id=photo_id,
            content_type="image/jpeg",
            ttl_seconds=60,
        )
        storage_harness.upload(grant, size=10)
        keys.append(grant.object_key)

    await storage_harness.port.delete_objects(object_keys=keys)

    for key in keys:
        assert await storage_harness.port.get_object(object_key=key) is None
