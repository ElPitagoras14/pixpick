from datetime import UTC, datetime, timedelta

from src.database.client import fetch_val
from src.packages.albums import repository as albums_repository
from src.packages.photos import repository
from tests.factories import create_album, create_photo, create_user


async def test_count_occupied_slots_counts_available_and_pending_with_a_live_grant(connection):
    user = await create_user(connection)
    album = await create_album(connection, owner_id=user.id)
    await create_photo(connection, album_id=album.id, position=1, available=True)
    await create_photo(
        connection,
        album_id=album.id,
        position=2,
        available=False,
        upload_expires_at=datetime.now(UTC) + timedelta(minutes=5),
    )
    # Expired and still pending: no longer occupies a slot (D14).
    await create_photo(
        connection,
        album_id=album.id,
        position=3,
        available=False,
        upload_expires_at=datetime.now(UTC) - timedelta(minutes=5),
    )

    count = await repository.count_occupied_slots(connection, album_id=album.id)

    assert count == 2


async def test_next_position_continues_after_the_existing_photos(connection):
    user = await create_user(connection)
    album = await create_album(connection, owner_id=user.id)

    assert await repository.next_position(connection, album_id=album.id) == 1

    await create_photo(connection, album_id=album.id, position=1)
    await create_photo(connection, album_id=album.id, position=2)

    assert await repository.next_position(connection, album_id=album.id) == 3


async def test_list_available_photos_excludes_unavailable_ones_and_orders_by_position(connection):
    user = await create_user(connection)
    album = await create_album(connection, owner_id=user.id)
    second = await create_photo(connection, album_id=album.id, position=2)
    first = await create_photo(connection, album_id=album.id, position=1)
    await create_photo(connection, album_id=album.id, position=3, available=False)

    rows = await repository.list_available_photos(connection, album_id=album.id)

    assert [row.id for row in rows] == [first.id, second.id]


async def test_get_owned_photos_is_none_for_a_foreign_album(connection):
    owner = await create_user(connection)
    stranger = await create_user(connection)
    album = await create_album(connection, owner_id=owner.id)
    photo = await create_photo(connection, album_id=album.id, position=1)

    result = await repository.get_owned_photos(
        connection, album_id=album.id, owner_id=stranger.id, photo_ids=[photo.id]
    )

    assert result is None


async def test_get_owned_photos_silently_skips_ids_that_are_not_the_albums_own(connection):
    user = await create_user(connection)
    album = await create_album(connection, owner_id=user.id)
    other_album = await create_album(connection, owner_id=user.id)
    own_photo = await create_photo(connection, album_id=album.id, position=1)
    foreign_photo = await create_photo(connection, album_id=other_album.id, position=1)

    result = await repository.get_owned_photos(
        connection, album_id=album.id, owner_id=user.id, photo_ids=[own_photo.id, foreign_photo.id]
    )

    assert result is not None
    assert [row.id for row in result] == [own_photo.id]


async def test_mark_photo_available_sets_the_real_size(connection):
    user = await create_user(connection)
    album = await create_album(connection, owner_id=user.id)
    photo = await create_photo(connection, album_id=album.id, position=1, available=False)

    await repository.mark_photo_available(connection, photo_id=photo.id, size=12345)

    rows = await repository.get_owned_photos(
        connection, album_id=album.id, owner_id=user.id, photo_ids=[photo.id]
    )
    assert rows[0].available is True
    assert rows[0].size == 12345


async def test_delete_owned_photo_is_false_for_a_foreign_photo(connection):
    owner = await create_user(connection)
    stranger = await create_user(connection)
    album = await create_album(connection, owner_id=owner.id)
    photo = await create_photo(connection, album_id=album.id, position=1)

    deleted = await repository.delete_owned_photo(
        connection, album_id=album.id, owner_id=stranger.id, photo_id=photo.id
    )

    assert deleted is False


async def test_delete_owned_photo_removes_it(connection):
    user = await create_user(connection)
    album = await create_album(connection, owner_id=user.id)
    photo = await create_photo(connection, album_id=album.id, position=1)

    deleted = await repository.delete_owned_photo(
        connection, album_id=album.id, owner_id=user.id, photo_id=photo.id
    )

    assert deleted is True
    remaining = await repository.get_owned_photos(
        connection, album_id=album.id, owner_id=user.id, photo_ids=[photo.id]
    )
    assert remaining == []


async def test_expired_pending_photo_ids_only_returns_unavailable_and_expired(connection):
    user = await create_user(connection)
    album = await create_album(connection, owner_id=user.id)
    expired_pending = await create_photo(
        connection,
        album_id=album.id,
        position=1,
        available=False,
        upload_expires_at=datetime.now(UTC) - timedelta(minutes=1),
    )
    await create_photo(
        connection,
        album_id=album.id,
        position=2,
        available=False,
        upload_expires_at=datetime.now(UTC) + timedelta(minutes=5),
    )
    await create_photo(connection, album_id=album.id, position=3, available=True)

    rows = await repository.expired_pending_photo_ids(connection)

    assert [row.id for row in rows] == [expired_pending.id]


async def test_confirming_and_renewing_roll_back_together(connection):
    """D4 in album-retention's design: marking a photo available and
    restarting its album's plazo happen in the same transaction
    (`photos.service.confirm_batch`); this exercises that transaction's
    boundary directly, the way `test_data_access.py`'s atomic tests do,
    a failure that undoes the first SHALL undo the second too.
    """
    user = await create_user(connection)
    original_renewed_at = datetime.now(UTC) - timedelta(days=10)
    album = await create_album(connection, owner_id=user.id, renewed_at=original_renewed_at)
    photo = await create_photo(connection, album_id=album.id, available=False)

    savepoint = await connection.begin_nested()
    await repository.mark_photo_available(connection, photo_id=photo.id, size=123)
    await albums_repository.touch_renewed_at(connection, album_id=album.id)
    await savepoint.rollback()

    renewed_at = await fetch_val(
        connection, "select renewed_at from albums where id = :id", {"id": album.id}
    )
    available = await fetch_val(
        connection, "select available from photos where id = :id", {"id": photo.id}
    )
    assert available is False
    assert abs((renewed_at - original_renewed_at).total_seconds()) < 1
