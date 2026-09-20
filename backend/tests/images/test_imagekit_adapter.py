import socket

from src.images.adapters.imagekit import ImageKitAdapter
from src.images.catalog import CATALOG
from src.images.port import Variant


def _adapter(monkeypatch) -> ImageKitAdapter:
    monkeypatch.setattr(
        "src.images.adapters.imagekit.images_settings.imagekit_url_endpoint",
        "https://ik.imagekit.io/demo",
    )
    monkeypatch.setattr(
        "src.images.adapters.imagekit.images_settings.imagekit_private_key", "a-private-key"
    )
    return ImageKitAdapter()


def test_building_every_variant_address_emits_no_network_request(monkeypatch):
    def _forbidden_connect(*_args, **_kwargs):
        raise AssertionError("variant_url must not open any connection")

    monkeypatch.setattr(socket.socket, "connect", _forbidden_connect)
    adapter = _adapter(monkeypatch)

    urls = [adapter.variant_url(object_key="albums/a/p", variant=variant) for variant in Variant]

    assert len(urls) == len(list(Variant))


def test_the_address_names_the_endpoint_the_object_key_and_a_signature(monkeypatch):
    adapter = _adapter(monkeypatch)

    url = adapter.variant_url(object_key="albums/a/p", variant=Variant.THUMBNAIL)

    assert url.startswith("https://ik.imagekit.io/demo/tr:")
    path, query = url.split("?", 1)
    assert path.endswith("/albums/a/p")
    assert "ik-t=9999999999" in query
    assert "ik-s=" in query


def test_the_address_is_stable_for_the_same_input(monkeypatch):
    adapter = _adapter(monkeypatch)

    first = adapter.variant_url(object_key="albums/a/p", variant=Variant.VIEWER)
    second = adapter.variant_url(object_key="albums/a/p", variant=Variant.VIEWER)

    assert first == second


def test_tampering_the_object_key_invalidates_the_signature(monkeypatch):
    """Mirrors imgproxy's own tampering test: this adapter never talks to
    ImageKit, so what's verifiable here is that the signature for the
    tampered path differs from the original -- ImageKit itself is what
    rejects a mismatched one on request."""
    adapter = _adapter(monkeypatch)
    original = adapter.variant_url(object_key="albums/a/p", variant=Variant.THUMBNAIL)
    tampered = adapter.variant_url(object_key="albums/a/other", variant=Variant.THUMBNAIL)

    original_signature = original.rsplit("ik-s=", 1)[1]
    tampered_signature = tampered.rsplit("ik-s=", 1)[1]

    assert original_signature != tampered_signature


def test_changing_a_variant_definition_changes_its_address(monkeypatch):
    """Presets would make this fail, since the transformer -- not the
    address -- would own the definition."""
    adapter = _adapter(monkeypatch)
    before = adapter.variant_url(object_key="albums/a/p", variant=Variant.RATING)

    monkeypatch.setitem(
        CATALOG,
        Variant.RATING,
        CATALOG[Variant.RATING].model_copy(update={"width": 900, "height": 900}),
    )
    after = adapter.variant_url(object_key="albums/a/p", variant=Variant.RATING)

    assert before != after


def test_the_fill_variant_uses_the_extract_crop_mode(monkeypatch):
    """ImageKit's "extract" crop mode is the "fill" equivalent -- it crops
    to the exact box, centered by default, matching the only gravity this
    catalog declares."""
    adapter = _adapter(monkeypatch)

    url = adapter.variant_url(object_key="albums/a/p", variant=Variant.THUMBNAIL)

    assert "cm-extract" in url


def test_a_fit_variant_uses_the_at_max_crop_strategy(monkeypatch):
    adapter = _adapter(monkeypatch)

    url = adapter.variant_url(object_key="albums/a/p", variant=Variant.RATING)

    assert "c-at_max" in url
