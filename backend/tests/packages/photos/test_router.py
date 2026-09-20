import uuid as uuid_module
from datetime import UTC, datetime, timedelta

import httpx
import pytest

from src.exceptions import ValidationFailedError
from src.packages.albums import service as albums_service
from src.packages.albums.config import albums_settings
from src.packages.photos import repository
from src.packages.photos import service as photos_service
from src.packages.photos.schemas import GrantFileInput
from src.packages.photos.warmup import warm_up_variants
from src.packages.quota import repository as quota_repository
from src.packages.ratings import service as ratings_service
from src.packages.shares import service as shares_service
from tests.authhelpers import log_in
from tests.factories import (
    create_album,
    create_membership,
    create_photo,
    create_session,
    create_user,
)

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


@pytest.mark.parametrize("size", [-1, 0])
async def test_a_non_positive_size_is_rejected_naming_the_field(
    client, connection, fake_storage, size
):
    """Task 1.1: a negative or zero declared size doesn't describe any
    possible file and, subtracted from what's available, would grow it
    instead of consuming it (photo-upload spec, D5)."""
    owner = await log_in(client, connection)
    album = await create_album(connection, owner_id=owner.id)

    response = client.post(
        f"/api/albums/{album.id}/photos/grants",
        json={"files": [{**_ONE_FILE, "size": size}]},
    )

    assert response.status_code == 422
    assert response.json()["error"]["field"] == "files.0.size"
    assert fake_storage._grants == {}


@pytest.mark.parametrize("field", ["width", "height"])
async def test_an_excessive_dimension_is_rejected_naming_the_field(
    client, connection, fake_storage, field
):
    owner = await log_in(client, connection)
    album = await create_album(connection, owner_id=owner.id)

    response = client.post(
        f"/api/albums/{album.id}/photos/grants",
        json={"files": [{**_ONE_FILE, field: 999_999}]},
    )

    assert response.status_code == 422
    assert response.json()["error"]["field"] == f"files.0.{field}"


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
    data = response.json()["data"]
    assert [item["position"] for item in data["granted"]] == [2, 3]
    assert [item["index"] for item in data["granted"]] == [0, 1]
    assert data["denied"] == []


async def test_a_lot_that_would_exceed_the_maximum_is_granted_in_part(
    client, connection, fake_storage, monkeypatch
):
    """Replaces the rejection this case used to produce (photo-upload
    spec, modified by add-account-quota): running out of room in an album
    is a fact about the album's state, not a mistake in what was asked,
    so what fits is granted and the rest comes back explained.
    """
    monkeypatch.setattr("src.packages.photos.service.photos_settings.album_max_photos", 2)
    owner = await log_in(client, connection)
    album = await create_album(connection, owner_id=owner.id)
    await create_photo(connection, album_id=album.id, position=1)

    response = client.post(
        f"/api/albums/{album.id}/photos/grants",
        json={"files": [_ONE_FILE, _ONE_FILE]},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert [item["index"] for item in data["granted"]] == [0]
    assert data["denied"] == [
        {"index": 1, "reason": "album_full", "remainingPhotos": 0, "remainingBytes": None}
    ]


async def test_pending_photos_with_a_live_grant_occupy_a_slot(
    client, connection, fake_storage, monkeypatch
):
    monkeypatch.setattr("src.packages.photos.service.photos_settings.album_max_photos", 1)
    owner = await log_in(client, connection)
    album = await create_album(connection, owner_id=owner.id)

    first = client.post(f"/api/albums/{album.id}/photos/grants", json={"files": [_ONE_FILE]})
    assert first.status_code == 200
    assert len(first.json()["data"]["granted"]) == 1

    second = client.post(f"/api/albums/{album.id}/photos/grants", json={"files": [_ONE_FILE]})
    assert second.status_code == 200
    assert second.json()["data"]["granted"] == []
    assert second.json()["data"]["denied"][0]["reason"] == "album_full"


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
    assert grant_response.status_code == 200
    assert grant_response.json()["data"]["granted"] == []
    assert grant_response.json()["data"]["denied"][0]["reason"] == "album_full"


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

    files = [GrantFileInput(content_type="image/jpeg", size=1000, width=100, height=100)]
    full = await photos_service.grant_batch(
        committed_connection, album_id=album.id, owner_id=owner.id, files=files
    )
    assert full.granted == []
    assert full.denied[0].reason == "album_full"
    await committed_connection.commit()

    await photos_service.delete_photo(album_id=album.id, user_id=owner.id, photo_id=photo.id)

    result = await photos_service.grant_batch(
        committed_connection, album_id=album.id, owner_id=owner.id, files=files
    )
    assert len(result.granted) == 1
    assert result.denied == []


async def test_a_non_positive_size_in_the_service_rejects_the_batch_without_touching_quotas(
    committed_connection, fake_storage
):
    """Task 1.2: `_validate_files` is the defense that still holds for a
    caller that builds `GrantFileInput` directly, bypassing the router's
    own schema constraint (task 1.1) -- the batch is rejected whole, the
    file responsible is named, and neither the account's nor the
    instance's consumption moves (photo-upload spec)."""
    owner = await create_user(committed_connection)
    album = await create_album(committed_connection, owner_id=owner.id)
    await committed_connection.commit()

    before_account = await quota_repository.account_used_bytes(
        committed_connection, owner_id=owner.id
    )
    before_instance = await quota_repository.instance_used_bytes(committed_connection)

    files = [
        GrantFileInput(content_type="image/jpeg", size=1_000, width=None, height=None),
        GrantFileInput(content_type="image/jpeg", size=-1, width=None, height=None),
    ]
    with pytest.raises(ValidationFailedError) as excinfo:
        await photos_service.grant_batch(
            committed_connection, album_id=album.id, owner_id=owner.id, files=files
        )
    assert excinfo.value.field == "files.1.size"

    after_account = await quota_repository.account_used_bytes(
        committed_connection, owner_id=owner.id
    )
    after_instance = await quota_repository.instance_used_bytes(committed_connection)
    assert after_account == before_account
    assert after_instance == before_instance


async def test_confirming_more_than_the_batch_ceiling_is_rejected_without_querying_storage(
    client, committed_connection, fake_storage, monkeypatch
):
    """Task 1.4: the same ceiling as granting (photo-upload spec, ADDED
    requirement) -- a lot above it fails as a validation error before any
    photo is looked up in storage."""
    owner = await create_user(committed_connection)
    album = await create_album(committed_connection, owner_id=owner.id)
    _, token = await create_session(committed_connection, user_id=owner.id)
    await committed_connection.commit()
    client.cookies.set("session", token)

    async def _boom(*, object_key):
        raise AssertionError("storage SHALL NOT be consulted for a rejected batch")

    monkeypatch.setattr(fake_storage, "get_object", _boom)

    photo_ids = [str(uuid_module.uuid4()) for _ in range(51)]
    response = client.post(f"/api/albums/{album.id}/photos/confirm", json={"photoIds": photo_ids})

    assert response.status_code == 422


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


async def test_granting_for_an_expired_album_responds_like_a_nonexistent_one(
    client, connection, fake_storage, monkeypatch
):
    """album-retention spec: asking for upload permissions on an album
    whose plazo already ran out answers exactly like a nonexistent
    album, the same as the foreign-album case above.
    """
    monkeypatch.setattr(albums_settings, "album_retention_days", 30)
    owner = await log_in(client, connection)
    expired = await create_album(
        connection, owner_id=owner.id, renewed_at=datetime.now(UTC) - timedelta(days=31)
    )

    response = client.post(f"/api/albums/{expired.id}/photos/grants", json={"files": [_ONE_FILE]})

    assert response.status_code == 404
    assert fake_storage._grants == {}


async def test_listing_photos_only_shows_available_ones(client, connection):
    owner = await log_in(client, connection)
    album = await create_album(connection, owner_id=owner.id)
    available = await create_photo(connection, album_id=album.id, position=1)
    await create_photo(connection, album_id=album.id, position=2, available=False)

    response = client.get(f"/api/albums/{album.id}/photos")

    assert response.status_code == 200
    ids = [photo["id"] for photo in response.json()["data"]]
    assert ids == [str(available.id)]


async def test_a_member_can_view_the_grid_without_owning_the_album(client, connection):
    owner = await create_user(connection)
    album = await create_album(connection, owner_id=owner.id)
    photo = await create_photo(connection, album_id=album.id, position=1)
    member = await log_in(client, connection)
    await create_membership(connection, album_id=album.id, user_id=member.id)

    response = client.get(f"/api/albums/{album.id}/photos")

    assert response.status_code == 200
    assert [p["id"] for p in response.json()["data"]] == [str(photo.id)]


async def test_a_member_who_is_not_the_owner_cannot_grant_upload_slots(client, connection):
    owner = await create_user(connection)
    album = await create_album(connection, owner_id=owner.id)
    member = await log_in(client, connection)
    await create_membership(connection, album_id=album.id, user_id=member.id)

    response = client.post(f"/api/albums/{album.id}/photos/grants", json={"files": [_ONE_FILE]})

    assert response.status_code == 403


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


async def test_a_member_who_is_not_the_owner_cannot_confirm_photos(
    client, committed_connection, fake_storage
):
    owner = await create_user(committed_connection)
    album = await create_album(committed_connection, owner_id=owner.id)
    photo = await create_photo(committed_connection, album_id=album.id, position=1, available=False)
    member = await log_in(client, committed_connection)
    await create_membership(committed_connection, album_id=album.id, user_id=member.id)
    await committed_connection.commit()

    response = client.post(
        f"/api/albums/{album.id}/photos/confirm", json={"photoIds": [str(photo.id)]}
    )

    assert response.status_code == 403


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


async def test_a_member_who_is_not_the_owner_cannot_delete_a_photo(client, committed_connection):
    owner = await create_user(committed_connection)
    album = await create_album(committed_connection, owner_id=owner.id)
    photo = await create_photo(committed_connection, album_id=album.id, position=1)
    member = await log_in(client, committed_connection)
    await create_membership(committed_connection, album_id=album.id, user_id=member.id)
    await committed_connection.commit()

    response = client.delete(f"/api/albums/{album.id}/photos/{photo.id}")

    assert response.status_code == 403


async def test_a_file_that_does_not_fit_is_skipped_and_a_smaller_one_behind_it_still_fits(
    client, connection, fake_storage, monkeypatch
):
    """D5: the walk skips what doesn't fit instead of stopping at it, so
    one large file at the front of a selection can't discard the smaller
    ones behind it for no reason other than the order they were picked.
    """
    monkeypatch.setattr("src.packages.photos.service.photos_settings.account_max_bytes", 1_500)
    owner = await log_in(client, connection)
    album = await create_album(connection, owner_id=owner.id)

    response = client.post(
        f"/api/albums/{album.id}/photos/grants",
        json={
            "files": [
                {**_ONE_FILE, "size": 1_400},
                {**_ONE_FILE, "size": 1_200},
                {**_ONE_FILE, "size": 100},
            ]
        },
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert [item["index"] for item in data["granted"]] == [0, 2]
    assert [item["index"] for item in data["denied"]] == [1]
    assert data["denied"][0]["reason"] == "account_full"
    assert data["denied"][0]["remainingBytes"] == 100


async def test_asking_for_more_than_fits_answers_every_file_exactly_once(
    client, connection, fake_storage, monkeypatch
):
    """D4: the two lists together account for the whole request, and the
    index on each entry is what lets the client say which file each one
    is -- the request carries no filename to match them by."""
    monkeypatch.setattr("src.packages.photos.service.photos_settings.account_max_bytes", 2_500)
    owner = await log_in(client, connection)
    album = await create_album(connection, owner_id=owner.id)

    response = client.post(f"/api/albums/{album.id}/photos/grants", json={"files": [_ONE_FILE] * 4})

    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data["granted"]) == 2
    assert len(data["denied"]) == 2
    indexes = [item["index"] for item in data["granted"] + data["denied"]]
    assert sorted(indexes) == [0, 1, 2, 3]


async def test_an_account_without_space_denies_with_its_own_reason(
    client, connection, fake_storage, monkeypatch
):
    monkeypatch.setattr("src.packages.photos.service.photos_settings.account_max_bytes", 500)
    owner = await log_in(client, connection)
    album = await create_album(connection, owner_id=owner.id)

    response = client.post(f"/api/albums/{album.id}/photos/grants", json={"files": [_ONE_FILE]})

    assert response.status_code == 200
    assert response.json()["data"]["denied"] == [
        {"index": 0, "reason": "account_full", "remainingPhotos": None, "remainingBytes": 500}
    ]


async def test_an_album_with_room_still_denies_when_the_account_is_full_elsewhere(
    client, connection, fake_storage, monkeypatch
):
    """The account's space is measured over every album its owner has
    (photo-upload spec), so an empty album is no help once the account
    itself is full -- and the reason says so, since creating yet another
    album would not fix it."""
    monkeypatch.setattr("src.packages.photos.service.photos_settings.account_max_bytes", 1_000)
    owner = await log_in(client, connection)
    crowded = await create_album(connection, owner_id=owner.id, title="Crowded")
    await create_photo(connection, album_id=crowded.id, declared_size=1_000, size=1_000)
    empty = await create_album(connection, owner_id=owner.id, title="Empty")

    response = client.post(f"/api/albums/{empty.id}/photos/grants", json={"files": [_ONE_FILE]})

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["granted"] == []
    assert data["denied"][0]["reason"] == "account_full"
    assert data["denied"][0]["remainingBytes"] == 0


async def test_a_file_that_does_not_fit_the_instance_is_skipped_and_a_smaller_one_fits(
    client, connection, fake_storage, monkeypatch
):
    """D4 in add-instance-quota: the instance is the third check, after
    the account's, and a smaller file further down the batch can still
    fit in what the instance has left even after a bigger one didn't."""
    monkeypatch.setattr("src.packages.photos.service.photos_settings.instance_max_bytes", 1_500)
    owner = await log_in(client, connection)
    album = await create_album(connection, owner_id=owner.id)

    response = client.post(
        f"/api/albums/{album.id}/photos/grants",
        json={"files": [{**_ONE_FILE, "size": 1_400}, {**_ONE_FILE, "size": 100}]},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert [item["index"] for item in data["granted"]] == [0, 1]
    assert data["denied"] == []

    second = client.post(
        f"/api/albums/{album.id}/photos/grants",
        json={"files": [{**_ONE_FILE, "size": 100}]},
    )
    assert second.status_code == 200
    assert second.json()["data"]["granted"] == []
    assert second.json()["data"]["denied"][0]["reason"] == "instance_full"


async def test_the_instance_full_denies_even_with_room_in_the_account(
    client, connection, fake_storage, monkeypatch
):
    monkeypatch.setattr("src.packages.photos.service.photos_settings.instance_max_bytes", 500)
    owner = await log_in(client, connection)
    album = await create_album(connection, owner_id=owner.id)

    response = client.post(f"/api/albums/{album.id}/photos/grants", json={"files": [_ONE_FILE]})

    assert response.status_code == 200
    assert response.json()["data"]["denied"] == [
        {"index": 0, "reason": "instance_full", "remainingPhotos": None, "remainingBytes": 500}
    ]


async def test_the_account_full_wins_over_the_instance_full(
    client, connection, fake_storage, monkeypatch
):
    """When both are full at once the account's reason is the one that
    comes back (photo-upload spec, modified by add-instance-quota): it's
    the only one whoever is asking can act on."""
    monkeypatch.setattr("src.packages.photos.service.photos_settings.account_max_bytes", 500)
    monkeypatch.setattr("src.packages.photos.service.photos_settings.instance_max_bytes", 500)
    owner = await log_in(client, connection)
    album = await create_album(connection, owner_id=owner.id)

    response = client.post(f"/api/albums/{album.id}/photos/grants", json={"files": [_ONE_FILE]})

    assert response.status_code == 200
    assert response.json()["data"]["denied"][0]["reason"] == "account_full"


async def test_an_album_of_someone_else_never_eats_into_this_persons_space(
    client, connection, fake_storage, monkeypatch
):
    """A photo rated in an album someone shared counts against its
    owner's limit, never the viewer's (account-quota spec)."""
    monkeypatch.setattr("src.packages.photos.service.photos_settings.account_max_bytes", 1_000)
    stranger = await create_user(connection)
    foreign = await create_album(connection, owner_id=stranger.id)
    await create_photo(connection, album_id=foreign.id, declared_size=1_000, size=1_000)
    owner = await log_in(client, connection)
    await create_membership(connection, album_id=foreign.id, user_id=owner.id)
    own = await create_album(connection, owner_id=owner.id)

    response = client.post(f"/api/albums/{own.id}/photos/grants", json={"files": [_ONE_FILE]})

    assert response.status_code == 200
    assert len(response.json()["data"]["granted"]) == 1


# --- Final verification (add-instance-quota, tasks 5.1-5.3) ---


async def test_full_cycle_across_two_accounts_instance_full_then_freed(
    committed_connection, fake_storage, monkeypatch
):
    """Task 5.1: fills the instance from one account, checks that a
    second, unrelated one is denied with a reason that never points it
    at its own photos, frees space from the first, and checks the second
    can upload again -- the space freed anywhere is what re-enables
    everyone (instance-quota spec)."""
    monkeypatch.setattr("src.packages.photos.service.photos_settings.instance_max_bytes", 1_000)
    first_owner = await create_user(committed_connection)
    second_owner = await create_user(committed_connection)
    first_album = await create_album(committed_connection, owner_id=first_owner.id)
    second_album = await create_album(committed_connection, owner_id=second_owner.id)
    await committed_connection.commit()

    files = [GrantFileInput(content_type="image/jpeg", size=1_000, width=None, height=None)]

    first_result = await photos_service.grant_batch(
        committed_connection, album_id=first_album.id, owner_id=first_owner.id, files=files
    )
    await committed_connection.commit()
    assert len(first_result.granted) == 1

    second_result = await photos_service.grant_batch(
        committed_connection, album_id=second_album.id, owner_id=second_owner.id, files=files
    )
    await committed_connection.commit()
    assert second_result.granted == []
    # Not the account reason: the second account's own space has nothing
    # to do with why this was denied.
    assert second_result.denied[0].reason == "instance_full"

    await photos_service.delete_photo(
        album_id=first_album.id,
        user_id=first_owner.id,
        photo_id=first_result.granted[0].photo_id,
    )

    retried = await photos_service.grant_batch(
        committed_connection, album_id=second_album.id, owner_id=second_owner.id, files=files
    )
    await committed_connection.commit()
    assert len(retried.granted) == 1
    assert retried.denied == []


async def test_the_instance_being_full_does_not_block_anything_else(
    committed_connection, fake_storage, monkeypatch
):
    """Task 5.2: with the instance already over its limit, every other
    flow -- creating an account, viewing, rating, sharing and deleting --
    keeps working exactly as it does with room to spare (instance-quota
    spec).

    Exercised at the service level, the same way
    `test_freeing_space_re_enables_granting` above is: `delete_photo`
    opens its own, separately committed transaction (D6 in
    add-albums-and-upload), and mixing that with the HTTP `client` --
    whose own connection never commits until the whole test tears down --
    deadlocks the two fixtures' teardown against each other the moment
    anything the client wrote is still locked when `delete_photo` needs
    the same row.
    """
    monkeypatch.setattr("src.packages.photos.service.photos_settings.instance_max_bytes", 10)
    owner = await create_user(committed_connection)
    album = await albums_service.create_album(
        committed_connection, owner_id=owner.id, title="Full", description=None
    )
    rated_photo = await create_photo(
        committed_connection, album_id=album.id, position=1, declared_size=500, size=500
    )
    deleted_photo = await create_photo(
        committed_connection, album_id=album.id, position=2, declared_size=500, size=500
    )
    await committed_connection.commit()

    assert await albums_service.list_albums(committed_connection, user_id=owner.id)
    gallery = await photos_service.get_gallery(
        committed_connection, album_id=album.id, user_id=owner.id, rating_filter="all"
    )
    assert len(gallery.photos) == 2

    rating = await ratings_service.rate_photo(
        committed_connection,
        album_id=album.id,
        photo_id=rated_photo.id,
        user_id=owner.id,
        approved=True,
    )
    assert rating.approved is True

    link = await shares_service.get_or_create_link(committed_connection, album_id=album.id)
    assert link
    await committed_connection.commit()

    await photos_service.delete_photo(
        album_id=album.id, user_id=owner.id, photo_id=deleted_photo.id
    )

    # A brand-new account is created and uses the product with the
    # instance still full: only incorporating new photos is ever
    # conditioned on the instance's own space.
    other_owner = await create_user(committed_connection)
    other_album = await albums_service.create_album(
        committed_connection, owner_id=other_owner.id, title="Fresh", description=None
    )
    await committed_connection.commit()
    assert other_album.owner_id == other_owner.id


async def test_reducing_the_account_limit_below_usage_keeps_photos_and_only_blocks_adding(
    client, connection, fake_storage, monkeypatch
):
    """Task 5.3, account scope: the same guarantee `account-quota` already
    established for this exact case -- lowering the limit below what an
    account already occupies removes nothing and only blocks adding."""
    owner = await log_in(client, connection)
    album = await create_album(connection, owner_id=owner.id)
    await create_photo(
        connection, album_id=album.id, position=1, declared_size=200_000_000, size=200_000_000
    )
    monkeypatch.setattr("src.packages.photos.service.photos_settings.account_max_bytes", 500)

    listing = client.get(f"/api/albums/{album.id}/photos")
    assert listing.status_code == 200
    assert len(listing.json()["data"]) == 1

    grant_response = client.post(
        f"/api/albums/{album.id}/photos/grants", json={"files": [_ONE_FILE]}
    )
    assert grant_response.status_code == 200
    assert grant_response.json()["data"]["granted"] == []
    assert grant_response.json()["data"]["denied"][0]["reason"] == "account_full"


async def test_reducing_the_instance_limit_below_usage_keeps_photos_and_only_blocks_adding(
    client, connection, fake_storage, monkeypatch
):
    """Task 5.3, instance scope: the same guarantee, one level up -- an
    instance already over a lowered limit conserves every account's
    photos and only rejects incorporating more."""
    owner = await log_in(client, connection)
    album = await create_album(connection, owner_id=owner.id)
    await create_photo(connection, album_id=album.id, position=1, declared_size=2_000, size=2_000)
    monkeypatch.setattr("src.packages.photos.service.photos_settings.instance_max_bytes", 500)

    listing = client.get(f"/api/albums/{album.id}/photos")
    assert listing.status_code == 200
    assert len(listing.json()["data"]) == 1

    grant_response = client.post(
        f"/api/albums/{album.id}/photos/grants", json={"files": [_ONE_FILE]}
    )
    assert grant_response.status_code == 200
    assert grant_response.json()["data"]["granted"] == []
    assert grant_response.json()["data"]["denied"][0]["reason"] == "instance_full"
