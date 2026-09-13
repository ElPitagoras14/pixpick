"""End-to-end confirmation that the addresses `ImgproxyAdapter` builds
actually resolve through nginx (image-delivery spec), against the
real transformer and storage this local environment provides.

Requires the local environment already running with at least
`postgres storage storage-init transformer nginx` up:
    docker compose -f compose.yaml -f compose.dev.yaml up -d \\
        postgres storage storage-init transformer nginx
"""

import base64
import os
import uuid
from collections.abc import Iterator

import boto3
import httpx
import pytest
from botocore.client import Config

from src.images.factory import image_port
from src.images.port import Variant
from src.storage.config import storage_settings

_NGINX_BASE_URL = f"http://localhost:{os.environ['NGINX_PORT']}"

# An 8x8 red JPEG -- small enough to embed, real enough for the
# transformer to actually decode and resize.
_TEST_IMAGE = base64.b64decode(
    "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQY"
    "GBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYa"
    "KCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAAR"
    "CAAIAAgDASIAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAA"
    "AgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkK"
    "FhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWG"
    "h4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl"
    "5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREA"
    "AgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYk"
    "NOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOE"
    "hYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk"
    "5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwDzqiiivjj+kT//2Q=="
)


def _direct_client():
    return boto3.client(
        "s3",
        endpoint_url=storage_settings.minio_server_endpoint,
        aws_access_key_id=storage_settings.minio_access_key_id,
        aws_secret_access_key=storage_settings.minio_secret_access_key,
        config=Config(signature_version="s3v4"),
    )


@pytest.fixture
def uploaded_object() -> Iterator[str]:
    """A real object already sitting in the storage -- test setup that
    bypasses `StoragePort` on purpose, the same way a browser bypasses
    the backend entirely when it writes directly (D2, D3)."""
    key = f"albums/contract-test/{uuid.uuid4()}"
    client = _direct_client()
    client.put_object(
        Bucket=storage_settings.minio_bucket,
        Key=key,
        Body=_TEST_IMAGE,
        ContentType="image/jpeg",
    )
    yield key
    client.delete_object(Bucket=storage_settings.minio_bucket, Key=key)


@pytest.mark.parametrize("variant", list(Variant))
def test_every_catalog_variant_resolves_through_nginx(uploaded_object, variant):
    url = image_port.variant_url(object_key=uploaded_object, variant=variant)
    assert url.startswith(_NGINX_BASE_URL)

    response = httpx.get(url, timeout=30)

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/webp"


def test_the_second_request_for_the_same_variant_is_served_from_cache(uploaded_object):
    url = image_port.variant_url(object_key=uploaded_object, variant=Variant.THUMBNAIL)

    first = httpx.get(url, timeout=30)
    second = httpx.get(url, timeout=30)

    assert first.status_code == second.status_code == 200
    assert second.headers["x-cache-status"] == "HIT"


def test_tampering_the_address_invalidates_its_signature(uploaded_object):
    url = image_port.variant_url(object_key=uploaded_object, variant=Variant.THUMBNAIL)
    # Flips one character deep in the processing options, past the
    # signature segment, leaving the (now stale) signature untouched.
    tampered = url.replace(":400:400:", ":401:401:")
    assert tampered != url

    response = httpx.get(tampered, timeout=30)

    assert response.status_code != 200


def test_a_missing_object_fails_as_an_error_not_as_the_app_document():
    missing_key = f"albums/contract-test/{uuid.uuid4()}"
    url = image_port.variant_url(object_key=missing_key, variant=Variant.THUMBNAIL)

    response = httpx.get(url, timeout=30)

    assert response.status_code >= 400
    assert "text/html" not in response.headers.get("content-type", "")
