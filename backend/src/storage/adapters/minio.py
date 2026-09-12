import asyncio

import boto3
from botocore.client import Config
from botocore.exceptions import BotoCoreError, ClientError

from src.storage.config import storage_settings
from src.storage.exceptions import StorageUnavailableError
from src.storage.port import ObjectMetadata, UploadGrant, object_key

# S3-compatible providers reject a v2-signed request; MinIO and Cloudflare
# R2 both require v4 (the future cloud change reuses this same adapter
# shape, per the proposal's Impact section).
_SIGNATURE_VERSION = "s3v4"


def _client(endpoint: str):
    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=storage_settings.storage_root_user,
        aws_secret_access_key=storage_settings.storage_root_password,
        config=Config(signature_version=_SIGNATURE_VERSION),
    )


class MinioStorageAdapter:
    """Talks to MinIO over the S3 protocol (D1). Two clients, not one
    (D4): grants are signed against the address the browser reaches,
    queries and deletes go through the address the server reaches.
    """

    def __init__(self) -> None:
        self._browser_client = _client(storage_settings.storage_browser_endpoint)
        self._server_client = _client(storage_settings.storage_server_endpoint)
        self._bucket = storage_settings.storage_bucket

    def grant_upload(
        self,
        *,
        album_id: str,
        photo_id: str,
        content_type: str,
        max_size: int,
        ttl_seconds: int,
    ) -> UploadGrant:
        key = object_key(album_id=album_id, photo_id=photo_id)
        try:
            # Pure local signing (D8): no request leaves the process here.
            presigned = self._browser_client.generate_presigned_post(
                Bucket=self._bucket,
                Key=key,
                Fields={"Content-Type": content_type},
                Conditions=[
                    {"Content-Type": content_type},
                    ["content-length-range", 0, max_size],
                ],
                ExpiresIn=ttl_seconds,
            )
        except (BotoCoreError, ClientError) as exc:
            raise StorageUnavailableError("could not prepare the upload grant") from exc
        return UploadGrant(url=presigned["url"], fields=presigned["fields"], object_key=key)

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
            await asyncio.to_thread(
                self._server_client.delete_objects,
                Bucket=self._bucket,
                Delete={"Objects": [{"Key": key} for key in object_keys], "Quiet": True},
            )
        except (BotoCoreError, ClientError) as exc:
            raise StorageUnavailableError("could not reach the object storage") from exc
