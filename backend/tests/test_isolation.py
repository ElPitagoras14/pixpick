"""Guards the `connection` fixture's isolation guarantee itself: both
functions below write to a *non-temporary* table of the same name -- so,
unlike a session-scoped temporary table, whether it's actually isolated
depends entirely on the fixture's rollback, not on Postgres scoping it to
the connection for free. Neither test may see the other's row, regardless of
which runs first.
"""

from pydantic import BaseModel

from src.database.client import fetch_all, write


class Row(BaseModel):
    name: str


async def _create_write_and_check_alone(connection, name: str) -> None:
    await write(connection, "create table if not exists t_isolation (name text)")
    rows = await fetch_all(connection, "select name from t_isolation", Row)
    assert rows == [], "saw a row from a previous test: rollback isolation is broken"
    await write(connection, "insert into t_isolation (name) values (:name)", {"name": name})
    rows = await fetch_all(connection, "select name from t_isolation", Row)
    assert [row.name for row in rows] == [name]


async def test_isolation_a(connection):
    await _create_write_and_check_alone(connection, "a")


async def test_isolation_b(connection):
    await _create_write_and_check_alone(connection, "b")
