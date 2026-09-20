import asyncio

import boto3
from botocore.client import Config
from botocore.exceptions import BotoCoreError, ClientError

from src.storage.config import storage_settings
from src.storage.exceptions import StorageUnavailableError
from src.storage.port import DELETE_BATCH_LIMIT, ObjectMetadata, UploadGrant, batched, object_key

# S3-compatible providers reject a v2-signed request; MinIO and Cloudflare
# R2 both require v4.
_SIGNATURE_VERSION = "s3v4"

# What the S3 protocol answers when the bucket itself isn't there.
_MISSING_BUCKET_CODES = ("404", "NoSuchBucket")

# What it answers when something created the bucket between this process's
# own check and its own create call.
_ALREADY_CREATED_CODES = ("BucketAlreadyOwnedByYou", "BucketAlreadyExists")


def _client(endpoint: str):
    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=storage_settings.minio_access_key_id,
        aws_secret_access_key=storage_settings.minio_secret_access_key,
        # Explicit, not left to boto3's own auto-detection (harden-local-
        # profile, task 3.2): the storage's own hostname is now a
        # subdomain of the application's (STORAGE_PUBLIC_URL), which looks
        # enough like a virtual-hosted-style bucket subdomain that
        # auto-detection could pick the wrong style. Path style is what
        # nginx's storage server block forwards untouched -- the bucket is
        # the first path segment, never part of the Host it matches on.
        config=Config(signature_version=_SIGNATURE_VERSION, s3={"addressing_style": "path"}),
    )


class MinioStorageAdapter:
    """Talks to MinIO over the S3 protocol (D1). Two clients, not one
    (D4): grants are signed against the address the browser reaches,
    queries and deletes go through the address the server reaches.
    """

    def __init__(self) -> None:
        self._browser_client = _client(storage_settings.minio_browser_endpoint)
        self._server_client = _client(storage_settings.minio_server_endpoint)
        self._bucket = storage_settings.minio_bucket

    @property
    def bucket(self) -> str:
        return self._bucket

    async def ensure_ready(self) -> None:
        """Creates the bucket when it's missing (D2). This is the
        provider the project runs itself, so creating its bucket is the
        project's own job -- the same guarantee `migrate` gives the
        schema.
        """
        if await self._bucket_exists():
            return
        try:
            await asyncio.to_thread(self._server_client.create_bucket, Bucket=self._bucket)
        except ClientError as exc:
            # Something else created it between the check above and this
            # call: the space is ready, which is all this promises.
            if exc.response.get("Error", {}).get("Code") in _ALREADY_CREATED_CODES:
                return
            raise StorageUnavailableError("could not prepare the object storage") from exc
        except BotoCoreError as exc:
            raise StorageUnavailableError("could not prepare the object storage") from exc

    async def _bucket_exists(self) -> bool:
        try:
            await asyncio.to_thread(self._server_client.head_bucket, Bucket=self._bucket)
        except ClientError as exc:
            if exc.response.get("Error", {}).get("Code") in _MISSING_BUCKET_CODES:
                return False
            raise StorageUnavailableError("could not reach the object storage") from exc
        except BotoCoreError as exc:
            raise StorageUnavailableError("could not reach the object storage") from exc
        return True

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
            # A PUT, not a POST with a policy (D9 in add-cloud-media-adapters):
            # no presigned URL, on any provider, can bound a size range, so
            # this signs only the object identity and the content type.
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
            # Split here, not by whoever calls this (D7): the S3 protocol
            # rejects a DeleteObjects request naming more than
            # DELETE_BATCH_LIMIT keys, and the two callers that can
            # exceed it -- periodic cleanup and deleting an album -- have
            # no way to know that limit without knowing which provider is
            # active, which is exactly what this port exists to hide.
            for batch in batched(object_keys, DELETE_BATCH_LIMIT):
                await asyncio.to_thread(
                    self._server_client.delete_objects,
                    Bucket=self._bucket,
                    Delete={"Objects": [{"Key": key} for key in batch], "Quiet": True},
                )
        except (BotoCoreError, ClientError) as exc:
            raise StorageUnavailableError("could not reach the object storage") from exc
