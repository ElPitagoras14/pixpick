import pytest
from pydantic import ValidationError

from src.images.config import ImagesSettings
from src.images.factory import build_image_port


def test_an_unrecognized_provider_fails_to_validate():
    """Startup fails naming the accepted values (image-delivery spec):
    this is what a Literal's own validation error already does."""
    with pytest.raises(ValidationError):
        ImagesSettings(image_provider="bogus", image_signing_key="ab", image_signing_salt="cd")


def test_the_local_provider_builds_successfully():
    assert build_image_port() is not None
