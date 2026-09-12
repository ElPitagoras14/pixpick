import base64
import socket

from src.images.adapters.imgproxy import ImgproxyAdapter
from src.images.catalog import CATALOG
from src.images.port import Variant
from src.storage.config import storage_settings


def _decode_source(url: str) -> str:
    path_part = url.split("/images/", 1)[1]
    encoded = path_part.rsplit("/", 1)[-1].rsplit(".", 1)[0]
    padded = encoded + "=" * (-len(encoded) % 4)
    return base64.urlsafe_b64decode(padded).decode()


def test_building_every_variant_address_emits_no_network_request(monkeypatch):
    """Also stands in for "an entire album's worth of addresses": building
    many is still zero requests (image-delivery spec)."""

    def _forbidden_connect(*_args, **_kwargs):
        raise AssertionError("variant_url must not open any connection")

    monkeypatch.setattr(socket.socket, "connect", _forbidden_connect)

    adapter = ImgproxyAdapter()
    urls = [adapter.variant_url(object_key="albums/a/p", variant=variant) for variant in Variant]

    assert len(urls) == len(list(Variant))


def test_the_address_encodes_the_bucket_and_object_key():
    adapter = ImgproxyAdapter()
    url = adapter.variant_url(object_key="albums/a/p", variant=Variant.THUMBNAIL)

    assert _decode_source(url) == f"s3://{storage_settings.storage_bucket}/albums/a/p"


def test_the_address_is_stable_for_the_same_input():
    adapter = ImgproxyAdapter()
    first = adapter.variant_url(object_key="albums/a/p", variant=Variant.VIEWER)
    second = adapter.variant_url(object_key="albums/a/p", variant=Variant.VIEWER)

    assert first == second


def test_changing_a_variant_definition_changes_its_address(monkeypatch):
    """The regression D7 depends on: presets would make this fail, since
    the transformer -- not the address -- would own the definition."""
    adapter = ImgproxyAdapter()
    before = adapter.variant_url(object_key="albums/a/p", variant=Variant.RATING)

    monkeypatch.setitem(
        CATALOG,
        Variant.RATING,
        CATALOG[Variant.RATING].model_copy(update={"width": 900, "height": 900}),
    )
    after = adapter.variant_url(object_key="albums/a/p", variant=Variant.RATING)

    assert before != after
