"""D12: the position each batch assigns, and the occupancy each counts
(D14), come from a lock on the album row -- not from hoping requests
never overlap. This is the one place that lock actually has to be
proven, with two real, independent connections racing for real.
"""

import asyncio

from sqlalchemy import text

from src.packages.photos import service
from src.packages.photos.schemas import GrantFileInput
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

        first_position = first_result[0][1]
        second_position = second_result[0][1]
        assert {first_position, second_position} == {1, 2}
    finally:
        async with test_engine.begin() as cleanup:
            await cleanup.execute(text("delete from users where id = :id"), {"id": user.id})
