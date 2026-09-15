from datetime import UTC, datetime, timedelta

from src.packages.quota import repository
from tests.factories import create_album, create_photo, create_user


async def test_the_total_counts_available_and_live_waits_but_not_expired_ones(connection):
    """The three situations a photo's row can be in (account-quota spec):
    confirmed, waiting with its grant still valid, and waiting with it
    already expired. Only the third contributes nothing -- it can never
    complete, so it holds no space.
    """
    owner = await create_user(connection)
    album = await create_album(connection, owner_id=owner.id)
    await create_photo(connection, album_id=album.id, declared_size=1_000, size=1_000)
    await create_photo(connection, album_id=album.id, available=False, declared_size=200)
    await create_photo(
        connection,
        album_id=album.id,
        available=False,
        declared_size=9_999,
        upload_expires_at=datetime.now(UTC) - timedelta(minutes=1),
    )

    assert await repository.account_used_bytes(connection, owner_id=owner.id) == 1_200


async def test_confirming_replaces_the_declared_size_with_the_real_one(connection):
    """What the declared size stands in for while a photo waits, and
    stops standing in for once the object itself has been measured."""
    owner = await create_user(connection)
    album = await create_album(connection, owner_id=owner.id)
    await create_photo(connection, album_id=album.id, declared_size=1_000, size=1_750)

    assert await repository.account_used_bytes(connection, owner_id=owner.id) == 1_750


async def test_an_album_of_someone_else_never_counts_against_this_account(connection):
    """The consumption of an album is its owner's (account-quota spec):
    being a member of one changes nothing about one's own usage."""
    owner = await create_user(connection)
    stranger = await create_user(connection)
    album = await create_album(connection, owner_id=owner.id)
    await create_photo(connection, album_id=album.id, declared_size=5_000)

    assert await repository.account_used_bytes(connection, owner_id=stranger.id) == 0


async def test_the_breakdown_adds_up_to_the_total_and_each_album_to_its_photos(connection):
    """The three levels are one number sliced twice, never three
    independently computed ones (account-quota spec): an album's total is
    the sum of its photos, and the account's is the sum of its albums.
    """
    owner = await create_user(connection)
    first = await create_album(connection, owner_id=owner.id, title="First")
    second = await create_album(connection, owner_id=owner.id, title="Second")
    empty = await create_album(connection, owner_id=owner.id, title="Empty")
    await create_photo(connection, album_id=first.id, declared_size=300, size=300)
    await create_photo(connection, album_id=first.id, declared_size=700, size=700)
    await create_photo(connection, album_id=second.id, available=False, declared_size=40)

    total = await repository.account_used_bytes(connection, owner_id=owner.id)
    by_album = await repository.account_usage_by_album(connection, owner_id=owner.id)

    assert sum(row.used_bytes for row in by_album) == total == 1_040
    # An album holding nothing is still a row: that is what makes the
    # breakdown add up to the total rather than to part of it.
    assert {row.album_id for row in by_album} == {first.id, second.id, empty.id}

    for album in (first, second, empty):
        photos = await repository.album_usage(connection, album_id=album.id)
        expected = next(row.used_bytes for row in by_album if row.album_id == album.id)
        assert sum(photo.size_bytes for photo in photos) == expected
