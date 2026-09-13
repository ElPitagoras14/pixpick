from datetime import UTC, datetime, timedelta

from src.packages.photos import reconcile, repository
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
