from src.packages.photos import repository as photos_repository
from src.packages.ratings import repository as ratings_repository
from tests.authhelpers import log_in
from tests.factories import (
    create_album,
    create_membership,
    create_photo,
    create_rating,
    create_user,
)


async def test_the_unrated_filter_is_the_exact_set_the_sequence_returns(connection):
    """Task 1.2, D1: comparing the two results, not just their counts --
    the gallery's "unrated" filter and the rating sequence are the same
    query with the same filter, so they can never diverge.
    """
    user = await create_user(connection)
    album = await create_album(connection, owner_id=user.id)
    rated = await create_photo(connection, album_id=album.id, position=1)
    pending = await create_photo(connection, album_id=album.id, position=2)
    await create_rating(connection, photo_id=rated.id, user_id=user.id, approved=True)

    gallery_rows = await photos_repository.list_photos_with_rating(
        connection, album_id=album.id, user_id=user.id, rating_filter="unrated"
    )
    sequence_rows = await ratings_repository.list_pending_photos(
        connection, album_id=album.id, user_id=user.id
    )

    assert [row.id for row in gallery_rows] == [pending.id]
    assert [row.id for row in gallery_rows] == [row.id for row in sequence_rows]


async def test_unrated_and_rejected_are_distinguishable(connection):
    """Task 1.6: neither state is represented as the absence of the
    other."""
    user = await create_user(connection)
    album = await create_album(connection, owner_id=user.id)
    rejected = await create_photo(connection, album_id=album.id, position=1)
    unrated = await create_photo(connection, album_id=album.id, position=2)
    await create_rating(connection, photo_id=rejected.id, user_id=user.id, approved=False)

    rows = await photos_repository.list_photos_with_rating(
        connection, album_id=album.id, user_id=user.id, rating_filter="all"
    )

    by_id = {row.id: row.approved for row in rows}
    assert by_id[rejected.id] is False
    assert by_id[unrated.id] is None


async def test_the_gallery_always_returns_the_four_counts(client, connection):
    """Task 1.3, D2: whatever filter was requested, the response carries
    all four counts."""
    owner = await log_in(client, connection)
    album = await create_album(connection, owner_id=owner.id)
    approved = await create_photo(connection, album_id=album.id, position=1)
    await create_photo(connection, album_id=album.id, position=2)
    client.post(f"/api/albums/{album.id}/photos/{approved.id}/rating", json={"approved": True})

    response = client.get(f"/api/albums/{album.id}/photos/gallery", params={"filter": "rejected"})

    assert response.status_code == 200
    counts = response.json()["data"]["counts"]
    assert counts == {"total": 2, "approved": 1, "rejected": 0, "unrated": 1}


async def test_the_three_partial_filters_partition_the_total(client, connection):
    """Task 1.4: the sum of approved, rejected and unrated equals the
    total, and no photo appears in more than one partial filter."""
    owner = await log_in(client, connection)
    album = await create_album(connection, owner_id=owner.id)
    approved = await create_photo(connection, album_id=album.id, position=1)
    rejected = await create_photo(connection, album_id=album.id, position=2)
    await create_photo(connection, album_id=album.id, position=3)
    client.post(f"/api/albums/{album.id}/photos/{approved.id}/rating", json={"approved": True})
    client.post(f"/api/albums/{album.id}/photos/{rejected.id}/rating", json={"approved": False})

    counts = client.get(f"/api/albums/{album.id}/photos/gallery").json()["data"]["counts"]
    assert counts["approved"] + counts["rejected"] + counts["unrated"] == counts["total"]

    ids_by_filter = {}
    for name in ("approved", "rejected", "unrated"):
        response = client.get(f"/api/albums/{album.id}/photos/gallery", params={"filter": name})
        ids_by_filter[name] = {photo["id"] for photo in response.json()["data"]["photos"]}
    all_partial_ids = (
        ids_by_filter["approved"] | ids_by_filter["rejected"] | ids_by_filter["unrated"]
    )
    assert len(all_partial_ids) == sum(len(ids) for ids in ids_by_filter.values())
    all_ids = {
        photo["id"]
        for photo in client.get(f"/api/albums/{album.id}/photos/gallery").json()["data"]["photos"]
    }
    assert all_partial_ids == all_ids


async def test_a_non_member_gets_the_same_response_as_a_nonexistent_album(client, connection):
    stranger = await create_user(connection)
    foreign_album = await create_album(connection, owner_id=stranger.id)
    await log_in(client, connection)

    response = client.get(f"/api/albums/{foreign_album.id}/photos/gallery")

    assert response.status_code == 404


async def test_two_members_who_rated_differently_get_different_filters(client, connection):
    owner = await create_user(connection)
    album = await create_album(connection, owner_id=owner.id)
    photo = await create_photo(connection, album_id=album.id, position=1)
    await create_rating(connection, photo_id=photo.id, user_id=owner.id, approved=True)
    member = await log_in(client, connection)
    await create_membership(connection, album_id=album.id, user_id=member.id)

    response = client.get(f"/api/albums/{album.id}/photos/gallery", params={"filter": "approved"})

    # `member` never rated this photo, so their own "approved" filter is
    # empty even though the owner approved it (rating-gallery spec).
    assert response.json()["data"]["photos"] == []


async def test_gallery_photos_show_the_viewers_own_rating(client, connection):
    owner = await log_in(client, connection)
    album = await create_album(connection, owner_id=owner.id)
    approved = await create_photo(connection, album_id=album.id, position=1)
    rejected = await create_photo(connection, album_id=album.id, position=2)
    unrated = await create_photo(connection, album_id=album.id, position=3)
    client.post(f"/api/albums/{album.id}/photos/{approved.id}/rating", json={"approved": True})
    client.post(f"/api/albums/{album.id}/photos/{rejected.id}/rating", json={"approved": False})

    response = client.get(f"/api/albums/{album.id}/photos/gallery")

    by_id = {photo["id"]: photo["rating"] for photo in response.json()["data"]["photos"]}
    assert by_id[str(approved.id)] == "approved"
    assert by_id[str(rejected.id)] == "rejected"
    assert by_id[str(unrated.id)] is None


async def test_photos_appear_in_album_order_for_every_filter(client, connection):
    """Task 3.7 (backend side): no filter reorders by rating or by when
    it was cast."""
    owner = await log_in(client, connection)
    album = await create_album(connection, owner_id=owner.id)
    third = await create_photo(connection, album_id=album.id, position=3)
    first = await create_photo(connection, album_id=album.id, position=1)
    second = await create_photo(connection, album_id=album.id, position=2)
    client.post(f"/api/albums/{album.id}/photos/{third.id}/rating", json={"approved": True})

    response = client.get(f"/api/albums/{album.id}/photos/gallery")

    ids = [photo["id"] for photo in response.json()["data"]["photos"]]
    assert ids == [str(first.id), str(second.id), str(third.id)]


async def test_the_gallery_does_not_expose_aggregated_counts(client, connection):
    """Task 2.6: not even the owner sees cross-viewer counts here -- that
    is `album-stats`'s own, separate resource."""
    owner = await log_in(client, connection)
    album = await create_album(connection, owner_id=owner.id)
    photo = await create_photo(connection, album_id=album.id, position=1)
    client.post(f"/api/albums/{album.id}/photos/{photo.id}/rating", json={"approved": True})

    response = client.get(f"/api/albums/{album.id}/photos/gallery")

    entry = response.json()["data"]["photos"][0]
    assert set(entry.keys()) == {"id", "position", "width", "height", "thumbnailUrl", "rating"}


async def test_an_unknown_filter_is_rejected_rather_than_silently_defaulted(client, connection):
    """The backend endpoint itself validates strictly (D9): the leniency
    that turns an unrecognized filter into the default lives in the
    frontend route, not here."""
    owner = await log_in(client, connection)
    album = await create_album(connection, owner_id=owner.id)

    response = client.get(f"/api/albums/{album.id}/photos/gallery", params={"filter": "bogus"})

    assert response.status_code == 422
