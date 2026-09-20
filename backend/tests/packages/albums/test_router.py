import uuid
from datetime import UTC, datetime, timedelta

import pytest

from src.packages.albums import repository
from src.packages.albums.config import albums_settings
from tests.authhelpers import log_in
from tests.factories import (
    create_album,
    create_membership,
    create_photo,
    create_session,
    create_user,
)


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


async def test_a_title_longer_than_the_maximum_is_rejected_on_create(client, connection):
    await log_in(client, connection)

    response = client.post(
        "/api/albums", json={"title": "x" * (albums_settings.album_title_max_length + 1)}
    )

    assert response.status_code == 422
    assert response.json()["error"]["field"] == "title"


async def test_a_description_longer_than_the_maximum_is_rejected_on_create(client, connection):
    await log_in(client, connection)

    response = client.post(
        "/api/albums",
        json={
            "title": "Vacation",
            "description": "x" * (albums_settings.album_description_max_length + 1),
        },
    )

    assert response.status_code == 422
    assert response.json()["error"]["field"] == "description"


async def test_a_title_longer_than_the_maximum_is_rejected_on_rename(client, connection):
    owner = await log_in(client, connection)
    album = await create_album(connection, owner_id=owner.id)

    response = client.patch(
        f"/api/albums/{album.id}",
        json={"title": "x" * (albums_settings.album_title_max_length + 1)},
    )

    assert response.status_code == 422
    assert response.json()["error"]["field"] == "title"


async def test_listing_shows_the_callers_own_and_shared_albums(client, connection):
    owner = await log_in(client, connection)
    stranger = await create_user(connection)
    await create_album(connection, owner_id=owner.id, title="Mine")
    shared = await create_album(connection, owner_id=stranger.id, title="Shared with me")
    await create_album(connection, owner_id=stranger.id, title="Not mine at all")
    await create_membership(connection, album_id=shared.id, user_id=owner.id)

    response = client.get("/api/albums")

    assert response.status_code == 200
    by_title = {album["title"]: album for album in response.json()["data"]}
    assert set(by_title) == {"Mine", "Shared with me"}
    assert by_title["Mine"]["isOwner"] is True
    assert by_title["Shared with me"]["isOwner"] is False


async def test_the_owner_can_view_their_album(client, connection):
    owner = await log_in(client, connection)
    album = await create_album(connection, owner_id=owner.id, title="Mine")

    response = client.get(f"/api/albums/{album.id}")

    assert response.status_code == 200
    assert response.json()["data"]["title"] == "Mine"
    assert response.json()["data"]["isOwner"] is True


async def test_the_album_response_carries_the_instant_it_expires_not_rendered_text(
    client, connection, monkeypatch
):
    """5.1: the backend sends the expiry as a timestamp, both in the
    list and in the single album's own response, for the client to
    turn into text -- never text itself (album-retention spec, D6).
    """
    monkeypatch.setattr(albums_settings, "album_retention_days", 30)
    owner = await log_in(client, connection)
    renewed_at = datetime.now(UTC) - timedelta(days=5)
    album = await create_album(connection, owner_id=owner.id, renewed_at=renewed_at)
    expected = renewed_at + timedelta(days=30)

    detail = client.get(f"/api/albums/{album.id}").json()["data"]
    listing = client.get("/api/albums").json()["data"][0]

    for expires_at in (detail["expiresAt"], listing["expiresAt"]):
        parsed = datetime.fromisoformat(expires_at)
        assert abs((parsed - expected).total_seconds()) < 1


async def test_a_member_can_view_an_album_they_do_not_own(client, connection):
    owner = await create_user(connection)
    album = await create_album(connection, owner_id=owner.id, title="Shared")
    member = await log_in(client, connection)
    await create_membership(connection, album_id=album.id, user_id=member.id)

    response = client.get(f"/api/albums/{album.id}")

    assert response.status_code == 200
    assert response.json()["data"]["isOwner"] is False


async def test_a_foreign_album_responds_like_a_nonexistent_one(client, connection):
    stranger = await create_user(connection)
    foreign_album = await create_album(connection, owner_id=stranger.id)
    await log_in(client, connection)

    foreign_response = client.get(f"/api/albums/{foreign_album.id}")
    missing_response = client.get(f"/api/albums/{uuid.uuid4()}")

    assert foreign_response.status_code == missing_response.status_code == 404
    assert foreign_response.json() == missing_response.json()


async def test_a_member_who_is_not_the_owner_cannot_rename_the_album(client, connection):
    owner = await create_user(connection)
    album = await create_album(connection, owner_id=owner.id, title="Untouched")
    member = await log_in(client, connection)
    await create_membership(connection, album_id=album.id, user_id=member.id)

    response = client.patch(f"/api/albums/{album.id}", json={"title": "Hijacked"})

    assert response.status_code == 403
    unchanged = await repository.get_owned_album(connection, album_id=album.id, owner_id=owner.id)
    assert unchanged.title == "Untouched"


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


async def test_a_member_who_is_not_the_owner_cannot_delete_the_album(client, committed_connection):
    owner = await create_user(committed_connection)
    album = await create_album(committed_connection, owner_id=owner.id)
    member = await log_in(client, committed_connection)
    await create_membership(committed_connection, album_id=album.id, user_id=member.id)
    await committed_connection.commit()

    response = client.delete(f"/api/albums/{album.id}")

    assert response.status_code == 403
    remaining = await repository.get_owned_album(
        committed_connection, album_id=album.id, owner_id=owner.id
    )
    assert remaining is not None


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
