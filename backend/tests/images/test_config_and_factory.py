import pytest
from pydantic import ValidationError

from src.images.config import ImagesSettings
from src.images.factory import (
    IncompatibleProviderCombinationError,
    MissingCredentialsError,
    build_image_port,
)


def test_an_unrecognized_provider_fails_to_validate():
    """Startup fails naming the accepted values: this is what a Literal's
    own validation error already does."""
    with pytest.raises(ValidationError):
        ImagesSettings(image_provider="bogus", image_signing_key="ab", image_signing_salt="cd")


def test_the_local_provider_builds_successfully():
    assert build_image_port() is not None


def test_local_provider_without_credentials_fails_to_start(monkeypatch):
    monkeypatch.setattr("src.images.factory.images_settings.image_provider", "local")
    monkeypatch.setattr("src.images.factory.images_settings.image_signing_key", None)
    monkeypatch.setattr("src.images.factory.images_settings.image_signing_salt", None)

    with pytest.raises(MissingCredentialsError, match="IMAGE_SIGNING_KEY.*IMAGE_SIGNING_SALT"):
        build_image_port()


def test_imagekit_provider_without_credentials_fails_to_start(monkeypatch):
    monkeypatch.setattr("src.images.factory.images_settings.image_provider", "imagekit")
    monkeypatch.setattr("src.images.factory.images_settings.imagekit_url_endpoint", None)
    monkeypatch.setattr("src.images.factory.images_settings.imagekit_private_key", None)

    with pytest.raises(
        MissingCredentialsError, match="IMAGEKIT_URL_ENDPOINT.*IMAGEKIT_PRIVATE_KEY"
    ):
        build_image_port()


def test_imagekit_provider_is_built_once_credentials_are_present(monkeypatch):
    monkeypatch.setattr("src.images.factory.images_settings.image_provider", "imagekit")
    monkeypatch.setattr(
        "src.images.factory.images_settings.imagekit_url_endpoint", "https://ik.imagekit.io/demo"
    )
    monkeypatch.setattr("src.images.factory.images_settings.imagekit_private_key", "a-private-key")

    assert build_image_port() is not None


def test_the_inactive_imagekit_providers_missing_credentials_do_not_block_local(monkeypatch):
    monkeypatch.setattr("src.images.factory.images_settings.image_provider", "local")
    monkeypatch.setattr("src.images.factory.images_settings.imagekit_url_endpoint", None)
    monkeypatch.setattr("src.images.factory.images_settings.imagekit_private_key", None)

    assert build_image_port() is not None


# The combination guard. The transformer this project runs itself is wired
# at the compose level to reach only this same environment's own storage, so
# the 'local' image provider only ever works paired with the 'local' storage
# provider -- every other combination either works (imagekit is external and
# its own reachability isn't this project's to verify) or is rejected
# outright.


def test_local_image_with_local_storage_is_admitted(monkeypatch):
    monkeypatch.setattr("src.images.factory.images_settings.image_provider", "local")
    monkeypatch.setattr("src.images.factory.storage_settings.storage_provider", "local")

    assert build_image_port() is not None


def test_local_image_with_a_non_local_storage_fails_to_start(monkeypatch):
    monkeypatch.setattr("src.images.factory.images_settings.image_provider", "local")
    monkeypatch.setattr("src.images.factory.storage_settings.storage_provider", "r2")

    with pytest.raises(IncompatibleProviderCombinationError, match="STORAGE_PROVIDER"):
        build_image_port()


def test_imagekit_image_with_r2_storage_is_admitted(monkeypatch):
    """The cloud pair: both external, neither wired to this environment's
    own storage."""
    monkeypatch.setattr("src.images.factory.images_settings.image_provider", "imagekit")
    monkeypatch.setattr("src.images.factory.storage_settings.storage_provider", "r2")
    monkeypatch.setattr(
        "src.images.factory.images_settings.imagekit_url_endpoint", "https://ik.imagekit.io/demo"
    )
    monkeypatch.setattr("src.images.factory.images_settings.imagekit_private_key", "a-private-key")

    assert build_image_port() is not None


def test_imagekit_image_with_local_storage_is_admitted(monkeypatch):
    """Not rejected: ImageKit is an external service, and whether its own
    configured origin can reach this environment's storage isn't
    something this project's own startup can verify -- only the 'local'
    image provider's fixed wiring is."""
    monkeypatch.setattr("src.images.factory.images_settings.image_provider", "imagekit")
    monkeypatch.setattr("src.images.factory.storage_settings.storage_provider", "local")
    monkeypatch.setattr(
        "src.images.factory.images_settings.imagekit_url_endpoint", "https://ik.imagekit.io/demo"
    )
    monkeypatch.setattr("src.images.factory.images_settings.imagekit_private_key", "a-private-key")

    assert build_image_port() is not None
