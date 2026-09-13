import uuid

from sqlalchemy import event

from src.packages.albums import repository
from tests.factories import create_album, create_membership, create_photo, create_user


async def test_insert_album_assigns_the_creator_as_owner(connection):
    user = await create_user(connection)

    album = await repository.insert_album(
        connection, owner_id=user.id, title="Vacation", description=None
    )

    assert album.owner_id == user.id
    assert album.title == "Vacation"
    assert album.description is None


async def test_get_owned_album_is_none_for_a_foreign_album(connection):
    owner = await create_user(connection)
    stranger = await create_user(connection)
    album = await create_album(connection, owner_id=owner.id)

    assert (
        await repository.get_owned_album(connection, album_id=album.id, owner_id=owner.id)
        is not None
    )
    assert (
        await repository.get_owned_album(connection, album_id=album.id, owner_id=stranger.id)
        is None
    )


async def test_get_owned_album_is_none_for_a_nonexistent_album(connection):
    user = await create_user(connection)

    assert (
        await repository.get_owned_album(connection, album_id=uuid.uuid4(), owner_id=user.id)
        is None
    )


async def test_list_member_albums_resolves_count_cover_and_pending_in_one_query(connection):
    user = await create_user(connection)
    await create_album(connection, owner_id=user.id, title="Empty")
    populated_album = await create_album(connection, owner_id=user.id, title="Populated")
    first_photo = await create_photo(connection, album_id=populated_album.id, position=1)
    await create_photo(connection, album_id=populated_album.id, position=2)
    await create_photo(connection, album_id=populated_album.id, position=3, available=False)

    query_count = 0

    def _count_queries(*args, **kwargs):
        nonlocal query_count
        query_count += 1

    event.listen(connection.sync_engine, "before_cursor_execute", _count_queries)
    try:
        rows = await repository.list_member_albums(connection, user_id=user.id)
    finally:
        event.remove(connection.sync_engine, "before_cursor_execute", _count_queries)

    assert query_count == 1

    by_title = {row.title: row for row in rows}
    assert by_title["Empty"].photo_count == 0
    assert by_title["Empty"].cover_photo_id is None
    assert by_title["Empty"].is_owner is True
    # Nothing rated yet: both available photos of "Populated" are pending.
    assert by_title["Populated"].pending_count == 2
    # Only the two available photos count; the unavailable one is
    # invisible to the count and never the cover (D1, photo-upload spec).
    assert by_title["Populated"].photo_count == 2
    assert by_title["Populated"].cover_photo_id == first_photo.id


async def test_list_member_albums_only_returns_albums_the_caller_is_a_member_of(connection):
    owner = await create_user(connection)
    stranger = await create_user(connection)
    await create_album(connection, owner_id=owner.id, title="Mine")
    await create_album(connection, owner_id=stranger.id, title="Theirs")

    rows = await repository.list_member_albums(connection, user_id=owner.id)

    assert [row.title for row in rows] == ["Mine"]


async def test_list_member_albums_includes_shared_albums_distinguished_from_owned(connection):
    owner = await create_user(connection)
    member = await create_user(connection)
    album = await create_album(connection, owner_id=owner.id, title="Shared")
    await create_membership(connection, album_id=album.id, user_id=member.id)

    owner_rows = await repository.list_member_albums(connection, user_id=owner.id)
    member_rows = await repository.list_member_albums(connection, user_id=member.id)

    assert owner_rows[0].is_owner is True
    assert member_rows[0].is_owner is False


async def test_get_accessible_album_is_none_for_someone_with_no_relation_to_it(connection):
    owner = await create_user(connection)
    stranger = await create_user(connection)
    album = await create_album(connection, owner_id=owner.id)

    assert (
        await repository.get_accessible_album(connection, album_id=album.id, user_id=owner.id)
        is not None
    )
    assert (
        await repository.get_accessible_album(connection, album_id=album.id, user_id=stranger.id)
        is None
    )


async def test_get_accessible_album_sees_a_member_who_is_not_the_owner(connection):
    owner = await create_user(connection)
    member = await create_user(connection)
    album = await create_album(connection, owner_id=owner.id)
    await create_membership(connection, album_id=album.id, user_id=member.id)

    accessible = await repository.get_accessible_album(
        connection, album_id=album.id, user_id=member.id
    )

    assert accessible is not None
    assert accessible.owner_id == owner.id


async def test_add_member_is_idempotent(connection):
    owner = await create_user(connection)
    member = await create_user(connection)
    album = await create_album(connection, owner_id=owner.id)

    await repository.add_member(connection, album_id=album.id, user_id=member.id)
    await repository.add_member(connection, album_id=album.id, user_id=member.id)

    rows = await repository.list_member_albums(connection, user_id=member.id)
    assert len(rows) == 1


async def test_is_member(connection):
    owner = await create_user(connection)
    stranger = await create_user(connection)
    album = await create_album(connection, owner_id=owner.id)

    assert await repository.is_member(connection, album_id=album.id, user_id=owner.id) is True
    assert await repository.is_member(connection, album_id=album.id, user_id=stranger.id) is False


async def test_rename_owned_album_updates_only_title_and_description(connection):
    user = await create_user(connection)
    album = await create_album(connection, owner_id=user.id, title="Old", description="Old desc")
    photo = await create_photo(connection, album_id=album.id, position=1)

    updated = await repository.rename_owned_album(
        connection, album_id=album.id, owner_id=user.id, title="New", description="New desc"
    )

    assert updated is not None
    assert updated.title == "New"
    assert updated.description == "New desc"

    rows = await repository.list_member_albums(connection, user_id=user.id)
    assert rows[0].cover_photo_id == photo.id


async def test_rename_owned_album_is_none_for_a_foreign_album(connection):
    owner = await create_user(connection)
    stranger = await create_user(connection)
    album = await create_album(connection, owner_id=owner.id, title="Mine")

    result = await repository.rename_owned_album(
        connection, album_id=album.id, owner_id=stranger.id, title="Hijacked", description=None
    )

    assert result is None


async def test_lock_owned_album_id_returns_none_for_a_foreign_album(connection):
    owner = await create_user(connection)
    stranger = await create_user(connection)
    album = await create_album(connection, owner_id=owner.id)

    assert (
        await repository.lock_owned_album_id(connection, album_id=album.id, owner_id=owner.id)
        == album.id
    )
    assert (
        await repository.lock_owned_album_id(connection, album_id=album.id, owner_id=stranger.id)
        is None
    )


async def test_delete_owned_album_returning_photo_ids(connection):
    user = await create_user(connection)
    album = await create_album(connection, owner_id=user.id)
    photo = await create_photo(connection, album_id=album.id, position=1)

    photo_ids = await repository.delete_owned_album_returning_photo_ids(
        connection, album_id=album.id, owner_id=user.id
    )

    assert photo_ids == [photo.id]
    assert await repository.get_owned_album(connection, album_id=album.id, owner_id=user.id) is None


async def test_delete_owned_album_returning_photo_ids_is_none_for_a_foreign_album(connection):
    owner = await create_user(connection)
    stranger = await create_user(connection)
    album = await create_album(connection, owner_id=owner.id)

    result = await repository.delete_owned_album_returning_photo_ids(
        connection, album_id=album.id, owner_id=stranger.id
    )

    assert result is None
    # Untouched: the rejected delete didn't modify it.
    assert (
        await repository.get_owned_album(connection, album_id=album.id, owner_id=owner.id)
        is not None
    )
