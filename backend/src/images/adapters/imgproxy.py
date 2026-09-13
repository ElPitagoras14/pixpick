import base64
import hashlib
import hmac

from src.config import settings
from src.images.catalog import CATALOG, FORMAT
from src.images.config import images_settings
from src.images.port import Variant
from src.storage.config import storage_settings

# Must match nginx's images location block (nginx/nginx.conf) -- the
# same relationship the backend's own "/api" prefix has with nginx's
# API location (src/routes.py), hardcoded on both sides rather than
# configured, since it's an internal wiring detail, not an environment
# difference.
_IMAGES_PATH_PREFIX = "/images"


def _b64url(data: bytes) -> str:
    """URL-safe Base64 without padding -- what imgproxy expects for both
    the encoded source URL and the signature."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _sign(path: str) -> str:
    """A URL-safe Base64 HMAC-SHA256 digest of the salt followed by the
    path, per imgproxy's own signing algorithm."""
    key = bytes.fromhex(images_settings.image_signing_key)
    salt = bytes.fromhex(images_settings.image_signing_salt)
    digest = hmac.new(key, salt + path.encode(), hashlib.sha256).digest()
    return _b64url(digest)


def _processing_options(variant: Variant) -> str:
    spec = CATALOG[variant]
    options = [f"rs:{spec.resize}:{spec.width}:{spec.height}:0", f"q:{spec.quality}"]
    if spec.gravity is not None:
        options.append(f"g:{spec.gravity}")
    return "/".join(options)


class ImgproxyAdapter:
    """Builds and signs imgproxy addresses (D6). Never calls imgproxy or
    the storage: the transformer reads the original from the storage on
    its own the first time a given address is requested (D2).
    """

    def variant_url(self, *, object_key: str, variant: Variant) -> str:
        # The bucket comes from the storage's own config rather than a
        # second variable that would just have to be kept in sync with it:
        # the transformer and the storage adapter must agree on where
        # originals live, so there's exactly one place that says so.
        source = f"s3://{storage_settings.minio_bucket}/{object_key}"
        encoded_source = _b64url(source.encode())
        path = f"/{_processing_options(variant)}/{encoded_source}.{FORMAT}"
        signature = _sign(path)
        return f"{settings.public_url}{_IMAGES_PATH_PREFIX}/{signature}{path}"
