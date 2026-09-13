from src.images.adapters.imgproxy import ImgproxyAdapter

from .config import images_settings
from .port import ImagePort


def build_image_port() -> ImagePort:
    """The application's single point of provider selection: the rest of
    the code depends on `ImagePort` and never branches on which provider
    is active (image-delivery spec).
    """
    if images_settings.image_provider == "local":
        return ImgproxyAdapter()
    raise AssertionError(f"unhandled image provider {images_settings.image_provider!r}")


# Built at import time so an invalid selection fails the process's
# startup, not the first request for a variant.
image_port: ImagePort = build_image_port()
