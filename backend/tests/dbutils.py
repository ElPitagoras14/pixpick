"""Schema introspection helpers the data-layer tests need, since this
change creates no domain tables to query directly.
"""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection


async def tables_with_column(connection: AsyncConnection, column: str) -> list[str]:
    """Names of the public-schema tables that declare `column`."""
    result = await connection.execute(
        text(
            "select table_name from information_schema.columns "
            "where table_schema = 'public' and column_name = :column"
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
