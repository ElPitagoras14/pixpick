import pytest
from pydantic import ValidationError

from src.storage.config import StorageSettings
from src.storage.factory import MissingCredentialsError, build_storage_port


def test_an_unrecognized_provider_fails_to_validate():
    """Startup fails naming the accepted values (object-storage spec):
    this is what a Literal's own validation error already does."""
    with pytest.raises(ValidationError):
        StorageSettings(storage_provider="bogus")


def test_the_local_provider_builds_successfully():
    assert build_storage_port() is not None


def test_local_provider_without_credentials_fails_to_start(monkeypatch):
    monkeypatch.setattr("src.storage.factory.storage_settings.storage_provider", "local")
    monkeypatch.setattr("src.storage.factory.storage_settings.minio_access_key_id", None)
    monkeypatch.setattr("src.storage.factory.storage_settings.minio_secret_access_key", None)

    with pytest.raises(
        MissingCredentialsError, match="MINIO_ACCESS_KEY_ID.*MINIO_SECRET_ACCESS_KEY"
    ):
        build_storage_port()


def test_r2_provider_without_credentials_fails_to_start(monkeypatch):
    monkeypatch.setattr("src.storage.factory.storage_settings.storage_provider", "r2")
    monkeypatch.setattr("src.storage.factory.storage_settings.r2_access_key_id", None)
    monkeypatch.setattr("src.storage.factory.storage_settings.r2_secret_access_key", None)

    with pytest.raises(MissingCredentialsError, match="R2_ACCESS_KEY_ID.*R2_SECRET_ACCESS_KEY"):
        build_storage_port()


def test_the_inactive_r2_providers_missing_credentials_do_not_block_local(monkeypatch):
    monkeypatch.setattr("src.storage.factory.storage_settings.storage_provider", "local")
    monkeypatch.setattr("src.storage.factory.storage_settings.r2_access_key_id", None)
    monkeypatch.setattr("src.storage.factory.storage_settings.r2_secret_access_key", None)

    assert build_storage_port() is not None


def test_naming_a_provider_explicitly_does_not_require_it_to_be_active(monkeypatch):
    """D6 in add-cloud-media-adapters: the migration check builds a port
    for a provider other than the active one, using that provider's own
    group of settings -- this only works because the two never share a
    field."""
    monkeypatch.setattr("src.storage.factory.storage_settings.storage_provider", "local")

    assert build_storage_port("r2") is not None
