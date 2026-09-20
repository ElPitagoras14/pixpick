from src.storage.config import storage_settings

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


class IncompatibleProviderCombinationError(RuntimeError):
    """Raised when the selected storage and image providers can't be
    made to work together in this environment (image-delivery spec, D10
    in harden-local-profile's design): the transformer this project runs
    itself is wired, at the compose level, only to this same environment's
    own storage -- parametrizing it to reach an external provider instead
    is out of scope, left for the cloud profile's own hardening.
    """


def build_image_port() -> ImagePort:
    """The application's single point of provider selection: the rest of
    the code depends on `ImagePort` and never branches on which provider
    is active (image-delivery spec).
    """
    if images_settings.image_provider == "local":
        if storage_settings.storage_provider != "local":
            # Caught here, not by a fixed address failing to resolve
            # later (D10): the transformer's own compose wiring
            # (IMGPROXY_S3_ENDPOINT) always points at this environment's
            # storage service, regardless of which provider
            # STORAGE_PROVIDER actually names, so this pair can never
            # produce a variant no matter how correctly the address
            # names the active bucket.
            raise IncompatibleProviderCombinationError(
                "the 'local' image provider only reaches this environment's own "
                f"storage; STORAGE_PROVIDER is {storage_settings.storage_provider!r}, "
                "not 'local'"
            )
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
