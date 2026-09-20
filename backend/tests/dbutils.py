"""Schema introspection helpers the data-layer tests need, since this
change creates no domain tables to query directly.
"""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection


async def tables_with_column(connection: AsyncConnection, column: str) -> list[str]:
    """Names of the public-schema *base tables* that declare `column`.

    Joined against `information_schema.tables` and filtered to `BASE TABLE`:
    a view built on a table with this column -- such as `available_photos`
    on `photos` -- reports the same column through
    `information_schema.columns` but can never have a trigger of its own, so
    including it here would make this helper report a false gap.
    """
    result = await connection.execute(
        text(
            "select c.table_name from information_schema.columns c "
            "join information_schema.tables t "
            "  on t.table_schema = c.table_schema and t.table_name = c.table_name "
            "where c.table_schema = 'public' and c.column_name = :column "
            "  and t.table_type = 'BASE TABLE'"
        ),
        {"column": column},
    )
    return [row[0] for row in result.all()]


async def triggers_of_table(connection: AsyncConnection, table: str) -> list[str]:
    """Names of the triggers declared on `table`."""
    result = await connection.execute(
        # Parenthesized so SQLAlchemy's bind-parameter parser doesn't choke
        # on ":table" immediately followed by Postgres's "::" cast operator
        # -- untested until this change added the first real tables to
        # check (see tasks.md 1.3).
        text(
            "select tgname from pg_trigger where tgrelid = (:table)::regclass and not tgisinternal"
        ),
        {"table": table},
    )
    return [row[0] for row in result.all()]
