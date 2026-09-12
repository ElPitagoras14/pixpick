import pytest
from pydantic import ValidationError

from src.storage.config import StorageSettings
from src.storage.factory import build_storage_port


def test_an_unrecognized_provider_fails_to_validate():
    """Startup fails naming the accepted values (object-storage spec):
    this is what a Literal's own validation error already does."""
    with pytest.raises(ValidationError):
        StorageSettings(
            storage_provider="bogus",
            storage_bucket="pixpick",
            storage_browser_endpoint="http://localhost:9000",
            storage_server_endpoint="http://localhost:9000",
            storage_root_user="key",
            storage_root_password="secret",
        )


def test_the_local_provider_builds_successfully():
    assert build_storage_port() is not None
