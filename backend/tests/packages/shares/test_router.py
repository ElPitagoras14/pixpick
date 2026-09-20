import uuid
from datetime import UTC, datetime, timedelta

from src.config import settings
from src.packages.albums import repository as albums_repository
from src.packages.albums.config import albums_settings
from src.packages.shares import repository as shares_repository
from tests.authhelpers import log_in
from tests.factories import create_album, create_membership, create_share_token, create_user


async def test_the_owner_gets_a_share_link_for_their_album(client, connection):
    owner = await log_in(client, connection)
    album = await create_album(connection, owner_id=owner.id)

    response = client.get(f"/api/albums/{album.id}/share")

    assert response.status_code == 200
    url = response.json()["data"]["url"]
    # Built from the configured public address, never from the request's own
    # scheme or host -- the test client talks to "testserver", which never
    # appears here.
    assert url.startswith(f"{settings.public_url.rstrip('/')}/a/")
    assert "testserver" not in url


async def test_getting_the_link_twice_returns_the_same_one(client, connection):
    owner = await log_in(client, connection)
    album = await create_album(connection, owner_id=owner.id)

    first = client.get(f"/api/albums/{album.id}/share").json()["data"]["url"]
    second = client.get(f"/api/albums/{album.id}/share").json()["data"]["url"]

    assert first == second


async def test_a_member_who_is_not_the_owner_cannot_administer_the_link(client, connection):
    owner = await create_user(connection)
    album = await create_album(connection, owner_id=owner.id)
    _, original_token = await create_share_token(connection, album_id=album.id)
    member = await log_in(client, connection)
    await create_membership(connection, album_id=album.id, user_id=member.id)

    regenerate_response = client.post(f"/api/albums/{album.id}/share/regenerate")
    revoke_response = client.post(f"/api/albums/{album.id}/share/revoke")

    assert regenerate_response.status_code == 403
    assert revoke_response.status_code == 403
    live = await shares_repository.get_live_token(connection, album_id=album.id)
    assert live is not None
    assert live.token == original_token


async def test_a_stranger_gets_the_same_response_as_a_nonexistent_album(client, connection):
    stranger_owner = await create_user(connection)
    album = await create_album(connection, owner_id=stranger_owner.id)
    await log_in(client, connection)

    foreign_response = client.get(f"/api/albums/{album.id}/share")
    missing_response = client.get(f"/api/albums/{uuid.uuid4()}/share")

    assert foreign_response.status_code == missing_response.status_code == 404
    assert foreign_response.json() == missing_response.json()


async def test_regenerating_invalidates_the_previous_link_and_never_repeats_a_token(
    client, connection
):
    owner = await log_in(client, connection)
    album = await create_album(connection, owner_id=owner.id)
    old_url = client.get(f"/api/albums/{album.id}/share").json()["data"]["url"]
    old_token = old_url.rsplit("/", 1)[-1]

    new_url = client.post(f"/api/albums/{album.id}/share/regenerate").json()["data"]["url"]
    new_token = new_url.rsplit("/", 1)[-1]

    assert new_token != old_token
    assert await shares_repository.get_live_album_id_by_token(connection, token=old_token) is None
    assert (
        await shares_repository.get_live_album_id_by_token(connection, token=new_token) == album.id
    )


async def test_revoking_leaves_the_album_without_a_live_link(client, connection):
    owner = await log_in(client, connection)
    album = await create_album(connection, owner_id=owner.id)
    url = client.get(f"/api/albums/{album.id}/share").json()["data"]["url"]
    token = url.rsplit("/", 1)[-1]

    revoke_response = client.post(f"/api/albums/{album.id}/share/revoke")

    assert revoke_response.status_code == 200
    assert await shares_repository.get_live_token(connection, album_id=album.id) is None
    assert await shares_repository.get_live_album_id_by_token(connection, token=token) is None


async def test_entering_is_a_write_not_a_read(client, connection):
    owner = await create_user(connection)
    album = await create_album(connection, owner_id=owner.id)
    _, token = await create_share_token(connection, album_id=album.id)
    await log_in(client, connection)

    response = client.get(f"/api/shares/{token}")

    assert response.status_code == 405


async def test_unknown_revoked_and_foreign_tokens_answer_identically(client, connection):
    owner = await create_user(connection)
    album = await create_album(connection, owner_id=owner.id)
    _, revoked_token = await create_share_token(connection, album_id=album.id)
    await shares_repository.revoke_live_token(connection, album_id=album.id)
    other_owner = await create_user(connection)
    other_album = await create_album(connection, owner_id=other_owner.id)
    _, foreign_token = await create_share_token(connection, album_id=other_album.id)
    await shares_repository.revoke_live_token(connection, album_id=other_album.id)
    await log_in(client, connection)

    unknown_response = client.post(f"/api/shares/{uuid.uuid4()}")
    revoked_response = client.post(f"/api/shares/{revoked_token}")
    foreign_response = client.post(f"/api/shares/{foreign_token}")

    assert unknown_response.status_code == revoked_response.status_code == 404
    assert unknown_response.json() == revoked_response.json() == foreign_response.json()


async def test_entering_an_expired_album_answers_like_an_unknown_token(
    client, connection, monkeypatch
):
    """The album's row and its live token can both still exist -- the
    physical delete is deferred -- but entering SHALL respond exactly as it
    does for a token that never existed, and SHALL NOT grant membership.
    """
    monkeypatch.setattr(albums_settings, "album_retention_days", 30)
    owner = await create_user(connection)
    album = await create_album(
        connection, owner_id=owner.id, renewed_at=datetime.now(UTC) - timedelta(days=31)
    )
    _, token = await create_share_token(connection, album_id=album.id)
    entrant = await log_in(client, connection)

    unknown_response = client.post(f"/api/shares/{uuid.uuid4()}")
    expired_response = client.post(f"/api/shares/{token}")

    assert expired_response.status_code == unknown_response.status_code == 404
    assert expired_response.json() == unknown_response.json()
    assert (
        await albums_repository.is_member(connection, album_id=album.id, user_id=entrant.id)
        is False
    )


async def test_entering_grants_membership(client, connection):
    owner = await create_user(connection)
    album = await create_album(connection, owner_id=owner.id)
    _, token = await create_share_token(connection, album_id=album.id)
    entrant = await log_in(client, connection)

    response = client.post(f"/api/shares/{token}")

    assert response.status_code == 200
    assert response.json()["data"]["albumId"] == str(album.id)
    assert (
        await albums_repository.is_member(connection, album_id=album.id, user_id=entrant.id) is True
    )


async def test_entering_twice_does_not_duplicate_membership(client, connection):
    owner = await create_user(connection)
    album = await create_album(connection, owner_id=owner.id)
    _, token = await create_share_token(connection, album_id=album.id)
    entrant = await log_in(client, connection)

    client.post(f"/api/shares/{token}")
    client.post(f"/api/shares/{token}")

    rows = await albums_repository.list_member_albums(connection, user_id=entrant.id)
    assert len(rows) == 1


async def test_revoking_the_link_does_not_evict_existing_members(client, connection):
    owner = await create_user(connection)
    album = await create_album(connection, owner_id=owner.id)
    _, token = await create_share_token(connection, album_id=album.id)
    member = await log_in(client, connection)
    client.post(f"/api/shares/{token}")

    await shares_repository.revoke_live_token(connection, album_id=album.id)

    assert (
        await albums_repository.is_member(connection, album_id=album.id, user_id=member.id) is True
    )


async def test_the_owner_can_rate_their_own_album_without_ever_using_the_link(client, connection):
    owner = await log_in(client, connection)
    album = await create_album(connection, owner_id=owner.id)

    response = client.get(f"/api/albums/{album.id}/pending")

    assert response.status_code == 200
