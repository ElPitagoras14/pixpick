import uuid

from src.packages.ratings import repository as ratings_repository
from tests.authhelpers import log_in
from tests.factories import create_album, create_photo, create_user


async def test_a_member_can_rate_a_photo(client, connection):
    owner = await log_in(client, connection)
    album = await create_album(connection, owner_id=owner.id)
    photo = await create_photo(connection, album_id=album.id, position=1)

    response = client.post(
        f"/api/albums/{album.id}/photos/{photo.id}/rating", json={"approved": True}
    )

    assert response.status_code == 200
    assert response.json()["data"] == {"photoId": str(photo.id), "approved": True}


async def test_a_non_member_gets_the_same_response_as_a_nonexistent_photo(client, connection):
    owner = await create_user(connection)
    album = await create_album(connection, owner_id=owner.id)
    photo = await create_photo(connection, album_id=album.id, position=1)
    await log_in(client, connection)

    response = client.post(
        f"/api/albums/{album.id}/photos/{photo.id}/rating", json={"approved": True}
    )
    missing_response = client.post(
        f"/api/albums/{album.id}/photos/{uuid.uuid4()}/rating", json={"approved": True}
    )

    # Neither the album nor the photo is visible to a non-member: the album
    # dependency alone already answers 404 here, the same shape a stranger
    # to the album always sees.
    assert response.status_code == missing_response.status_code == 404
    assert response.json() == missing_response.json()


async def test_a_non_member_cannot_register_a_rating(client, connection):
    owner = await create_user(connection)
    album = await create_album(connection, owner_id=owner.id)
    photo = await create_photo(connection, album_id=album.id, position=1)
    await log_in(client, connection)

    client.post(f"/api/albums/{album.id}/photos/{photo.id}/rating", json={"approved": True})

    pending_for_owner = await ratings_repository.list_pending_photos(
        connection, album_id=album.id, user_id=owner.id
    )
    assert [row.id for row in pending_for_owner] == [photo.id]


async def test_repeating_the_same_rating_leaves_the_same_result(client, connection):
    owner = await log_in(client, connection)
    album = await create_album(connection, owner_id=owner.id)
    photo = await create_photo(connection, album_id=album.id, position=1)

    client.post(f"/api/albums/{album.id}/photos/{photo.id}/rating", json={"approved": True})
    response = client.post(
        f"/api/albums/{album.id}/photos/{photo.id}/rating", json={"approved": True}
    )

    assert response.json()["data"]["approved"] is True


async def test_changing_the_rating_replaces_it(client, connection):
    owner = await log_in(client, connection)
    album = await create_album(connection, owner_id=owner.id)
    photo = await create_photo(connection, album_id=album.id, position=1)

    client.post(f"/api/albums/{album.id}/photos/{photo.id}/rating", json={"approved": True})
    response = client.post(
        f"/api/albums/{album.id}/photos/{photo.id}/rating", json={"approved": False}
    )

    assert response.json()["data"]["approved"] is False


async def test_the_sequence_lists_only_pending_photos_in_album_order(client, connection):
    owner = await log_in(client, connection)
    album = await create_album(connection, owner_id=owner.id)
    first = await create_photo(connection, album_id=album.id, position=1)
    second = await create_photo(connection, album_id=album.id, position=2)
    client.post(f"/api/albums/{album.id}/photos/{first.id}/rating", json={"approved": True})

    response = client.get(f"/api/albums/{album.id}/pending")

    assert response.status_code == 200
    ids = [row["id"] for row in response.json()["data"]]
    assert ids == [str(second.id)]


async def test_the_sequence_brings_every_pending_photo_unpaginated(client, connection, monkeypatch):
    """The sequence is bounded only by the album's own maximum, and never
    paginates -- a full album's response still brings every one of its
    pending photos in a single reply.
    """
    monkeypatch.setattr("src.packages.photos.service.photos_settings.album_max_photos", 8)
    owner = await log_in(client, connection)
    album = await create_album(connection, owner_id=owner.id)
    photos = [await create_photo(connection, album_id=album.id, position=i) for i in range(1, 9)]

    response = client.get(f"/api/albums/{album.id}/pending")

    ids = [row["id"] for row in response.json()["data"]]
    assert ids == [str(photo.id) for photo in photos]


async def test_deleting_a_photo_reduces_what_is_pending(client, committed_connection, fake_storage):
    """Deleting a photo opens its own transaction, separate from `client`'s
    -- see `photos.service.delete_photo` -- so setup here has to actually
    commit, like `tests/packages/photos/test_router.py`'s own delete tests
    already do.
    """
    owner = await log_in(client, committed_connection)
    album = await create_album(committed_connection, owner_id=owner.id)
    first = await create_photo(committed_connection, album_id=album.id, position=1)
    second = await create_photo(committed_connection, album_id=album.id, position=2)
    await committed_connection.commit()

    delete_response = client.delete(f"/api/albums/{album.id}/photos/{first.id}")
    assert delete_response.status_code == 200

    response = client.get(f"/api/albums/{album.id}/pending")
    ids = [row["id"] for row in response.json()["data"]]
    assert ids == [str(second.id)]


async def test_resuming_after_an_interruption_continues_where_it_left_off(client, connection):
    owner = await log_in(client, connection)
    album = await create_album(connection, owner_id=owner.id)
    first = await create_photo(connection, album_id=album.id, position=1)
    second = await create_photo(connection, album_id=album.id, position=2)
    third = await create_photo(connection, album_id=album.id, position=3)

    client.post(f"/api/albums/{album.id}/photos/{first.id}/rating", json={"approved": True})
    # "Leaving and coming back later" is just asking for the sequence again
    # -- there is no session state to resume.
    response = client.get(f"/api/albums/{album.id}/pending")

    ids = [row["id"] for row in response.json()["data"]]
    assert ids == [str(second.id), str(third.id)]


async def test_finishing_leaves_the_sequence_empty(client, connection):
    owner = await log_in(client, connection)
    album = await create_album(connection, owner_id=owner.id)
    photo = await create_photo(connection, album_id=album.id, position=1)

    client.post(f"/api/albums/{album.id}/photos/{photo.id}/rating", json={"approved": True})
    response = client.get(f"/api/albums/{album.id}/pending")

    assert response.json()["data"] == []


async def test_uploading_more_photos_increases_what_a_finished_member_still_owes(
    client, connection
):
    owner = await log_in(client, connection)
    album = await create_album(connection, owner_id=owner.id)
    photo = await create_photo(connection, album_id=album.id, position=1)
    client.post(f"/api/albums/{album.id}/photos/{photo.id}/rating", json={"approved": True})
    assert client.get(f"/api/albums/{album.id}/pending").json()["data"] == []

    new_photo = await create_photo(connection, album_id=album.id, position=2)

    response = client.get(f"/api/albums/{album.id}/pending")
    ids = [row["id"] for row in response.json()["data"]]
    assert ids == [str(new_photo.id)]


async def test_a_not_yet_available_photo_never_appears_as_pending(client, connection):
    owner = await log_in(client, connection)
    album = await create_album(connection, owner_id=owner.id)
    await create_photo(connection, album_id=album.id, position=1, available=False)

    response = client.get(f"/api/albums/{album.id}/pending")

    assert response.json()["data"] == []
