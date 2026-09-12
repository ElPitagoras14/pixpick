from src.images.catalog import CATALOG, FORMAT
from src.images.port import Variant


def test_every_variant_is_declared_exactly_once():
    assert set(CATALOG.keys()) == set(Variant)


def test_output_format_is_webp_for_every_variant():
    assert FORMAT == "webp"


def test_the_thumbnail_crops_to_a_square():
    spec = CATALOG[Variant.THUMBNAIL]
    assert spec.resize == "fill"
    assert spec.width == spec.height == 400


def test_the_rating_and_viewer_variants_never_crop():
    for variant in (Variant.RATING, Variant.VIEWER):
        assert CATALOG[variant].resize == "fit"
