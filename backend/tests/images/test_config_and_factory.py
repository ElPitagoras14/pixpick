import pytest
from pydantic import ValidationError

from src.images.config import ImagesSettings
from src.images.factory import MissingCredentialsError, build_image_port


def test_an_unrecognized_provider_fails_to_validate():
    """Startup fails naming the accepted values (image-delivery spec):
    this is what a Literal's own validation error already does."""
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
