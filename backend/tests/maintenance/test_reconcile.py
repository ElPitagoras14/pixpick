from datetime import UTC, datetime, timedelta

from src.maintenance import reconcile
from src.packages.albums.config import albums_settings
from src.packages.photos import repository
from tests.factories import create_album, create_photo, create_user


async def test_reconcile_discards_expired_pending_photos_and_their_objects(
    committed_connection, fake_storage
):
    user = await create_user(committed_connection)
    album = await create_album(committed_connection, owner_id=user.id)
    expired = await create_photo(
        committed_connection,
        album_id=album.id,
        position=1,
        available=False,
        upload_expires_at=datetime.now(UTC) - timedelta(minutes=1),
    )
    still_pending = await create_photo(
        committed_connection,
        album_id=album.id,
        position=2,
        available=False,
        upload_expires_at=datetime.now(UTC) + timedelta(minutes=5),
    )
    available = await create_photo(committed_connection, album_id=album.id, position=3)
    expired_key = f"albums/{album.id}/{expired.id}"
    fake_storage.grant_upload(
        album_id=str(album.id),
        photo_id=str(expired.id),
        content_type="image/jpeg",
        ttl_seconds=60,
    )
    fake_storage.upload(target_key=expired_key, size=10, content_type="image/jpeg")
    await committed_connection.commit()

    await reconcile.reconcile()

    remaining = await repository.get_owned_photos(
        committed_connection,
        album_id=album.id,
        owner_id=user.id,
        photo_ids=[expired.id, still_pending.id, available.id],
    )
    remaining_ids = {row.id for row in remaining}
    assert remaining_ids == {still_pending.id, available.id}
    assert await fake_storage.get_object(object_key=expired_key) is None


async def test_reconcile_discards_expired_albums_with_their_photos_and_objects(
    committed_connection, fake_storage, monkeypatch
):
    """D3 in album-retention's design: the command that already
    discarded abandoned uploads now also discards whole expired
    albums, rows first and committed, storage only after -- an album
    still within its plazo is left untouched.
    """
    monkeypatch.setattr(albums_settings, "album_retention_days", 30)
    user = await create_user(committed_connection)
    expired_album = await create_album(
        committed_connection, owner_id=user.id, renewed_at=datetime.now(UTC) - timedelta(days=31)
    )
    alive_album = await create_album(committed_connection, owner_id=user.id)
    expired_photo = await create_photo(committed_connection, album_id=expired_album.id, position=1)
    alive_photo = await create_photo(committed_connection, album_id=alive_album.id, position=1)
    expired_key = f"albums/{expired_album.id}/{expired_photo.id}"
    alive_key = f"albums/{alive_album.id}/{alive_photo.id}"
    for album_id, photo_id, key in (
        (expired_album.id, expired_photo.id, expired_key),
        (alive_album.id, alive_photo.id, alive_key),
    ):
        fake_storage.grant_upload(
            album_id=str(album_id),
            photo_id=str(photo_id),
            content_type="image/jpeg",
            ttl_seconds=60,
        )
        fake_storage.upload(target_key=key, size=10, content_type="image/jpeg")
    await committed_connection.commit()

    await reconcile.reconcile()

    assert (
        await repository.get_owned_photos(
            committed_connection,
            album_id=expired_album.id,
            owner_id=user.id,
            photo_ids=[expired_photo.id],
        )
        is None
    )
    assert await fake_storage.get_object(object_key=expired_key) is None

    remaining = await repository.get_owned_photos(
        committed_connection,
        album_id=alive_album.id,
        owner_id=user.id,
        photo_ids=[alive_photo.id],
    )
    assert [row.id for row in remaining] == [alive_photo.id]
    assert await fake_storage.get_object(object_key=alive_key) is not None


async def test_reconcile_does_nothing_when_there_is_nothing_expired(committed_connection):
    user = await create_user(committed_connection)
    album = await create_album(committed_connection, owner_id=user.id)
    photo = await create_photo(committed_connection, album_id=album.id, position=1)
    await committed_connection.commit()

    await reconcile.reconcile()

    remaining = await repository.get_owned_photos(
        committed_connection, album_id=album.id, owner_id=user.id, photo_ids=[photo.id]
    )
    assert [row.id for row in remaining] == [photo.id]


async def test_reconcile_stays_invocable_by_hand_and_a_second_run_in_a_row_does_not_fail(
    committed_connection, fake_storage
):
    """Task 5.3: the periodic service (compose.yaml, compose.dev.yaml)
    invokes the exact same command a person can still run by hand
    (src/maintenance/reconcile.py's own docstring) -- calling it twice
    back to back, the second time against whatever the first already
    cleaned up, SHALL NOT fail."""
    user = await create_user(committed_connection)
    album = await create_album(committed_connection, owner_id=user.id)
    expired = await create_photo(
        committed_connection,
        album_id=album.id,
        position=1,
        available=False,
        upload_expires_at=datetime.now(UTC) - timedelta(minutes=1),
    )
    expired_key = f"albums/{album.id}/{expired.id}"
    fake_storage.grant_upload(
        album_id=str(album.id),
        photo_id=str(expired.id),
        content_type="image/jpeg",
        ttl_seconds=60,
    )
    fake_storage.upload(target_key=expired_key, size=10, content_type="image/jpeg")
    await committed_connection.commit()

    await reconcile.reconcile()
    remaining = await repository.get_owned_photos(
        committed_connection, album_id=album.id, owner_id=user.id, photo_ids=[expired.id]
    )
    assert remaining == []

    # The second run finds an already-clean environment: no row left to
    # discard, no object left orphaned -- and, per the assertion below,
    # no exception either.
    await reconcile.reconcile()
