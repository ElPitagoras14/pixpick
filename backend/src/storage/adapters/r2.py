import asyncio

import boto3
from botocore.client import Config
from botocore.exceptions import BotoCoreError, ClientError

from src.storage.config import storage_settings
from src.storage.exceptions import StorageNotReadyError, StorageUnavailableError
from src.storage.port import DELETE_BATCH_LIMIT, ObjectMetadata, UploadGrant, batched, object_key

_SIGNATURE_VERSION = "s3v4"

_MISSING_BUCKET_CODES = ("404", "NoSuchBucket")

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
    """The same S3 protocol `MinioStorageAdapter` speaks; only the client's
    configuration differs. Two clients for the same `r2_endpoint`: R2 is
    reached the same way from both sides, so one field serves both."""

    def __init__(self) -> None:
        self._browser_client = _client()
        self._server_client = _client()
        self._bucket = storage_settings.r2_bucket

    @property
    def bucket(self) -> str:
        return self._bucket

    async def ensure_ready(self) -> None:
        """Checks, never creates: the bucket is made once at the provider,
        so its absence is a configuration error, and creating a paid
        resource is not this application's call."""
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
            # Signed locally: no request leaves the process. A PUT, not a
            # POST with a policy, which R2 doesn't implement at all.
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
            # Split here, not by the caller: S3 rejects a DeleteObjects
            # naming more than DELETE_BATCH_LIMIT keys, and a caller would
            # have to know the active provider to know that limit.
            for batch in batched(object_keys, DELETE_BATCH_LIMIT):
                await asyncio.to_thread(
                    self._server_client.delete_objects,
                    Bucket=self._bucket,
                    Delete={"Objects": [{"Key": key} for key in batch], "Quiet": True},
                )
        except (BotoCoreError, ClientError) as exc:
            raise StorageUnavailableError("could not reach the object storage") from exc
