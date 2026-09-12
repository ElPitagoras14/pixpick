from tests.dbutils import tables_with_column, triggers_of_table


async def test_every_table_with_updated_at_has_its_trigger(connection):
    """Passes trivially today -- there are no domain tables yet -- and
    starts failing the moment a table declares updated_at without wiring
    the trigger that keeps it current (D5, Risks).
    """
    tables = await tables_with_column(connection, "updated_at")
    for table in tables:
        triggers = await triggers_of_table(connection, table)
        assert triggers, f"table {table!r} has updated_at but no trigger"
