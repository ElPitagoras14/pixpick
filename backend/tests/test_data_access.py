import pytest
from pydantic import BaseModel, ValidationError

from src.database.client import fetch_one, fetch_val, write
from src.exceptions import QueryExecutionError


async def test_a_failed_write_in_a_multi_write_operation_leaves_none_committed(connection):
    """A multi-write operation is atomic (database-access spec): all its
    writes share one connection and one transaction scope (here, a
    savepoint standing in for that scope), and a failure partway through
    leaves none of them committed.
    """
    await write(connection, "create temporary table t_atomic_fail (id int primary key, name text)")

    savepoint = await connection.begin_nested()
    try:
        await write(
            connection,
            "insert into t_atomic_fail (id, name) values (:id, :name)",
            {"id": 1, "name": "a"},
        )
        # Same id again: a primary key violation partway through.
        await write(
            connection,
            "insert into t_atomic_fail (id, name) values (:id, :name)",
            {"id": 1, "name": "b"},
        )
    except QueryExecutionError:
        await savepoint.rollback()
    else:
        pytest.fail("expected the second insert to fail")

    count = await fetch_val(connection, "select count(*) from t_atomic_fail")
    assert count == 0


async def test_a_multi_write_operation_without_failure_commits_all_of_it(connection):
    await write(connection, "create temporary table t_atomic_ok (id int primary key, name text)")

    savepoint = await connection.begin_nested()
    await write(connection, "insert into t_atomic_ok (id, name) values (1, 'a')")
    await write(connection, "insert into t_atomic_ok (id, name) values (2, 'b')")
    await savepoint.commit()

    count = await fetch_val(connection, "select count(*) from t_atomic_ok")
    assert count == 2


async def test_fetch_one_fails_at_the_boundary_when_a_declared_field_is_missing(connection):
    """D4: a query that stops returning a field the model declares fails
    while the model is being constructed, not downstream as a missing key.
    """

    class RowWithMissingField(BaseModel):
        id: int
        never_returned: str

    await write(connection, "create temporary table t_model_mismatch (id int)")
    await write(connection, "insert into t_model_mismatch (id) values (1)")

    with pytest.raises(ValidationError):
        await fetch_one(connection, "select id from t_model_mismatch", RowWithMissingField)
