from src.packages.photos import repository as photos_repository
from tests.authhelpers import log_in
from tests.factories import create_album, create_membership, create_photo, create_user


async def test_the_instance_resource_answers_with_only_the_percentage(
    client, connection, monkeypatch
):
    monkeypatch.setattr("src.packages.quota.service.photos_settings.instance_max_bytes", 10_000)
    owner = await log_in(client, connection)
    album = await create_album(connection, owner_id=owner.id)
    await create_photo(connection, album_id=album.id, declared_size=1_500, size=1_500)

    response = client.get("/api/instance/usage")

    assert response.status_code == 200
    assert response.json()["data"] == {"usedPercent": 15}


async def test_the_instance_resource_never_reveals_the_raw_total_or_limit(
    client, connection, monkeypatch
):
    """The instance's real capacity never crosses the response -- only the
    percentage that follows from it."""
    monkeypatch.setattr("src.packages.quota.service.photos_settings.instance_max_bytes", 10_000)
    owner = await log_in(client, connection)
    album = await create_album(connection, owner_id=owner.id)
    await create_photo(connection, album_id=album.id, declared_size=1_500, size=1_500)

    response = client.get("/api/instance/usage")

    data = response.json()["data"]
    assert "usedBytes" not in data
    assert "limitBytes" not in data


async def test_the_instance_percentage_caps_at_100(client, connection, monkeypatch):
    monkeypatch.setattr("src.packages.quota.service.photos_settings.instance_max_bytes", 1_000)
    owner = await log_in(client, connection)
    album = await create_album(connection, owner_id=owner.id)
    await create_photo(connection, album_id=album.id, declared_size=5_000, size=5_000)

    response = client.get("/api/instance/usage")

    assert response.json()["data"]["usedPercent"] == 100


async def test_the_instance_resource_does_not_require_owning_anything(
    client, connection, monkeypatch
):
    """Any signed-in person, without needing an album of their own: the
    instance's space belongs to no one."""
    monkeypatch.setattr("src.packages.quota.service.photos_settings.instance_max_bytes", 8_000)
    stranger = await create_user(connection)
    foreign_album = await create_album(connection, owner_id=stranger.id)
    await create_photo(connection, album_id=foreign_album.id, declared_size=4_000, size=4_000)
    await log_in(client, connection)

    response = client.get("/api/instance/usage")

    assert response.status_code == 200
    # The stranger's photos still count towards the percentage: it
    # isn't scoped to the caller the way the account resource is.
    assert response.json()["data"]["usedPercent"] > 0


async def test_the_instance_resource_reveals_no_single_accounts_usage(client, connection):
    stranger = await create_user(connection)
    foreign_album = await create_album(connection, owner_id=stranger.id)
    await create_photo(connection, album_id=foreign_album.id, declared_size=4_000)
    await log_in(client, connection)

    response = client.get("/api/instance/usage")

    assert set(response.json()["data"].keys()) == {"usedPercent"}


async def test_the_instance_resource_requires_a_session(client):
    assert client.get("/api/instance/usage").status_code == 401


async def test_the_account_resource_answers_with_the_total_the_limit_and_the_breakdown(
    client, connection, monkeypatch
):
    monkeypatch.setattr("src.packages.quota.service.photos_settings.account_max_bytes", 10_000)
    owner = await log_in(client, connection)
    album = await create_album(connection, owner_id=owner.id)
    await create_photo(connection, album_id=album.id, declared_size=1_500, size=1_500)

    response = client.get("/api/account/usage")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["usedBytes"] == 1_500
    assert data["limitBytes"] == 10_000
    assert data["albums"] == [{"albumId": str(album.id), "usedBytes": 1_500}]


async def test_the_account_resource_only_ever_reports_the_signed_in_person(client, connection):
    """There is no identifier in this path: another person's albums are
    invisible to it no matter what, because nothing in the request names
    whose account to report on."""
    stranger = await create_user(connection)
    foreign_album = await create_album(connection, owner_id=stranger.id)
    await create_photo(connection, album_id=foreign_album.id, declared_size=4_000)
    viewer = await log_in(client, connection)
    # A member of the album, and still it counts against its owner alone.
    await create_membership(connection, album_id=foreign_album.id, user_id=viewer.id)

    response = client.get("/api/account/usage")

    assert response.status_code == 200
    assert response.json()["data"]["usedBytes"] == 0
    assert response.json()["data"]["albums"] == []


async def test_the_account_resource_requires_a_session(client):
    assert client.get("/api/account/usage").status_code == 401


async def test_the_owner_gets_an_albums_usage_with_each_photos_size(client, connection):
    owner = await log_in(client, connection)
    album = await create_album(connection, owner_id=owner.id)
    first = await create_photo(connection, album_id=album.id, position=1, declared_size=300)
    second = await create_photo(connection, album_id=album.id, position=2, declared_size=700)

    response = client.get(f"/api/albums/{album.id}/usage")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["usedBytes"] == 1_000
    assert data["photos"] == [
        {"photoId": str(first.id), "sizeBytes": 300},
        {"photoId": str(second.id), "sizeBytes": 700},
    ]


async def test_a_member_who_is_not_the_owner_cannot_read_an_albums_usage(client, connection):
    """What an album occupies is its owner's space: someone who reached it
    through a shared link already knows it exists, so this is a refusal and
    not a disappearance."""
    owner = await create_user(connection)
    album = await create_album(connection, owner_id=owner.id)
    await create_photo(connection, album_id=album.id, declared_size=300)
    member = await log_in(client, connection)
    await create_membership(connection, album_id=album.id, user_id=member.id)

    response = client.get(f"/api/albums/{album.id}/usage")

    assert response.status_code == 403


async def test_a_stranger_gets_the_same_answer_as_for_a_nonexistent_album(client, connection):
    owner = await create_user(connection)
    album = await create_album(connection, owner_id=owner.id)
    await log_in(client, connection)

    assert client.get(f"/api/albums/{album.id}/usage").status_code == 404


async def test_deleting_a_photo_is_reflected_the_next_time_usage_is_asked_for(client, connection):
    """What is consulted reflects the moment it was asked, because it is
    summed then and not kept as a running total.

    The row is removed through the repository on this test's own connection
    rather than through the endpoint: deleting a photo also deletes its
    object, so that flow opens a transaction of its own which cannot see
    anything this rollback-only connection wrote. What is being checked here
    is the reading, and the reading cannot tell how the row went away.
    """
    owner = await log_in(client, connection)
    album = await create_album(connection, owner_id=owner.id)
    photo = await create_photo(connection, album_id=album.id, declared_size=900)
    assert client.get("/api/account/usage").json()["data"]["usedBytes"] == 900

    await photos_repository.delete_owned_photo(
        connection, album_id=album.id, owner_id=owner.id, photo_id=photo.id
    )

    assert client.get("/api/account/usage").json()["data"]["usedBytes"] == 0
