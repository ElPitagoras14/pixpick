from src.packages.ratings import service
from tests.authhelpers import log_in
from tests.factories import (
    create_album,
    create_membership,
    create_photo,
    create_rating,
    create_user,
)


async def test_a_photo_nobody_rated_appears_at_zero(connection):
    """Starting from the album's photos, not from its ratings, is what keeps
    an unrated photo from being missing entirely."""
    owner = await create_user(connection)
    album = await create_album(connection, owner_id=owner.id)
    photo = await create_photo(connection, album_id=album.id, position=1)

    stats = await service.get_album_stats(connection, album_id=album.id)

    assert len(stats.photos) == 1
    assert stats.photos[0].photo_id == photo.id
    assert stats.photos[0].approved_count == 0
    assert stats.photos[0].rejected_count == 0


async def test_no_available_photo_is_missing(connection):
    owner = await create_user(connection)
    album = await create_album(connection, owner_id=owner.id)
    first = await create_photo(connection, album_id=album.id, position=1)
    second = await create_photo(connection, album_id=album.id, position=2)
    await create_rating(connection, photo_id=first.id, user_id=owner.id, approved=True)

    stats = await service.get_album_stats(connection, album_id=album.id)

    assert {photo.photo_id for photo in stats.photos} == {first.id, second.id}


async def test_the_summary_total_matches_the_sum_of_per_photo_counts(connection):
    owner = await create_user(connection)
    other = await create_user(connection)
    album = await create_album(connection, owner_id=owner.id)
    await create_membership(connection, album_id=album.id, user_id=other.id)
    first = await create_photo(connection, album_id=album.id, position=1)
    second = await create_photo(connection, album_id=album.id, position=2)
    await create_rating(connection, photo_id=first.id, user_id=owner.id, approved=True)
    await create_rating(connection, photo_id=first.id, user_id=other.id, approved=False)
    await create_rating(connection, photo_id=second.id, user_id=owner.id, approved=True)

    stats = await service.get_album_stats(connection, album_id=album.id)

    total_from_photos = sum(photo.approved_count + photo.rejected_count for photo in stats.photos)
    assert total_from_photos == stats.rating_count == 3
    assert stats.participant_count == 2


async def test_the_owner_can_access_the_stats(client, connection):
    owner = await log_in(client, connection)
    album = await create_album(connection, owner_id=owner.id)
    await create_photo(connection, album_id=album.id, position=1)

    response = client.get(f"/api/albums/{album.id}/stats")

    assert response.status_code == 200


async def test_a_member_who_is_not_the_owner_gets_forbidden(client, connection):
    owner = await create_user(connection)
    album = await create_album(connection, owner_id=owner.id)
    member = await log_in(client, connection)
    await create_membership(connection, album_id=album.id, user_id=member.id)

    response = client.get(f"/api/albums/{album.id}/stats")

    assert response.status_code == 403
    assert response.json()["data"] is None


async def test_a_stranger_gets_not_found(client, connection):
    owner = await create_user(connection)
    album = await create_album(connection, owner_id=owner.id)
    await log_in(client, connection)

    response = client.get(f"/api/albums/{album.id}/stats")

    assert response.status_code == 404


async def test_an_unavailable_photo_does_not_appear_in_the_stats(connection):
    owner = await create_user(connection)
    album = await create_album(connection, owner_id=owner.id)
    await create_photo(connection, album_id=album.id, position=1, available=False)

    stats = await service.get_album_stats(connection, album_id=album.id)

    assert stats.photos == []


async def test_the_response_carries_no_identity(client, connection):
    """Only counts, nothing that names or otherwise identifies who cast a
    rating."""
    owner = await log_in(client, connection)
    album = await create_album(connection, owner_id=owner.id)
    photo = await create_photo(connection, album_id=album.id, position=1)
    client.post(f"/api/albums/{album.id}/photos/{photo.id}/rating", json={"approved": True})

    response = client.get(f"/api/albums/{album.id}/stats")

    entry = response.json()["data"]["photos"][0]
    assert set(entry.keys()) == {"photoId", "approvedCount", "rejectedCount"}
    body = response.text
    assert str(owner.id) not in body
    assert "email" not in body.lower()


async def test_the_owners_own_ratings_count_like_anyone_elses(client, connection):
    owner = await log_in(client, connection)
    album = await create_album(connection, owner_id=owner.id)
    photo = await create_photo(connection, album_id=album.id, position=1)

    client.post(f"/api/albums/{album.id}/photos/{photo.id}/rating", json={"approved": True})
    response = client.get(f"/api/albums/{album.id}/stats")

    assert response.json()["data"]["photos"][0]["approvedCount"] == 1


async def test_a_new_rating_is_reflected_immediately(client, connection):
    """No value computed ahead of time."""
    owner = await log_in(client, connection)
    album = await create_album(connection, owner_id=owner.id)
    photo = await create_photo(connection, album_id=album.id, position=1)

    before = client.get(f"/api/albums/{album.id}/stats").json()["data"]["photos"][0]
    assert before == {"photoId": str(photo.id), "approvedCount": 0, "rejectedCount": 0}

    client.post(f"/api/albums/{album.id}/photos/{photo.id}/rating", json={"approved": True})
    after = client.get(f"/api/albums/{album.id}/stats").json()["data"]["photos"][0]
    assert after == {"photoId": str(photo.id), "approvedCount": 1, "rejectedCount": 0}


async def test_a_change_of_mind_is_reflected_immediately(client, connection):
    owner = await log_in(client, connection)
    album = await create_album(connection, owner_id=owner.id)
    photo = await create_photo(connection, album_id=album.id, position=1)
    client.post(f"/api/albums/{album.id}/photos/{photo.id}/rating", json={"approved": True})

    client.post(f"/api/albums/{album.id}/photos/{photo.id}/rating", json={"approved": False})
    stats = client.get(f"/api/albums/{album.id}/stats").json()["data"]["photos"][0]

    assert stats == {"photoId": str(photo.id), "approvedCount": 0, "rejectedCount": 1}
