import asyncio
import os
import subprocess
import sys
from collections.abc import AsyncIterator
from pathlib import Path

import psycopg
import pytest
import pytest_asyncio
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, create_async_engine

from src.database.dependencies import get_connection
from src.main import app

# psycopg3's async mode cannot run on asyncio's default ProactorEventLoop on
# Windows (see backend/src/loop.py). pytest-asyncio creates its loop through
# the current policy, so setting it here -- before any test runs -- is
# enough; it needs no equivalent of uvicorn's --loop workaround.
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

load_dotenv()

_REPO_ROOT = Path(__file__).resolve().parents[2]
_MIGRATIONS_DIR = _REPO_ROOT / "dbmate" / "migrations"
# Keep in sync with dbmate/Dockerfile's FROM line (database-migrations spec:
# every reference to the tool's version must name the same one).
_DBMATE_IMAGE = "ghcr.io/amacneil/dbmate:2.35.1"

_POSTGRES_USER = os.environ["POSTGRES_USER"]
_POSTGRES_PASSWORD = os.environ["POSTGRES_PASSWORD"]
_POSTGRES_DB = os.environ["POSTGRES_DB"]
_POSTGRES_PORT = os.environ["POSTGRES_PORT"]

# Derived from the dev database's own name, never from a separately
# overridable setting -- there is no variable a stray copy-paste could set
# to the dev database's name instead.
TEST_DATABASE_NAME = f"{_POSTGRES_DB}_test"


def _require_test_database(name: str) -> None:
    """Refuses to touch anything that isn't the test database (Risks: a
    developer running the suite against the dev database by mistake)."""
    if name == _POSTGRES_DB or not name.endswith("_test"):
        raise RuntimeError(
            f"refusing to prepare the test suite against database {name!r}: "
            f"it is not the expected test database ({TEST_DATABASE_NAME!r})"
        )


def _create_database_if_missing(name: str) -> None:
    _require_test_database(name)
    connection = psycopg.connect(
        host="localhost",
        port=_POSTGRES_PORT,
        user=_POSTGRES_USER,
        password=_POSTGRES_PASSWORD,
        dbname=_POSTGRES_DB,
        autocommit=True,
    )
    try:
        exists = connection.execute(
            "select 1 from pg_database where datname = %s", (name,)
        ).fetchone()
        if exists is None:
            connection.execute(f'create database "{name}"')
    finally:
        connection.close()


def _migrate(name: str) -> None:
    """Applies the project's migrations with the same pinned dbmate version
    used everywhere else (D10)."""
    _require_test_database(name)
    database_url = (
        f"postgres://{_POSTGRES_USER}:{_POSTGRES_PASSWORD}"
        f"@host.docker.internal:{_POSTGRES_PORT}/{name}?sslmode=disable"
    )
    subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            "--add-host=host.docker.internal:host-gateway",
            "-e",
            f"DATABASE_URL={database_url}",
            "-v",
            f"{_MIGRATIONS_DIR}:/db/migrations:ro",
            _DBMATE_IMAGE,
            "--no-dump-schema",
            "migrate",
        ],
        check=True,
    )


def pytest_configure(config: pytest.Config) -> None:
    """Prepares the test database once, before any test runs (single
    command, no manual steps -- backend-testing spec)."""
    _create_database_if_missing(TEST_DATABASE_NAME)
    _migrate(TEST_DATABASE_NAME)


@pytest.fixture(scope="session")
def test_engine() -> AsyncEngine:
    url = (
        f"postgresql+psycopg://{_POSTGRES_USER}:{_POSTGRES_PASSWORD}"
        f"@localhost:{_POSTGRES_PORT}/{TEST_DATABASE_NAME}"
    )
    # A pool of its own, much smaller than the app's (D11): the suite runs
    # one test at a time and has no reason to reserve twenty connections.
    return create_async_engine(url, pool_size=2, max_overflow=3)


@pytest.fixture(autouse=True)
def _point_the_default_engine_at_the_test_database(test_engine, monkeypatch):
    """A handful of services open their own transaction through
    `database.utils.transaction()` instead of the per-request connection
    (D6 in add-albums-and-upload: deleting a photo's object is a network
    call, and a transaction that deletes its row SHALL fully commit --
    releasing its pooled connection -- before that call, never hold it
    open across the wait). Called with no explicit engine, as production
    always calls it, that helper defaults to `database.client.engine`;
    this points the same name at the test database for the duration of
    every test, so that default is never the developer's own.
    """
    monkeypatch.setattr("src.database.client.engine", test_engine)


@pytest.fixture
def fake_storage(monkeypatch):
    """Swaps the real storage adapter for the in-memory double in both
    packages that call it, so albums/photos tests never need MinIO up.
    The contract suite (`tests/storage/`) is what verifies the fake
    behaves like the real thing (D9, D10) -- these tests only rely on
    that already being true.

    Also stubs out the warm-up task: a photo the fake storage marks
    available has no real object behind it, so warming its variant would
    only mean a real, slow round trip to nginx/imgproxy for something
    guaranteed to 404. `tests/packages/photos/test_upload_integration.py`
    is what actually exercises warming against the real stack (task 4.3).
    """
    from tests.fakes import FakeStoragePort

    fake = FakeStoragePort()
    monkeypatch.setattr("src.packages.albums.service.storage_port", fake)
    monkeypatch.setattr("src.packages.photos.service.storage_port", fake)
    monkeypatch.setattr("src.packages.photos.reconcile.storage_port", fake)

    async def _no_op_warm_up(object_keys):
        return None

    monkeypatch.setattr("src.packages.photos.router.warm_up_variants", _no_op_warm_up)
    return fake


@pytest_asyncio.fixture
async def committed_connection(test_engine: AsyncEngine) -> AsyncIterator[AsyncConnection]:
    """A connection that commits for real against the test database,
    unlike `connection` above. Only the tests that exercise a flow
    spanning more than one transaction need this: setting up data through
    the rollback-only `connection` keeps it invisible to a service's own,
    separately opened transaction, which a real commit here does not.

    Callers commit explicitly after each step that must become visible to
    that other transaction (`await connection.commit()`); teardown wipes
    every table `users` cascades to, so nothing leaks into another test.
    """
    async with test_engine.connect() as connection:
        yield connection
    async with test_engine.begin() as cleanup:
        await cleanup.execute(text("delete from users"))


@pytest_asyncio.fixture
async def connection(test_engine: AsyncEngine) -> AsyncIterator[AsyncConnection]:
    """Opens a connection, starts a transaction, yields it, and always
    rolls back on teardown (D9): nothing a test writes is visible to
    another test, regardless of execution order, and nothing is left
    behind to clean up.
    """
    async with test_engine.connect() as connection:
        transaction = await connection.begin()
        try:
            yield connection
        finally:
            await transaction.rollback()


@pytest_asyncio.fixture
async def client(connection: AsyncConnection) -> AsyncIterator[TestClient]:
    """An HTTP client against the real app, with `get_connection`
    overridden to reuse this test's own rollback-only `connection`
    instead of opening one against the dev database. Each request still
    gets its own transaction boundary via a savepoint, mirroring
    production's one-transaction-per-request shape (D3 in
    add-backend-data-layer) while nesting inside the outer rollback that
    undoes everything at teardown.
    """

    async def override_get_connection() -> AsyncIterator[AsyncConnection]:
        async with connection.begin_nested():
            yield connection

    app.dependency_overrides[get_connection] = override_get_connection
    try:
        # Redirects aren't followed automatically: the auth flow's own
        # tests inspect each hop's status and Location header in turn.
        with TestClient(app, follow_redirects=False) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.pop(get_connection, None)
