import hashlib
import hmac

from src.images.catalog import CATALOG, FORMAT
from src.images.config import images_settings
from src.images.port import Variant

# A signed ImageKit address always carries an expiry (ik-t) -- there is no
# documented way to sign one without it. Variant addresses aren't meant to
# expire at all (D7 in add-media-ports-and-local-adapters: a catalog change
# invalidates a variant by producing a new address, never by a clock), so
# this is a fixed point far enough in the future to behave as permanent --
# the same placeholder ImageKit's own documentation uses for this case.
_NEVER_EXPIRES = 9999999999


def _transformation(variant: Variant) -> str:
    spec = CATALOG[variant]
    if spec.resize == "fill":
        # "extract" crops to the exact box from its default focus, the
        # center -- the only gravity this catalog ever declares, so no
        # separate `fo-` is needed.
        parts = [f"w-{spec.width}", f"h-{spec.height}", "cm-extract"]
    else:
        # "at_max" fits entirely inside the box, preserving aspect ratio,
        # and (per ImageKit's own docs) never enlarges an original smaller
        # than the box -- the same "never enlarge" rule imgproxy's own
        # `:0` flag gives the `fit` variants (D11 in
        # add-media-ports-and-local-adapters).
        parts = [f"w-{spec.width}", f"h-{spec.height}", "c-at_max"]
    parts.append(f"q-{spec.quality}")
    parts.append(f"f-{FORMAT}")
    return ",".join(parts)


def _sign(path: str) -> str:
    """A URL-safe hex HMAC-SHA1 digest of the path (with its expiry
    appended) using the account's private key, per ImageKit's own signing
    algorithm."""
    key = images_settings.imagekit_private_key.encode()
    message = f"{path}{_NEVER_EXPIRES}".encode()
    return hmac.new(key, message, hashlib.sha1).hexdigest()


class ImageKitAdapter:
    """Builds and signs ImageKit addresses (D1, D9 in
    add-cloud-media-adapters). Never calls ImageKit or the storage: the
    transformer reads the original from the storage account it's
    configured against on its own, the first time a given address is
    requested (D2 in add-media-ports-and-local-adapters).
    """

    def variant_url(self, *, object_key: str, variant: Variant) -> str:
        path = f"/tr:{_transformation(variant)}/{object_key}"
        signature = _sign(path)
        endpoint = images_settings.imagekit_url_endpoint.rstrip("/")
        return f"{endpoint}{path}?ik-t={_NEVER_EXPIRES}&ik-s={signature}"
