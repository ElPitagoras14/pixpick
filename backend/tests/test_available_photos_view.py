"""Every read of photos other than the upload flow's own writes goes through
`available_photos`, never `photos` directly. These tests are the guarantee
that querying the view needs no extra condition.
"""

from sqlalchemy import text

from tests.factories import create_album, create_photo, create_user


async def test_the_view_needs_no_extra_condition(connection):
    user = await create_user(connection)
    album = await create_album(connection, owner_id=user.id)
    available = await create_photo(connection, album_id=album.id, available=True)

    result = await connection.execute(
        text("select id from available_photos where album_id = :album_id"),
        {"album_id": album.id},
    )
    ids = {row[0] for row in result.all()}

    assert ids == {available.id}


async def test_an_unavailable_photo_does_not_appear_in_the_view(connection):
    user = await create_user(connection)
    album = await create_album(connection, owner_id=user.id)
    await create_photo(connection, album_id=album.id, available=False)

    result = await connection.execute(
        text("select id from available_photos where album_id = :album_id"),
        {"album_id": album.id},
    )

    assert result.all() == []
