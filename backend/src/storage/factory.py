from src.storage.adapters.minio import MinioStorageAdapter
from src.storage.config import storage_settings
from src.storage.port import StoragePort


def build_storage_port() -> StoragePort:
    """The application's single point of provider selection: the rest of
    the code depends on `StoragePort` and never branches on which
    provider is active (object-storage spec).
    """
    if storage_settings.storage_provider == "local":
        return MinioStorageAdapter()
    raise AssertionError(f"unhandled storage provider {storage_settings.storage_provider!r}")


# Built at import time so an invalid selection fails the process's
# startup, not the first upload someone attempts.
storage_port: StoragePort = build_storage_port()
