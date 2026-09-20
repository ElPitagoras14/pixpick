import typing

from src.storage.port import StoragePort, object_key


def test_the_port_has_exactly_the_four_operations_and_none_reads_content():
    """No operation returns bytes (D2): the transformer reads originals
    from the storage on its own. Preparing the storage is one of them,
    so the startup that calls it never names a provider. `bucket` is the
    one member that isn't an operation (task 7.1, harden-local-profile):
    a plain property naming the active provider's own space, not a call
    that reaches the network."""
    assert typing.get_protocol_members(StoragePort) == {
        "ensure_ready",
        "grant_upload",
        "get_object",
        "delete_objects",
        "bucket",
    }


def test_two_files_with_the_same_original_name_do_not_collide():
    first = object_key(album_id="album-1", photo_id="photo-1")
    second = object_key(album_id="album-1", photo_id="photo-2")

    assert first != second


def test_objects_of_the_same_album_share_a_prefix():
    first = object_key(album_id="album-1", photo_id="photo-1")
    second = object_key(album_id="album-1", photo_id="photo-2")
    other_album = object_key(album_id="album-2", photo_id="photo-1")

    common_prefix = f"albums/{'album-1'}/"
    assert first.startswith(common_prefix)
    assert second.startswith(common_prefix)
    assert not other_album.startswith(common_prefix)


def test_the_name_does_not_depend_on_anything_the_client_controls():
    """Only domain identifiers feed the name -- a client-declared
    filename never does, because the function doesn't even accept one."""
    key = object_key(album_id="album-1", photo_id="photo-1")

    assert "album-1" in key
    assert "photo-1" in key
