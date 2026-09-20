import asyncio

import boto3
from botocore.client import Config
from botocore.exceptions import BotoCoreError, ClientError

from src.storage.config import storage_settings
from src.storage.exceptions import StorageNotReadyError, StorageUnavailableError
from src.storage.port import DELETE_BATCH_LIMIT, ObjectMetadata, UploadGrant, batched, object_key

# S3-compatible providers reject a v2-signed request; MinIO and Cloudflare
# R2 both require v4.
_SIGNATURE_VERSION = "s3v4"

# What the S3 protocol answers when the bucket itself isn't there.
_MISSING_BUCKET_CODES = ("404", "NoSuchBucket")

# R2 has no regions of its own; this is the literal value its S3 API
# expects in every request, regardless of where the bucket's data
# actually lives (Cloudflare's own S3-compatible API docs).
_REGION = "auto"


def _client():
    return boto3.client(
        "s3",
        endpoint_url=storage_settings.r2_endpoint,
        region_name=_REGION,
        aws_access_key_id=storage_settings.r2_access_key_id,
        aws_secret_access_key=storage_settings.r2_secret_access_key,
        config=Config(signature_version=_SIGNATURE_VERSION),
    )


class R2StorageAdapter:
    """Talks to Cloudflare R2 over the same S3 protocol MinIO speaks
    (D2, D9 in add-cloud-media-adapters): the only thing that differs
    from `MinioStorageAdapter` is this client's configuration -- the
    region R2 expects, and the endpoint and credentials this provider
    issues -- never the operations themselves. Two clients, not one
    (D4): grants are signed against the address the browser reaches,
    queries and deletes go through the address the server reaches --
    the same single `r2_endpoint` for both in this provider (D7), which
    is one config field rather than two that would always have to
    agree, but still two separate client objects.
    """

    def __init__(self) -> None:
        self._browser_client = _client()
        self._server_client = _client()
        self._bucket = storage_settings.r2_bucket

    @property
    def bucket(self) -> str:
        return self._bucket

    async def ensure_ready(self) -> None:
        """Checks, never creates (D2). This bucket is created once at the
        provider itself, so its absence is a configuration error -- and
        answering it by creating a paid resource on its own is not this
        application's call. A missing one gets its own error (D3), since
        it's fixed at the provider and not by looking at the network.
        """
        try:
            await asyncio.to_thread(self._server_client.head_bucket, Bucket=self._bucket)
        except ClientError as exc:
            if exc.response.get("Error", {}).get("Code") in _MISSING_BUCKET_CODES:
                raise StorageNotReadyError(
                    f"the object storage has no space named {self._bucket!r}"
                ) from exc
            raise StorageUnavailableError("could not reach the object storage") from exc
        except BotoCoreError as exc:
            raise StorageUnavailableError("could not reach the object storage") from exc

    def grant_upload(
        self,
        *,
        album_id: str,
        photo_id: str,
        content_type: str,
        ttl_seconds: int,
    ) -> UploadGrant:
        key = object_key(album_id=album_id, photo_id=photo_id)
        try:
            # Pure local signing (D8): no request leaves the process here.
            # A PUT, not a POST with a policy (D9): R2 doesn't implement
            # presigned POST at all, and no presigned URL on any provider
            # can bound a size range the way a POST policy can.
            url = self._browser_client.generate_presigned_url(
                ClientMethod="put_object",
                Params={"Bucket": self._bucket, "Key": key, "ContentType": content_type},
                ExpiresIn=ttl_seconds,
            )
        except (BotoCoreError, ClientError) as exc:
            raise StorageUnavailableError("could not prepare the upload grant") from exc
        return UploadGrant(url=url, headers={"Content-Type": content_type}, object_key=key)

    async def get_object(self, *, object_key: str) -> ObjectMetadata | None:
        try:
            response = await asyncio.to_thread(
                self._server_client.head_object, Bucket=self._bucket, Key=object_key
            )
        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code")
            if error_code in ("404", "NoSuchKey"):
                return None
            raise StorageUnavailableError("could not reach the object storage") from exc
        except BotoCoreError as exc:
            raise StorageUnavailableError("could not reach the object storage") from exc
        return ObjectMetadata(size=response["ContentLength"], content_type=response["ContentType"])

    async def delete_objects(self, *, object_keys: list[str]) -> None:
        if not object_keys:
            return
        try:
            # Split here, not by whoever calls this (D7 in harden-local-
            # profile's design): the S3 protocol rejects a DeleteObjects
            # request naming more than DELETE_BATCH_LIMIT keys, and the
            # two callers that can exceed it -- periodic cleanup and
            # deleting an album -- have no way to know that limit without
            # knowing which provider is active, which is exactly what
            # this port exists to hide.
            for batch in batched(object_keys, DELETE_BATCH_LIMIT):
                await asyncio.to_thread(
                    self._server_client.delete_objects,
                    Bucket=self._bucket,
                    Delete={"Objects": [{"Key": key} for key in batch], "Quiet": True},
                )
        except (BotoCoreError, ClientError) as exc:
            raise StorageUnavailableError("could not reach the object storage") from exc
