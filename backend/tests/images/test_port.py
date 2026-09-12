import typing

from src.images.port import ImagePort, Variant


def test_the_port_has_exactly_one_operation():
    assert typing.get_protocol_members(ImagePort) == {"variant_url"}


def test_the_variant_set_is_closed():
    assert {member.value for member in Variant} == {"thumbnail", "rating", "viewer"}
