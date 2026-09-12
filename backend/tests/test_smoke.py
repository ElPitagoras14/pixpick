from sqlalchemy import text

from src.database.client import MAX_OVERFLOW, POOL_SIZE, engine


async def test_suite_sees_the_migrated_schema(connection):
    """Fails if the migrations were never applied: schema_migrations
    wouldn't exist, or wouldn't list 0001."""
    result = await connection.execute(
        text("select version from schema_migrations order by version")
    )
    versions = [row[0] for row in result.all()]
    assert "0001" in versions


def test_engine_declares_the_expected_pool_limits():
    assert engine.pool.size() == POOL_SIZE
    # No public getter for the configured ceiling; this is the pool's own
    # record of it, not a copy of the constant it was built from.
    assert engine.pool._max_overflow == MAX_OVERFLOW
