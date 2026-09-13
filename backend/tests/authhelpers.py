"""A shared way for a package's tests to become an authenticated user,
without going through the full local-provider HTTP cycle every time --
that cycle is already covered by `tests/packages/auth/test_router.py`.
"""

from sqlalchemy.ext.asyncio import AsyncConnection

from tests.factories import UserRow, create_session, create_user


async def log_in(client, connection: AsyncConnection, **user_kwargs) -> UserRow:
    """Creates a user and session on `connection` -- the same one
    `client`'s `get_connection` override reuses -- and carries the
    session cookie so `client`'s next request authenticates as them.
    """
    user = await create_user(connection, **user_kwargs)
    _, token = await create_session(connection, user_id=user.id)
    client.cookies.set("session", token)
    return user
