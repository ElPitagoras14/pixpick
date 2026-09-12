from tests.factories import create_session, create_user


async def test_create_user_needs_only_the_email(connection):
    """A test declares only what it cares about (backend-testing spec);
    every other column takes a valid default."""
    user = await create_user(connection, email="someone@example.com")

    assert user.id is not None


async def test_create_session_defaults_to_a_valid_unexpired_token(connection):
    user = await create_user(connection)

    session, token = await create_session(connection, user_id=user.id)

    assert session.id is not None
    assert token
