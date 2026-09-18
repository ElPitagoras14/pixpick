"""album-retention spec: an album whose plazo has run out behaves as if
it never existed, for every read the repository offers.
"""

from datetime import UTC, datetime, timedelta

from src.database.client import fetch_val, write
from src.packages.albums import repository
from src.packages.albums.config import albums_settings
from src.packages.photos import repository as photos_repository
from src.packages.photos import service as photos_service
from src.packages.photos.schemas import GrantFileInput
from src.packages.quota import repository as quota_repository
from src.packages.shares import repository as shares_repository
from tests.factories import create_album, create_photo, create_share_token, create_user


async def test_get_owned_album_is_none_for_an_expired_album(connection, monkeypatch):
    monkeypatch.setattr(albums_settings, "album_retention_days", 30)
    user = await create_user(connection)
    expired = await create_album(
        connection, owner_id=user.id, renewed_at=datetime.now(UTC) - timedelta(days=31)
    )

    assert (
        await repository.get_owned_album(connection, album_id=expired.id, owner_id=user.id) is None
    )


async def test_get_owned_album_sees_an_album_still_within_its_plazo(connection, monkeypatch):
    monkeypatch.setattr(albums_settings, "album_retention_days", 30)
    user = await create_user(connection)
    fresh = await create_album(
        connection, owner_id=user.id, renewed_at=datetime.now(UTC) - timedelta(days=29)
    )

    assert (
        await repository.get_owned_album(connection, album_id=fresh.id, owner_id=user.id)
        is not None
    )


async def test_list_member_albums_excludes_an_expired_album(connection, monkeypatch):
    monkeypatch.setattr(albums_settings, "album_retention_days", 30)
    user = await create_user(connection)
    await create_album(
        connection,
        owner_id=user.id,
        title="Expired",
        renewed_at=datetime.now(UTC) - timedelta(days=31),
    )
    await create_album(connection, owner_id=user.id, title="Alive")

    rows = await repository.list_member_albums(connection, user_id=user.id)

    assert [row.title for row in rows] == ["Alive"]


async def test_get_accessible_album_is_none_for_an_expired_album(connection, monkeypatch):
    monkeypatch.setattr(albums_settings, "album_retention_days", 30)
    user = await create_user(connection)
    expired = await create_album(
        connection, owner_id=user.id, renewed_at=datetime.now(UTC) - timedelta(days=31)
    )

    assert (
        await repository.get_accessible_album(connection, album_id=expired.id, user_id=user.id)
        is None
    )


async def test_album_exists_is_false_for_an_expired_album(connection, monkeypatch):
    monkeypatch.setattr(albums_settings, "album_retention_days", 30)
    user = await create_user(connection)
    expired = await create_album(
        connection, owner_id=user.id, renewed_at=datetime.now(UTC) - timedelta(days=31)
    )

    assert await repository.album_exists(connection, album_id=expired.id) is False


async def test_album_exists_is_true_for_a_fresh_album(connection):
    user = await create_user(connection)
    album = await create_album(connection, owner_id=user.id)

    assert await repository.album_exists(connection, album_id=album.id) is True


async def test_touch_renewed_at_restarts_the_plazo(connection, monkeypatch):
    monkeypatch.setattr(albums_settings, "album_retention_days", 30)
    user = await create_user(connection)
    album = await create_album(
        connection, owner_id=user.id, renewed_at=datetime.now(UTC) - timedelta(days=31)
    )
    assert await repository.album_exists(connection, album_id=album.id) is False

    await repository.touch_renewed_at(connection, album_id=album.id)

    assert await repository.album_exists(connection, album_id=album.id) is True


async def test_delete_owned_album_returning_photo_ids_is_none_for_an_expired_album(
    connection, monkeypatch
):
    monkeypatch.setattr(albums_settings, "album_retention_days", 30)
    user = await create_user(connection)
    expired = await create_album(
        connection, owner_id=user.id, renewed_at=datetime.now(UTC) - timedelta(days=31)
    )

    result = await repository.delete_owned_album_returning_photo_ids(
        connection, album_id=expired.id, owner_id=user.id
    )

    assert result is None


async def test_a_new_album_without_photos_counts_its_plazo_from_its_creation(connection):
    """3.3: with no photo ever confirmed, `renewed_at` never moves away
    from what `insert_album` -- the production path, not the factory's
    override -- gave it at creation.
    """
    user = await create_user(connection)

    album = await repository.insert_album(
        connection, owner_id=user.id, title="New", description=None
    )

    renewed_at = await fetch_val(
        connection, "select renewed_at from albums where id = :id", {"id": album.id}
    )
    assert abs((renewed_at - album.created_at).total_seconds()) < 1


async def test_the_first_available_photo_moves_the_plazo(connection):
    """3.3: an old `renewed_at` -- as if the album had sat with no
    photo for a while -- is moved forward the moment its first photo
    becomes available, the same transaction `photos.service.confirm_batch`
    itself uses (D4).
    """
    user = await create_user(connection)
    old_renewed_at = datetime.now(UTC) - timedelta(days=10)
    album = await create_album(connection, owner_id=user.id, renewed_at=old_renewed_at)
    photo = await create_photo(connection, album_id=album.id, available=False)

    await photos_repository.mark_photo_available(connection, photo_id=photo.id, size=123)
    await repository.touch_renewed_at(connection, album_id=album.id)

    renewed_at = await fetch_val(
        connection, "select renewed_at from albums where id = :id", {"id": album.id}
    )
    assert renewed_at > old_renewed_at


async def test_the_delay_before_the_cleanup_command_runs_has_no_observable_effect(
    connection, monkeypatch
):
    """4.3: an expired album, with the maintenance command never run,
    behaves exactly as if it were already gone -- nobody sees it, its
    share link doesn't resolve, and it no longer counts against its
    owner's quota. Only the objects in storage are left waiting, and
    this test never touches storage at all.
    """
    monkeypatch.setattr(albums_settings, "album_retention_days", 30)
    owner = await create_user(connection)
    expired = await create_album(
        connection, owner_id=owner.id, renewed_at=datetime.now(UTC) - timedelta(days=31)
    )
    await create_photo(connection, album_id=expired.id, declared_size=5_000, size=5_000)
    _, token = await create_share_token(connection, album_id=expired.id)

    # Nobody sees it.
    assert (
        await repository.get_owned_album(connection, album_id=expired.id, owner_id=owner.id) is None
    )
    assert (
        await repository.get_accessible_album(connection, album_id=expired.id, user_id=owner.id)
        is None
    )
    assert [
        row.id for row in await repository.list_member_albums(connection, user_id=owner.id)
    ] == []

    # Its link doesn't resolve: the token is still live, but the album
    # it names has expired.
    assert await shares_repository.get_live_album_id_by_token(connection, token=token) == expired.id
    assert await repository.album_exists(connection, album_id=expired.id) is False

    # Its space no longer counts.
    assert await quota_repository.account_used_bytes(connection, owner_id=owner.id) == 0


async def test_an_expired_album_frees_space_for_a_new_upload_before_any_cleanup(
    connection, monkeypatch
):
    """6.2: an account sitting at its limit can grant again the moment
    the album occupying that space expires -- no cleanup command has
    to run first, since the account's usage is a read of `albums` like
    any other and inherits the same condition (D5).
    """
    monkeypatch.setattr(albums_settings, "album_retention_days", 30)
    monkeypatch.setattr("src.packages.photos.service.photos_settings.account_max_bytes", 1_000)
    owner = await create_user(connection)
    full_album = await create_album(connection, owner_id=owner.id)
    await create_photo(connection, album_id=full_album.id, declared_size=1_000, size=1_000)
    other_album = await create_album(connection, owner_id=owner.id)
    files = [GrantFileInput(content_type="image/jpeg", size=500, width=None, height=None)]

    # At the limit: a fresh album's own upload is denied.
    while_alive = await photos_service.grant_batch(
        connection, album_id=other_album.id, owner_id=owner.id, files=files
    )
    assert while_alive.granted == []
    assert while_alive.denied[0].reason == "account_full"

    # The album expires -- nothing else changes, no cleanup runs.
    await write(
        connection,
        "update albums set renewed_at = :renewed_at where id = :id",
        {"renewed_at": datetime.now(UTC) - timedelta(days=31), "id": full_album.id},
    )

    after_expiry = await photos_service.grant_batch(
        connection, album_id=other_album.id, owner_id=owner.id, files=files
    )
    assert after_expiry.denied == []
    assert len(after_expiry.granted) == 1


async def test_lowering_the_plazo_expires_every_older_album_at_once(connection, monkeypatch):
    """6.3: the plazo is read fresh on every query, never baked into a
    row when it's created (D1) -- lowering it in the configuration
    expires every album already older than the new value, all at
    once, with no migration and no code change needed. `monkeypatch`
    is what returns the value to its original one once this test
    ends, the same effect the task asks to verify.
    """
    owner = await create_user(connection)
    ages_in_days = [10, 20, 40]
    albums = [
        await create_album(
            connection, owner_id=owner.id, renewed_at=datetime.now(UTC) - timedelta(days=age)
        )
        for age in ages_in_days
    ]

    monkeypatch.setattr(albums_settings, "album_retention_days", 30)
    alive = {
        album.id for album in albums if await repository.album_exists(connection, album_id=album.id)
    }
    assert alive == {albums[0].id, albums[1].id}

    monkeypatch.setattr(albums_settings, "album_retention_days", 5)
    for album in albums:
        assert await repository.album_exists(connection, album_id=album.id) is False
