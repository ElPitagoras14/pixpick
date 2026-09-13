import uuid

import pytest

from src.packages.albums import repository
from tests.authhelpers import log_in
from tests.factories import create_album, create_photo, create_session, create_user


async def test_creating_an_album_needs_only_a_title(client, connection):
    await log_in(client, connection)

    response = client.post("/api/albums", json={"title": "Vacation"})

    assert response.status_code == 200
    body = response.json()["data"]
    assert body["title"] == "Vacation"
    assert body["description"] is None


async def test_creating_an_album_without_a_title_is_rejected(client, connection):
    await log_in(client, connection)

    response = client.post("/api/albums", json={"description": "no title"})

    assert response.status_code == 422
    assert response.json()["error"]["field"] == "title"


async def test_a_blank_title_is_rejected_the_same_way(client, connection):
    await log_in(client, connection)

    response = client.post("/api/albums", json={"title": "   "})

    assert response.status_code == 422
    assert response.json()["error"]["field"] == "title"


async def test_listing_shows_only_the_callers_own_albums(client, connection):
    owner = await log_in(client, connection)
    stranger = await create_user(connection)
    await create_album(connection, owner_id=owner.id, title="Mine")
    await create_album(connection, owner_id=stranger.id, title="Theirs")

    response = client.get("/api/albums")

    assert response.status_code == 200
    titles = [album["title"] for album in response.json()["data"]]
    assert titles == ["Mine"]


async def test_the_owner_can_view_their_album(client, connection):
    owner = await log_in(client, connection)
    album = await create_album(connection, owner_id=owner.id, title="Mine")

    response = client.get(f"/api/albums/{album.id}")

    assert response.status_code == 200
    assert response.json()["data"]["title"] == "Mine"


async def test_a_foreign_album_responds_like_a_nonexistent_one(client, connection):
    stranger = await create_user(connection)
    foreign_album = await create_album(connection, owner_id=stranger.id)
    await log_in(client, connection)

    foreign_response = client.get(f"/api/albums/{foreign_album.id}")
    missing_response = client.get(f"/api/albums/{uuid.uuid4()}")

    assert foreign_response.status_code == missing_response.status_code == 404
    assert foreign_response.json() == missing_response.json()


async def test_renaming_updates_title_and_description(client, connection):
    owner = await log_in(client, connection)
    album = await create_album(connection, owner_id=owner.id, title="Old")

    response = client.patch(
        f"/api/albums/{album.id}", json={"title": "New", "description": "updated"}
    )

    assert response.status_code == 200
    assert response.json()["data"] == {
        "id": str(album.id),
        "title": "New",
        "description": "updated",
    }


async def test_renaming_a_foreign_album_does_not_modify_it(client, connection):
    stranger = await create_user(connection)
    foreign_album = await create_album(connection, owner_id=stranger.id, title="Untouched")
    await log_in(client, connection)

    response = client.patch(f"/api/albums/{foreign_album.id}", json={"title": "Hijacked"})

    assert response.status_code == 404
    unchanged = await repository.get_owned_album(
        connection, album_id=foreign_album.id, owner_id=stranger.id
    )
    assert unchanged.title == "Untouched"


async def test_deleting_an_album_removes_it_and_its_photos_objects(
    client, committed_connection, fake_storage
):
    """Delete opens its own transaction, separate from `client`'s (D6),
    so setup for this one test has to actually commit -- see
    `committed_connection` -- instead of relying on the rollback the
    other tests in this file share.
    """
    owner = await create_user(committed_connection)
    album = await create_album(committed_connection, owner_id=owner.id)
    photo = await create_photo(committed_connection, album_id=album.id, position=1)
    key = f"albums/{album.id}/{photo.id}"
    fake_storage.grant_upload(
        album_id=str(album.id),
        photo_id=str(photo.id),
        content_type="image/jpeg",
        max_size=10,
        ttl_seconds=60,
    )
    fake_storage.upload(target_key=key, size=10, content_type="image/jpeg")
    _, token = await create_session(committed_connection, user_id=owner.id)
    await committed_connection.commit()
    client.cookies.set("session", token)

    response = client.delete(f"/api/albums/{album.id}")

    assert response.status_code == 200
    assert await fake_storage.get_object(object_key=key) is None
    remaining = await repository.get_owned_album(
        committed_connection, album_id=album.id, owner_id=owner.id
    )
    assert remaining is None


async def test_a_failed_object_deletion_still_leaves_no_dangling_record(
    client, committed_connection, fake_storage, monkeypatch
):
    """D6: the rows are gone the moment the DB transaction commits, before
    storage is ever called -- so a failure to delete the object leaves an
    orphan in storage, never a row that points at nothing."""
    owner = await create_user(committed_connection)
    album = await create_album(committed_connection, owner_id=owner.id)
    await create_photo(committed_connection, album_id=album.id, position=1)
    _, token = await create_session(committed_connection, user_id=owner.id)
    await committed_connection.commit()
    client.cookies.set("session", token)

    async def _boom(*, object_keys):
        raise RuntimeError("storage is unreachable")

    monkeypatch.setattr(fake_storage, "delete_objects", _boom)

    with pytest.raises(RuntimeError):
        client.delete(f"/api/albums/{album.id}")

    remaining = await repository.get_owned_album(
        committed_connection, album_id=album.id, owner_id=owner.id
    )
    assert remaining is None


async def test_deleting_a_foreign_album_responds_like_a_nonexistent_one(
    client, committed_connection
):
    stranger = await create_user(committed_connection)
    foreign_album = await create_album(committed_connection, owner_id=stranger.id)
    caller = await create_user(committed_connection)
    _, token = await create_session(committed_connection, user_id=caller.id)
    await committed_connection.commit()
    client.cookies.set("session", token)

    response = client.delete(f"/api/albums/{foreign_album.id}")

    assert response.status_code == 404
    # Untouched: the rejected delete didn't remove it from under its
    # real owner.
    still_there = await repository.get_owned_album(
        committed_connection, album_id=foreign_album.id, owner_id=stranger.id
    )
    assert still_there is not None
