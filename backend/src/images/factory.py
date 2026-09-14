from .adapters.imagekit import ImageKitAdapter
from .adapters.imgproxy import ImgproxyAdapter
from .config import images_settings
from .port import ImagePort


class MissingCredentialsError(RuntimeError):
    """Raised when the active image provider requires credentials from an
    external system and they aren't configured (same shape as
    `identity.factory`'s own). Evaluated only for the provider that's
    actually selected: a provider that isn't active never blocks startup
    over credentials nothing is going to use.
    """


def build_image_port() -> ImagePort:
    """The application's single point of provider selection: the rest of
    the code depends on `ImagePort` and never branches on which provider
    is active (image-delivery spec).
    """
    if images_settings.image_provider == "local":
        missing = [
            name
            for name, value in (
                ("IMAGE_SIGNING_KEY", images_settings.image_signing_key),
                ("IMAGE_SIGNING_SALT", images_settings.image_signing_salt),
            )
            if not value
        ]
        if missing:
            raise MissingCredentialsError(
                f"the 'local' image provider requires: {', '.join(missing)}"
            )
        return ImgproxyAdapter()
    if images_settings.image_provider == "imagekit":
        missing = [
            name
            for name, value in (
                ("IMAGEKIT_URL_ENDPOINT", images_settings.imagekit_url_endpoint),
                ("IMAGEKIT_PRIVATE_KEY", images_settings.imagekit_private_key),
            )
            if not value
        ]
        if missing:
            raise MissingCredentialsError(
                f"the 'imagekit' image provider requires: {', '.join(missing)}"
            )
        return ImageKitAdapter()
    raise AssertionError(f"unhandled image provider {images_settings.image_provider!r}")


# Built at import time so an invalid selection fails the process's
# startup, not the first request for a variant.
image_port: ImagePort = build_image_port()
