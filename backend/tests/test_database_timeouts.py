"""Task 4.7 (database-access spec): the statement timeout is declared as
connection-level GUCs (src/database/client.py), so this confirms it
actually cuts a slow statement off and gives its connection back to the
pool, using an engine of its own with the timeout turned all the way
down instead of waiting out the real one.
"""

import pytest
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import create_async_engine

from src.database.client import POOL_PRE_PING, POOL_RECYCLE_SECONDS
from src.database.client import engine as real_engine
from src.database.config import database_settings


@pytest.fixture
async def short_timeout_engine():
    engine = create_async_engine(
        database_settings.database_url,
        pool_size=1,
        max_overflow=0,
        pool_pre_ping=POOL_PRE_PING,
        pool_recycle=POOL_RECYCLE_SECONDS,
        connect_args={"options": "-c statement_timeout=200"},
    )
    yield engine
    await engine.dispose()


async def test_a_slow_statement_is_interrupted_and_its_connection_freed(short_timeout_engine):
    async with short_timeout_engine.connect() as connection:
        with pytest.raises(SQLAlchemyError):
            await connection.execute(text("select pg_sleep(2)"))

    # The pool has exactly one slot (pool_size=1, max_overflow=0): a
    # second query going through cleanly proves the first's connection
    # came back, instead of the statement timeout leaving it stuck.
    async with short_timeout_engine.connect() as connection:
        result = await connection.execute(text("select 1"))
        assert result.scalar_one() == 1


async def test_the_real_engine_declares_pre_ping_and_recycle():
    assert real_engine.pool._pre_ping is True
    assert real_engine.pool._recycle == POOL_RECYCLE_SECONDS
