from enum import StrEnum
from typing import Protocol


class Variant(StrEnum):
    """The closed set of named variants (image-delivery spec). Nothing
    outside `src/images/catalog.py` names a size, a quality, or a format
    -- a consumer names one of these and nothing else.
    """

    THUMBNAIL = "thumbnail"
    RATING = "rating"
    VIEWER = "viewer"


class ImagePort(Protocol):
    """The single operation any image transformer provider offers
    (image-delivery spec). Synchronous and side-effect free: building and
    signing an address is local computation, so it never talks to the
    transformer or the storage.
    """

    def variant_url(self, *, object_key: str, variant: Variant) -> str:
        """The full, signed address of `variant` for the object at
        `object_key`. Doesn't say whether it resolves through nginx's
        cache or a third party's CDN -- callers don't need to know."""
        ...
