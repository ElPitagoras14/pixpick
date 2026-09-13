from datetime import UTC, datetime, timedelta

import httpx
import pytest

from src.exceptions import StateConflictError
from src.packages.photos import repository
from src.packages.photos import service as photos_service
from src.packages.photos.schemas import GrantFileInput
from src.packages.photos.warmup import warm_up_variants
from tests.authhelpers import log_in
from tests.factories import create_album, create_photo, create_session, create_user

_ONE_FILE = {"contentType": "image/jpeg", "size": 1000, "width": 100, "height": 100}


async def test_a_disallowed_content_type_rejects_the_whole_batch(client, connection, fake_storage):
    owner = await log_in(client, connection)
    album = await create_album(connection, owner_id=owner.id)

    response = client.post(
        f"/api/albums/{album.id}/photos/grants",
        json={"files": [_ONE_FILE, {**_ONE_FILE, "contentType": "application/pdf"}]},
    )

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["field"] == "files.1.contentType"
    assert fake_storage._grants == {}


async def test_an_oversized_file_rejects_the_whole_batch(client, connection, fake_storage):
    owner = await log_in(client, connection)
    album = await create_album(connection, owner_id=owner.id)

    response = client.post(
        f"/api/albums/{album.id}/photos/grants",
        json={"files": [{**_ONE_FILE, "size": 100 * 1024 * 1024}]},
    )

    assert response.status_code == 422
    assert response.json()["error"]["field"] == "files.0.size"


async def test_a_batch_over_fifty_is_rejected_before_granting_anything(client, connection):
    owner = await log_in(client, connection)
    album = await create_album(connection, owner_id=owner.id)

    response = client.post(
        f"/api/albums/{album.id}/photos/grants",
        json={"files": [_ONE_FILE] * 51},
    )

    assert response.status_code == 422


async def test_granting_assigns_sequential_positions_after_existing_photos(
    client, connection, fake_storage
):
    owner = await log_in(client, connection)
    album = await create_album(connection, owner_id=owner.id)
    await create_photo(connection, album_id=album.id, position=1)

    response = client.post(
        f"/api/albums/{album.id}/photos/grants",
        json={"files": [_ONE_FILE, _ONE_FILE]},
    )

    assert response.status_code == 200
    positions = [item["position"] for item in response.json()["data"]]
    assert positions == [2, 3]


async def test_a_lot_that_would_exceed_the_maximum_is_rejected_as_a_state_conflict(
    client, connection, fake_storage, monkeypatch
):
    monkeypatch.setattr("src.packages.photos.service.photos_settings.album_max_photos", 2)
    owner = await log_in(client, connection)
    album = await create_album(connection, owner_id=owner.id)
    await create_photo(connection, album_id=album.id, position=1)

    response = client.post(
        f"/api/albums/{album.id}/photos/grants",
        json={"files": [_ONE_FILE, _ONE_FILE]},
    )

    assert response.status_code == 409
    error = response.json()["error"]
    assert error["field"] is None
    assert error["details"] == {"remaining": 1}


async def test_pending_photos_with_a_live_grant_occupy_a_slot(
    client, connection, fake_storage, monkeypatch
):
    monkeypatch.setattr("src.packages.photos.service.photos_settings.album_max_photos", 1)
    owner = await log_in(client, connection)
    album = await create_album(connection, owner_id=owner.id)

    first = client.post(f"/api/albums/{album.id}/photos/grants", json={"files": [_ONE_FILE]})
    assert first.status_code == 200

    second = client.post(f"/api/albums/{album.id}/photos/grants", json={"files": [_ONE_FILE]})
    assert second.status_code == 409
    assert second.json()["error"]["details"]["remaining"] == 0


async def test_an_expired_pending_grant_no_longer_occupies_a_slot(
    client, connection, fake_storage, monkeypatch
):
    monkeypatch.setattr("src.packages.photos.service.photos_settings.album_max_photos", 1)
    owner = await log_in(client, connection)
    album = await create_album(connection, owner_id=owner.id)
    await create_photo(
        connection,
        album_id=album.id,
        position=1,
        available=False,
        upload_expires_at=datetime.now(UTC) - timedelta(minutes=1),
    )

    response = client.post(f"/api/albums/{album.id}/photos/grants", json={"files": [_ONE_FILE]})

    assert response.status_code == 200


async def test_reducing_the_maximum_does_not_touch_an_existing_album(
    client, connection, fake_storage, monkeypatch
):
    owner = await log_in(client, connection)
    album = await create_album(connection, owner_id=owner.id)
    await create_photo(connection, album_id=album.id, position=1)
    await create_photo(connection, album_id=album.id, position=2)
    monkeypatch.setattr("src.packages.photos.service.photos_settings.album_max_photos", 1)

    get_response = client.get(f"/api/albums/{album.id}/photos")
    assert get_response.status_code == 200
    assert len(get_response.json()["data"]) == 2

    grant_response = client.post(
        f"/api/albums/{album.id}/photos/grants", json={"files": [_ONE_FILE]}
    )
    assert grant_response.status_code == 409


async def test_freeing_space_re_enables_granting(committed_connection, fake_storage, monkeypatch):
    """Exercised at the service level, all through `committed_connection`:
    granting takes a row lock on the album (D12, D14) that a plain HTTP
    request only holds for the length of that one request, but `client`'s
    own request-scoped connection stays open for the whole test (it's
    what makes its rollback-based isolation possible) -- long enough to
    deadlock against `delete_photo`'s separate, real transaction below.
    """
    monkeypatch.setattr("src.packages.photos.service.photos_settings.album_max_photos", 1)
    owner = await create_user(committed_connection)
    album = await create_album(committed_connection, owner_id=owner.id)
    photo = await create_photo(committed_connection, album_id=album.id, position=1)
    await committed_connection.commit()

    with pytest.raises(StateConflictError):
        await photos_service.grant_batch(
            committed_connection,
            album_id=album.id,
            owner_id=owner.id,
            files=[GrantFileInput(content_type="image/jpeg", size=1000, width=100, height=100)],
        )
    await committed_connection.commit()

    await photos_service.delete_photo(album_id=album.id, owner_id=owner.id, photo_id=photo.id)

    grants = await photos_service.grant_batch(
        committed_connection,
        album_id=album.id,
        owner_id=owner.id,
        files=[GrantFileInput(content_type="image/jpeg", size=1000, width=100, height=100)],
    )
    assert len(grants) == 1


async def test_granting_for_a_foreign_album_responds_like_a_nonexistent_one(
    client, connection, fake_storage
):
    stranger = await create_user(connection)
    foreign_album = await create_album(connection, owner_id=stranger.id)
    await log_in(client, connection)

    response = client.post(
        f"/api/albums/{foreign_album.id}/photos/grants", json={"files": [_ONE_FILE]}
    )

    assert response.status_code == 404


async def test_listing_photos_only_shows_available_ones(client, connection):
    owner = await log_in(client, connection)
    album = await create_album(connection, owner_id=owner.id)
    available = await create_photo(connection, album_id=album.id, position=1)
    await create_photo(connection, album_id=album.id, position=2, available=False)

    response = client.get(f"/api/albums/{album.id}/photos")

    assert response.status_code == 200
    ids = [photo["id"] for photo in response.json()["data"]]
    assert ids == [str(available.id)]


# --- Confirm: its own transaction (D6), so setup here commits for real. ---


async def test_confirming_an_absent_object_leaves_the_photo_pending(
    client, committed_connection, fake_storage
):
    owner = await create_user(committed_connection)
    album = await create_album(committed_connection, owner_id=owner.id)
    photo = await create_photo(committed_connection, album_id=album.id, position=1, available=False)
    _, token = await create_session(committed_connection, user_id=owner.id)
    await committed_connection.commit()
    client.cookies.set("session", token)

    response = client.post(
        f"/api/albums/{album.id}/photos/confirm", json={"photoIds": [str(photo.id)]}
    )

    assert response.status_code == 200
    assert response.json()["data"] == [{"photoId": str(photo.id), "status": "pending"}]


async def test_confirming_a_mismatched_object_is_rejected_and_the_object_is_deleted(
    client, committed_connection, fake_storage
):
    owner = await create_user(committed_connection)
    album = await create_album(committed_connection, owner_id=owner.id)
    photo = await create_photo(
        committed_connection,
        album_id=album.id,
        position=1,
        available=False,
        declared_content_type="image/jpeg",
        declared_size=1000,
    )
    key = f"albums/{album.id}/{photo.id}"
    fake_storage.grant_upload(
        album_id=str(album.id),
        photo_id=str(photo.id),
        content_type="image/jpeg",
        max_size=10_000,
        ttl_seconds=60,
    )
    # A real size different from the 1000 declared -- a mismatch.
    fake_storage.upload(target_key=key, size=5, content_type="image/jpeg")
    _, token = await create_session(committed_connection, user_id=owner.id)
    await committed_connection.commit()
    client.cookies.set("session", token)

    response = client.post(
        f"/api/albums/{album.id}/photos/confirm", json={"photoIds": [str(photo.id)]}
    )

    assert response.status_code == 200
    assert response.json()["data"] == [{"photoId": str(photo.id), "status": "rejected"}]
    assert await fake_storage.get_object(object_key=key) is None
    grid = client.get(f"/api/albums/{album.id}/photos")
    assert grid.json()["data"] == []


async def test_confirming_a_matching_object_becomes_available_with_the_real_size(
    client, committed_connection, fake_storage
):
    owner = await create_user(committed_connection)
    album = await create_album(committed_connection, owner_id=owner.id)
    photo = await create_photo(
        committed_connection,
        album_id=album.id,
        position=1,
        available=False,
        declared_content_type="image/jpeg",
        declared_size=42,
    )
    key = f"albums/{album.id}/{photo.id}"
    fake_storage.grant_upload(
        album_id=str(album.id),
        photo_id=str(photo.id),
        content_type="image/jpeg",
        max_size=10_000,
        ttl_seconds=60,
    )
    fake_storage.upload(target_key=key, size=42, content_type="image/jpeg")
    _, token = await create_session(committed_connection, user_id=owner.id)
    await committed_connection.commit()
    client.cookies.set("session", token)

    response = client.post(
        f"/api/albums/{album.id}/photos/confirm", json={"photoIds": [str(photo.id)]}
    )

    assert response.status_code == 200
    assert response.json()["data"] == [{"photoId": str(photo.id), "status": "available"}]
    grid = client.get(f"/api/albums/{album.id}/photos")
    assert [p["id"] for p in grid.json()["data"]] == [str(photo.id)]


async def test_reconfirming_an_already_available_photo_is_inert(
    client, committed_connection, fake_storage
):
    owner = await create_user(committed_connection)
    album = await create_album(committed_connection, owner_id=owner.id)
    photo = await create_photo(committed_connection, album_id=album.id, position=1, available=True)
    _, token = await create_session(committed_connection, user_id=owner.id)
    await committed_connection.commit()
    client.cookies.set("session", token)

    response = client.post(
        f"/api/albums/{album.id}/photos/confirm", json={"photoIds": [str(photo.id)]}
    )

    assert response.status_code == 200
    assert response.json()["data"] == [{"photoId": str(photo.id), "status": "available"}]


async def test_confirming_for_a_foreign_album_responds_like_a_nonexistent_one(
    client, committed_connection
):
    stranger = await create_user(committed_connection)
    foreign_album = await create_album(committed_connection, owner_id=stranger.id)
    photo = await create_photo(committed_connection, album_id=foreign_album.id, position=1)
    caller = await create_user(committed_connection)
    _, token = await create_session(committed_connection, user_id=caller.id)
    await committed_connection.commit()
    client.cookies.set("session", token)

    response = client.post(
        f"/api/albums/{foreign_album.id}/photos/confirm", json={"photoIds": [str(photo.id)]}
    )

    assert response.status_code == 404


async def test_a_failed_warmup_is_only_logged(monkeypatch):
    """Task 4.4: a warm-up failure never propagates -- it's caught and
    logged, and nothing about a photo's own state depends on it."""

    async def _boom(self, url, timeout):
        raise httpx.ConnectError("simulated failure")

    monkeypatch.setattr(httpx.AsyncClient, "get", _boom)

    await warm_up_variants(["albums/some-album/some-photo"])  # must not raise


# --- Delete a photo: its own transaction too (D6). ---


async def test_deleting_a_photo_removes_it_and_its_object(
    client, committed_connection, fake_storage
):
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

    response = client.delete(f"/api/albums/{album.id}/photos/{photo.id}")

    assert response.status_code == 200
    assert await fake_storage.get_object(object_key=key) is None
    remaining = await repository.get_owned_photos(
        committed_connection, album_id=album.id, owner_id=owner.id, photo_ids=[photo.id]
    )
    assert remaining == []


async def test_a_failed_object_deletion_still_leaves_no_dangling_photo_record(
    client, committed_connection, fake_storage, monkeypatch
):
    """D6: the row is gone the moment its own transaction commits, before
    storage is ever called -- so a failure to delete the object leaves an
    orphan in storage, never a row that points at nothing."""
    owner = await create_user(committed_connection)
    album = await create_album(committed_connection, owner_id=owner.id)
    photo = await create_photo(committed_connection, album_id=album.id, position=1)
    _, token = await create_session(committed_connection, user_id=owner.id)
    await committed_connection.commit()
    client.cookies.set("session", token)

    async def _boom(*, object_keys):
        raise RuntimeError("storage is unreachable")

    monkeypatch.setattr(fake_storage, "delete_objects", _boom)

    with pytest.raises(RuntimeError):
        client.delete(f"/api/albums/{album.id}/photos/{photo.id}")

    remaining = await repository.get_owned_photos(
        committed_connection, album_id=album.id, owner_id=owner.id, photo_ids=[photo.id]
    )
    assert remaining == []


async def test_deleting_a_foreign_photo_responds_like_a_nonexistent_one(client, connection):
    stranger = await create_user(connection)
    foreign_album = await create_album(connection, owner_id=stranger.id)
    foreign_photo = await create_photo(connection, album_id=foreign_album.id, position=1)
    await log_in(client, connection)

    response = client.delete(f"/api/albums/{foreign_album.id}/photos/{foreign_photo.id}")

    assert response.status_code == 404
