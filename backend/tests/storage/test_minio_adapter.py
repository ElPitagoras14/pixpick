import socket

import pytest

from src.storage.adapters.minio import MinioStorageAdapter
from src.storage.exceptions import StorageUnavailableError
from src.storage.port import object_key


def test_granting_an_upload_emits_no_network_request(monkeypatch):
    """Signing is pure computation (D8): nothing opens a socket."""

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
