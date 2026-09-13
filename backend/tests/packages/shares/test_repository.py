import uuid
from datetime import UTC, datetime

from src.packages.shares import repository
from tests.factories import create_album, create_share_token, create_user


async def test_get_live_token_is_none_when_the_album_has_none(connection):
    owner = await create_user(connection)
    album = await create_album(connection, owner_id=owner.id)

    assert await repository.get_live_token(connection, album_id=album.id) is None


async def test_get_live_token_finds_a_just_created_token(connection):
    owner = await create_user(connection)
    album = await create_album(connection, owner_id=owner.id)
    _, token = await create_share_token(connection, album_id=album.id)

    live = await repository.get_live_token(connection, album_id=album.id)

    assert live is not None
    assert live.token == token
    assert live.revoked_at is None


async def test_revoke_live_token_leaves_no_live_token(connection):
    owner = await create_user(connection)
    album = await create_album(connection, owner_id=owner.id)
    await create_share_token(connection, album_id=album.id)

    await repository.revoke_live_token(connection, album_id=album.id)

    assert await repository.get_live_token(connection, album_id=album.id) is None


async def test_revoke_live_token_is_a_no_op_when_already_revoked(connection):
    owner = await create_user(connection)
    album = await create_album(connection, owner_id=owner.id)
    await repository.revoke_live_token(connection, album_id=album.id)
    await repository.revoke_live_token(connection, album_id=album.id)

    assert await repository.get_live_token(connection, album_id=album.id) is None


async def test_get_live_album_id_by_token_resolves_a_live_token(connection):
    owner = await create_user(connection)
    album = await create_album(connection, owner_id=owner.id)
    _, token = await create_share_token(connection, album_id=album.id)

    assert await repository.get_live_album_id_by_token(connection, token=token) == album.id


async def test_get_live_album_id_by_token_is_none_for_a_revoked_token(connection):
    owner = await create_user(connection)
    album = await create_album(connection, owner_id=owner.id)
    _, token = await create_share_token(connection, album_id=album.id, revoked_at=datetime.now(UTC))

    assert await repository.get_live_album_id_by_token(connection, token=token) is None


async def test_get_live_album_id_by_token_is_none_for_an_unknown_token(connection):
    assert await repository.get_live_album_id_by_token(connection, token=str(uuid.uuid4())) is None
