from typing import Literal

from pydantic import BaseModel

from src.images.port import Variant

# Every variant's output format (D11): WebP wins over a more modern format
# on every one of the three, because the codec's cost falls exactly where
# this project's two real latencies live -- warming a variant on upload
# confirmation and the first view of a photo during the swipe -- and the
# codec is several times slower to encode for a saving that doesn't matter
# once a cache sits in front of it.
FORMAT: Literal["webp"] = "webp"


class VariantSpec(BaseModel):
    """A variant's full definition (D6, D11): it travels in the address
    the adapter builds, so changing any field here changes every address
    for that variant and invalidates what was cached under the old one --
    no separate invalidation mechanism needed (D7).
    """

    resize: Literal["fit", "fill"]
    width: int
    height: int
    quality: int
    # Only meaningful (and only set) for "fill": which part of the image
    # survives the crop.
    gravity: str | None = None


# The single declaration of these characteristics in the repository (task
# 4.2): the adapter reads this and builds the transformation the
# transformer receives already specified -- no presets configured on the
# transformer's own side (D6).
CATALOG: dict[Variant, VariantSpec] = {
    # The gallery grid is two columns of 170-210 logical px on a phone;
    # at high pixel density that calls for more than the 320px that once
    # looked sufficient. Cropped to a square: the grid doesn't need the
    # original aspect ratio.
    Variant.THUMBNAIL: VariantSpec(resize="fill", width=400, height=400, quality=75, gravity="ce"),
    # The rating card spans almost the full screen width, and what's being
    # judged is the whole photo -- cropping it would invalidate the
    # decision being made, so this one only fits, it never crops.
    Variant.RATING: VariantSpec(resize="fit", width=1080, height=1080, quality=82),
    # The viewer tolerates zooming in without the bytes stopping being
    # affordable on a phone.
    Variant.VIEWER: VariantSpec(resize="fit", width=2048, height=2048, quality=85),
}
