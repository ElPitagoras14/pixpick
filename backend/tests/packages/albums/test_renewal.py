"""album-retention spec: renewing the plazo is a consequence only of a
photo becoming available. Every other action a person can take on an
album or its photos SHALL NOT move it.
"""

from src.database.client import fetch_val
from src.packages.albums import service as albums_service
from src.packages.photos import repository as photos_repository
from src.packages.photos import service as photos_service
from src.packages.photos.schemas import GrantFileInput
from src.packages.ratings import service as ratings_service
from src.packages.shares import service as shares_service
from tests.factories import create_album, create_membership, create_photo, create_user


async def _renewed_at(connection, album_id):
    return await fetch_val(
        connection, "select renewed_at from albums where id = :id", {"id": album_id}
    )


async def test_rating_does_not_renew_the_plazo(connection):
    owner = await create_user(connection)
    rater = await create_user(connection)
    album = await create_album(connection, owner_id=owner.id)
    photo = await create_photo(connection, album_id=album.id)
    await create_membership(connection, album_id=album.id, user_id=rater.id)
    before = await _renewed_at(connection, album.id)

    await ratings_service.rate_photo(
        connection, album_id=album.id, photo_id=photo.id, user_id=rater.id, approved=True
    )

    assert await _renewed_at(connection, album.id) == before


async def test_sharing_and_revoking_do_not_renew_the_plazo(connection):
    owner = await create_user(connection)
    album = await create_album(connection, owner_id=owner.id)
    before = await _renewed_at(connection, album.id)

    await shares_service.get_or_create_link(connection, album_id=album.id)
    await shares_service.regenerate_link(connection, album_id=album.id)
    await shares_service.revoke_link(connection, album_id=album.id)

    assert await _renewed_at(connection, album.id) == before


async def test_renaming_does_not_renew_the_plazo(connection):
    owner = await create_user(connection)
    album = await create_album(connection, owner_id=owner.id, title="Old")
    before = await _renewed_at(connection, album.id)

    await albums_service.rename_album(
        connection, album_id=album.id, user_id=owner.id, title="New", description=None
    )

    assert await _renewed_at(connection, album.id) == before


async def test_deleting_photos_does_not_renew_the_plazo(connection):
    """Includes the last photo the album had, per the spec's own
    wording -- deleting down to none is still not a move of the plazo.
    """
    owner = await create_user(connection)
    album = await create_album(connection, owner_id=owner.id)
    first = await create_photo(connection, album_id=album.id, position=1)
    last = await create_photo(connection, album_id=album.id, position=2)
    before = await _renewed_at(connection, album.id)

    await photos_repository.delete_owned_photo(
        connection, album_id=album.id, owner_id=owner.id, photo_id=first.id
    )
    await photos_repository.delete_owned_photo(
        connection, album_id=album.id, owner_id=owner.id, photo_id=last.id
    )

    assert await _renewed_at(connection, album.id) == before


async def test_requesting_an_upload_grant_does_not_renew_the_plazo(connection):
    """Only the photo that *becomes available* renews it (D4) -- the
    permission requested to upload it, whether or not it's ever
    completed, never does.
    """
    owner = await create_user(connection)
    album = await create_album(connection, owner_id=owner.id)
    before = await _renewed_at(connection, album.id)

    await photos_service.grant_batch(
        connection,
        album_id=album.id,
        owner_id=owner.id,
        files=[GrantFileInput(content_type="image/jpeg", size=1_000, width=None, height=None)],
    )

    assert await _renewed_at(connection, album.id) == before
