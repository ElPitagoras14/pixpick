"""End-to-end confirmation that the addresses `ImgproxyAdapter` builds
actually resolve through nginx (image-delivery spec), against the
real transformer and storage this local environment provides.

Requires the local environment already running with at least
`postgres storage transformer nginx` up:
    docker compose -f compose.dev.yaml up -d \\
        postgres storage transformer nginx
"""

import base64
import os
import struct
import uuid
import zlib
from collections.abc import Iterator

import boto3
import httpx
import pytest
from botocore.client import Config

from src.images.catalog import CATALOG
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


def _solid_png(width: int, height: int) -> bytes:
    """A PNG of the given size, built here rather than embedded: the
    viewer variant's ceiling is 2048px, so checking that the longest side
    comes back at that ceiling needs an original bigger than it, and that
    is far too many bytes to paste into a test file."""

    def chunk(kind: bytes, payload: bytes) -> bytes:
        return (
            struct.pack(">I", len(payload))
            + kind
            + payload
            + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)
        )

    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    # One filter byte per scanline, then RGB triples -- uniform, so zlib
    # takes the whole thing down to a few kilobytes.
    raw = b"".join(b"\x00" + b"\xc0\x40\x20" * width for _ in range(height))
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", header)
        + chunk(b"IDAT", zlib.compress(raw, 6))
        + chunk(b"IEND", b"")
    )


def _webp_size(data: bytes) -> tuple[int, int]:
    """The canvas size of a lossy (VP8) or extended (VP8X) WebP, read off
    its own header -- the project has no image library, and this is the
    only thing these tests need to know about the bytes that came back."""
    assert data[:4] == b"RIFF" and data[8:12] == b"WEBP"
    kind = data[12:16]
    if kind == b"VP8X":
        width = int.from_bytes(data[24:27], "little") + 1
        height = int.from_bytes(data[27:30], "little") + 1
        return width, height
    if kind == b"VP8 ":
        assert data[23:26] == b"\x9d\x01\x2a"
        width = int.from_bytes(data[26:28], "little") & 0x3FFF
        height = int.from_bytes(data[28:30], "little") & 0x3FFF
        return width, height
    raise AssertionError(f"unsupported WebP chunk {kind!r}")


@pytest.fixture
def uploaded_wide_object() -> Iterator[str]:
    """A real original wider than the viewer variant's own ceiling, so
    the variant has something to actually shrink."""
    key = f"albums/contract-test/{uuid.uuid4()}"
    client = _direct_client()
    client.put_object(
        Bucket=storage_settings.minio_bucket,
        Key=key,
        Body=_solid_png(3000, 1500),
        ContentType="image/png",
    )
    yield key
    client.delete_object(Bucket=storage_settings.minio_bucket, Key=key)


def test_the_viewer_variant_arrives_at_its_ceiling_without_cropping(uploaded_wide_object):
    """Task 1.2 (photo-viewer spec): the address the gallery now carries
    resolves through nginx to the largest variant -- longest side at the
    catalog's own ceiling, and the original's proportion intact, which is
    what says it was fitted and not cropped."""
    spec = CATALOG[Variant.VIEWER]
    url = image_port.variant_url(object_key=uploaded_wide_object, variant=Variant.VIEWER)

    response = httpx.get(url, timeout=30)

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/webp"
    width, height = _webp_size(response.content)
    assert max(width, height) == spec.width
    # 3000x1500 is exactly 2:1, so a crop to the variant's square box
    # would come back 2048x2048 instead.
    assert width == pytest.approx(height * 2, abs=2)


def test_the_viewer_variant_never_enlarges_a_smaller_original(uploaded_object):
    """Task 1.2: the ceiling is a ceiling, not a target -- an original
    below it comes back at its own size, not blown up to 2048."""
    url = image_port.variant_url(object_key=uploaded_object, variant=Variant.VIEWER)

    response = httpx.get(url, timeout=30)

    assert response.status_code == 200
    assert _webp_size(response.content) == (8, 8)
