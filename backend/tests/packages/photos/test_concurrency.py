"""D12: the position each batch assigns, and the occupancy each counts
(D14), come from a lock on the album row -- not from hoping requests
never overlap. This is the one place that lock actually has to be
proven, with two real, independent connections racing for real.
"""

import asyncio

from sqlalchemy import text

from src.packages.photos import service
from src.packages.photos.schemas import GrantFileInput
from src.packages.quota import repository as quota_repository
from tests.factories import create_album, create_user


async def test_two_batches_granted_at_once_never_claim_the_same_position(test_engine, fake_storage):
    async with test_engine.begin() as setup:
        user = await create_user(setup)
        album = await create_album(setup, owner_id=user.id)

    files = [GrantFileInput(content_type="image/jpeg", size=1000, width=None, height=None)]

    async def grant_one():
        async with test_engine.begin() as connection:
            return await service.grant_batch(
                connection, album_id=album.id, owner_id=user.id, files=files
            )

    try:
        first_result, second_result = await asyncio.gather(grant_one(), grant_one())

        first_position = first_result.granted[0].position
        second_position = second_result.granted[0].position
        assert {first_position, second_position} == {1, 2}
    finally:
        async with test_engine.begin() as cleanup:
            await cleanup.execute(text("delete from users where id = :id"), {"id": user.id})


async def test_two_batches_in_different_albums_never_exceed_the_accounts_space(
    test_engine, fake_storage, monkeypatch
):
    """D1: the account's limit spans every album its owner has, so the
    point of exclusion has to be the person and not the album. Two
    batches in two albums of the same person lock two different rows and
    would each read the same total, granting twice what fits.

    Asserted over the usage the account is left with, never over what
    either call returned: which of the two wins the lock is a race, and
    the invariant is that between them they never pass the limit.
    """
    monkeypatch.setattr("src.packages.photos.service.photos_settings.account_max_bytes", 1_500)
    async with test_engine.begin() as setup:
        user = await create_user(setup)
        first = await create_album(setup, owner_id=user.id, title="First")
        second = await create_album(setup, owner_id=user.id, title="Second")

    files = [GrantFileInput(content_type="image/jpeg", size=1_000, width=None, height=None)]

    async def grant_in(album_id):
        async with test_engine.begin() as connection:
            return await service.grant_batch(
                connection, album_id=album_id, owner_id=user.id, files=files
            )

    try:
        await asyncio.gather(grant_in(first.id), grant_in(second.id), return_exceptions=True)

        async with test_engine.begin() as check:
            used = await quota_repository.account_used_bytes(check, owner_id=user.id)
        assert used <= 1_500
    finally:
        async with test_engine.begin() as cleanup:
            await cleanup.execute(text("delete from users where id = :id"), {"id": user.id})
