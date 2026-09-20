from src.packages.ratings import service
from tests.factories import create_album, create_photo, create_rating, create_user


async def test_count_pending_matches_the_length_of_the_sequence(connection):
    """The counter is `len()` of the very same rows the sequence returns --
    not a second query that could say something different about the same
    person and album.
    """
    user = await create_user(connection)
    album = await create_album(connection, owner_id=user.id)
    await create_photo(connection, album_id=album.id, position=1)
    rated = await create_photo(connection, album_id=album.id, position=2)
    await create_photo(connection, album_id=album.id, position=3)
    await create_rating(connection, photo_id=rated.id, user_id=user.id, approved=True)

    pending = await service.list_pending(connection, album_id=album.id, user_id=user.id)
    count = await service.count_pending(connection, album_id=album.id, user_id=user.id)

    assert count == len(pending) == 2
