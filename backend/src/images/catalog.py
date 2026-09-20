from typing import Literal

from pydantic import BaseModel

from .port import Variant

# WebP over a newer codec on all three: this project's latencies are
# warming a variant on confirmation and the first view during a swipe, and
# a slower encode buys a saving a cache in front already makes moot.
FORMAT: Literal["webp"] = "webp"


class VariantSpec(BaseModel):
    """Travels in the address the adapter builds, so changing a field here
    changes every address for that variant -- which is what invalidates the
    old cache entries."""

    resize: Literal["fit", "fill"]
    width: int
    height: int
    quality: int
    # Only set for "fill": which part of the image survives the crop.
    gravity: str | None = None


# The one declaration of these: the adapter builds a fully specified
# transformation from it, so the transformer has no presets of its own.
CATALOG: dict[Variant, VariantSpec] = {
    # Two columns of 170-210 logical px on a phone, so high pixel density
    # needs more than 320. Square: the grid doesn't need the real ratio.
    Variant.THUMBNAIL: VariantSpec(resize="fill", width=400, height=400, quality=75, gravity="ce"),
    # What's being judged is the whole photo, so this one only fits: a crop
    # would invalidate the decision.
    Variant.RATING: VariantSpec(resize="fit", width=1080, height=1080, quality=82),
    # Enough to zoom into, still affordable on a phone.
    Variant.VIEWER: VariantSpec(resize="fit", width=2048, height=2048, quality=85),
}
