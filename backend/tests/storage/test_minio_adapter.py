import socket
import uuid

import boto3
import pytest
from botocore.client import Config
from botocore.exceptions import ClientError

from src.storage.adapters.minio import MinioStorageAdapter
from src.storage.config import storage_settings
from src.storage.exceptions import StorageUnavailableError
from src.storage.port import object_key


def _probe_client():
    """An observer the adapter knows nothing about, so what these tests
    assert about the storage is read from the storage itself."""
    return boto3.client(
        "s3",
        endpoint_url=storage_settings.minio_server_endpoint,
        aws_access_key_id=storage_settings.minio_access_key_id,
        aws_secret_access_key=storage_settings.minio_secret_access_key,
        config=Config(signature_version="s3v4"),
    )


def _use_a_bucket_of_its_own(monkeypatch) -> str:
    name = f"pixpick-ensure-{uuid.uuid4()}"
    monkeypatch.setattr("src.storage.config.storage_settings.minio_bucket", name)
    return name


def test_granting_an_upload_emits_no_network_request(monkeypatch):
    """Signing is pure computation: nothing opens a socket."""

    def _forbidden_connect(*_args, **_kwargs):
        raise AssertionError("grant_upload must not open any connection")

    monkeypatch.setattr(socket.socket, "connect", _forbidden_connect)

    adapter = MinioStorageAdapter()
    grant = adapter.grant_upload(
        album_id="album-1",
        photo_id="photo-1",
        content_type="image/jpeg",
        ttl_seconds=60,
    )

    assert grant.object_key == object_key(album_id="album-1", photo_id="photo-1")
    assert grant.headers["Content-Type"] == "image/jpeg"


async def test_an_unreachable_storage_surfaces_as_a_domain_error(monkeypatch):
    monkeypatch.setattr(
        "src.storage.config.storage_settings.minio_server_endpoint", "http://localhost:1"
    )
    adapter = MinioStorageAdapter()

    with pytest.raises(StorageUnavailableError) as exc_info:
        await adapter.get_object(object_key="albums/album-1/photo-1")

    # Nothing about the provider leaks into the message the rest of the
    # app -- and eventually the client -- would see.
    message = str(exc_info.value).lower()
    assert "boto" not in message
    assert "minio" not in message
    assert "s3" not in message


async def test_a_missing_space_is_created(monkeypatch):
    """The provider the project runs itself owns its space, so startup
    creates it instead of failing."""
    bucket = _use_a_bucket_of_its_own(monkeypatch)
    probe = _probe_client()
    with pytest.raises(ClientError):
        probe.head_bucket(Bucket=bucket)

    adapter = MinioStorageAdapter()
    try:
        await adapter.ensure_ready()

        probe.head_bucket(Bucket=bucket)
    finally:
        probe.delete_bucket(Bucket=bucket)


async def test_an_existing_space_is_left_as_it_is(monkeypatch):
    bucket = _use_a_bucket_of_its_own(monkeypatch)
    probe = _probe_client()
    probe.create_bucket(Bucket=bucket)
    key = object_key(album_id="album-1", photo_id="photo-1")
    probe.put_object(Bucket=bucket, Key=key, Body=b"0" * 10, ContentType="image/jpeg")

    adapter = MinioStorageAdapter()
    try:
        await adapter.ensure_ready()

        metadata = await adapter.get_object(object_key=key)
        assert metadata is not None
        assert metadata.size == 10
    finally:
        probe.delete_object(Bucket=bucket, Key=key)
        probe.delete_bucket(Bucket=bucket)
