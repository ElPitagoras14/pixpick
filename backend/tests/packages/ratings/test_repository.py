from src.packages.ratings import repository
from tests.factories import create_album, create_photo, create_rating, create_user


async def test_list_pending_photos_excludes_already_rated_ones(connection):
    user = await create_user(connection)
    album = await create_album(connection, owner_id=user.id)
    rated = await create_photo(connection, album_id=album.id, position=1)
    pending = await create_photo(connection, album_id=album.id, position=2)
    await create_rating(connection, photo_id=rated.id, user_id=user.id, approved=True)

    rows = await repository.list_pending_photos(connection, album_id=album.id, user_id=user.id)

    assert [row.id for row in rows] == [pending.id]


async def test_list_pending_photos_is_in_album_order(connection):
    user = await create_user(connection)
    album = await create_album(connection, owner_id=user.id)
    third = await create_photo(connection, album_id=album.id, position=3)
    first = await create_photo(connection, album_id=album.id, position=1)
    second = await create_photo(connection, album_id=album.id, position=2)

    rows = await repository.list_pending_photos(connection, album_id=album.id, user_id=user.id)

    assert [row.id for row in rows] == [first.id, second.id, third.id]


async def test_list_pending_photos_excludes_unavailable_photos(connection):
    user = await create_user(connection)
    album = await create_album(connection, owner_id=user.id)
    await create_photo(connection, album_id=album.id, position=1, available=False)

    rows = await repository.list_pending_photos(connection, album_id=album.id, user_id=user.id)

    assert rows == []


async def test_each_person_has_their_own_independent_pending_set(connection):
    owner = await create_user(connection)
    other = await create_user(connection)
    album = await create_album(connection, owner_id=owner.id)
    photo = await create_photo(connection, album_id=album.id, position=1)
    await create_rating(connection, photo_id=photo.id, user_id=owner.id, approved=True)

    owner_pending = await repository.list_pending_photos(
        connection, album_id=album.id, user_id=owner.id
    )
    other_pending = await repository.list_pending_photos(
        connection, album_id=album.id, user_id=other.id
    )

    assert owner_pending == []
    assert [row.id for row in other_pending] == [photo.id]


async def test_photo_is_available_in_album_is_false_for_an_unavailable_photo(connection):
    user = await create_user(connection)
    album = await create_album(connection, owner_id=user.id)
    photo = await create_photo(connection, album_id=album.id, position=1, available=False)

    assert (
        await repository.photo_is_available_in_album(
            connection, album_id=album.id, photo_id=photo.id
        )
        is False
    )


async def test_photo_is_available_in_album_is_false_for_a_foreign_photo(connection):
    user = await create_user(connection)
    album = await create_album(connection, owner_id=user.id)
    other_album = await create_album(connection, owner_id=user.id)
    photo = await create_photo(connection, album_id=other_album.id, position=1)

    assert (
        await repository.photo_is_available_in_album(
            connection, album_id=album.id, photo_id=photo.id
        )
        is False
    )


async def test_upsert_rating_repeating_the_same_value_changes_nothing(connection):
    user = await create_user(connection)
    album = await create_album(connection, owner_id=user.id)
    photo = await create_photo(connection, album_id=album.id, position=1)

    first = await repository.upsert_rating(
        connection, photo_id=photo.id, user_id=user.id, approved=True
    )
    second = await repository.upsert_rating(
        connection, photo_id=photo.id, user_id=user.id, approved=True
    )

    assert first.id == second.id
    assert second.approved is True


async def test_upsert_rating_the_opposite_value_replaces_it(connection):
    user = await create_user(connection)
    album = await create_album(connection, owner_id=user.id)
    photo = await create_photo(connection, album_id=album.id, position=1)

    first = await repository.upsert_rating(
        connection, photo_id=photo.id, user_id=user.id, approved=True
    )
    second = await repository.upsert_rating(
        connection, photo_id=photo.id, user_id=user.id, approved=False
    )

    # Same row (the schema's own unique key resolved the conflict, D3),
    # its value replaced -- never a second rating alongside the first.
    assert first.id == second.id
    assert second.approved is False
