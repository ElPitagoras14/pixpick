from sqlalchemy import text

from tests.factories import create_album, create_photo, create_session, create_user


async def test_create_user_needs_only_the_email(connection):
    """A test declares only what it cares about (backend-testing spec);
    every other column takes a valid default."""
    user = await create_user(connection, email="someone@example.com")

    assert user.id is not None


async def test_create_session_defaults_to_a_valid_unexpired_token(connection):
    user = await create_user(connection)

    session, token = await create_session(connection, user_id=user.id)

    assert session.id is not None
    assert token


async def test_an_album_with_photos_can_be_created_declaring_only_the_title(connection):
    """A test declares only what it cares about (task 1.5): a title, and
    however many photos, with every other column taking a valid default."""
    user = await create_user(connection)

    album = await create_album(connection, owner_id=user.id, title="Vacation")
    first_photo = await create_photo(connection, album_id=album.id)
    second_photo = await create_photo(connection, album_id=album.id)

    assert album.id is not None
    assert first_photo.id is not None
    assert second_photo.id is not None


async def test_create_photo_defaults_to_available(connection):
    user = await create_user(connection)
    album = await create_album(connection, owner_id=user.id)

    photo = await create_photo(connection, album_id=album.id)

    result = await connection.execute(
        text("select available, size from photos where id = :id"), {"id": photo.id}
    )
    available, size = result.one()
    assert available is True
    assert size is not None


async def test_create_photo_has_an_unavailable_variant(connection):
    user = await create_user(connection)
    album = await create_album(connection, owner_id=user.id)

    photo = await create_photo(connection, album_id=album.id, available=False)

    result = await connection.execute(
        text("select available, size from photos where id = :id"), {"id": photo.id}
    )
    available, size = result.one()
    assert available is False
    assert size is None
