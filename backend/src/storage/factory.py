from .adapters.minio import MinioStorageAdapter
from .adapters.r2 import R2StorageAdapter
from .config import storage_settings
from .port import StoragePort


class MissingCredentialsError(RuntimeError):
    """Raised when the named storage provider's own group of settings
    isn't fully filled in (same shape as `identity.factory`'s own).
    Evaluated only for the provider actually selected: MinIO's fields
    being empty never blocks startup while R2 is the one active, and
    the other way around.
    """


def build_storage_port(provider: str | None = None) -> StoragePort:
    """The application's single point of provider selection: the rest of
    the code depends on `StoragePort` and never branches on which
    provider is active (object-storage spec). Defaults to whichever
    provider is configured active; the migration check (D6 in
    add-cloud-media-adapters) is the one caller that names a provider
    explicitly, to build a port for a migration's destination without
    that becoming the active one -- which only works because each
    provider keeps its own group of settings (D9), so naming one never
    depends on it also being the active value.
    """
    selected = provider if provider is not None else storage_settings.storage_provider
    if selected == "local":
        missing = [
            name
            for name, value in (
                ("MINIO_ACCESS_KEY_ID", storage_settings.minio_access_key_id),
                ("MINIO_SECRET_ACCESS_KEY", storage_settings.minio_secret_access_key),
                ("MINIO_BUCKET", storage_settings.minio_bucket),
                ("MINIO_BROWSER_ENDPOINT", storage_settings.minio_browser_endpoint),
                ("MINIO_SERVER_ENDPOINT", storage_settings.minio_server_endpoint),
            )
            if not value
        ]
        if missing:
            raise MissingCredentialsError(
                f"the 'local' storage provider requires: {', '.join(missing)}"
            )
        return MinioStorageAdapter()
    if selected == "r2":
        missing = [
            name
            for name, value in (
                ("R2_ACCESS_KEY_ID", storage_settings.r2_access_key_id),
                ("R2_SECRET_ACCESS_KEY", storage_settings.r2_secret_access_key),
                ("R2_BUCKET", storage_settings.r2_bucket),
                ("R2_ENDPOINT", storage_settings.r2_endpoint),
            )
            if not value
        ]
        if missing:
            raise MissingCredentialsError(
                f"the 'r2' storage provider requires: {', '.join(missing)}"
            )
        return R2StorageAdapter()
    raise AssertionError(f"unhandled storage provider {selected!r}")


# Built at import time so an invalid selection fails the process's
# startup, not the first upload someone attempts.
storage_port: StoragePort = build_storage_port()
