"""The one place the two adapters differ on purpose: R2's space is created
once at the provider, so this one checks and never creates. Driven against a
stubbed client, since the real provider is a paid account nobody has to own
to run this suite.
"""

import pytest
from botocore.exceptions import ClientError

from src.storage.adapters.r2 import R2StorageAdapter
from src.storage.exceptions import StorageNotReadyError, StorageUnavailableError


@pytest.fixture
def adapter(monkeypatch) -> R2StorageAdapter:
    monkeypatch.setattr("src.storage.config.storage_settings.r2_access_key_id", "key")
    monkeypatch.setattr("src.storage.config.storage_settings.r2_secret_access_key", "secret")
    monkeypatch.setattr("src.storage.config.storage_settings.r2_bucket", "pixpick")
    monkeypatch.setattr(
        "src.storage.config.storage_settings.r2_endpoint", "https://example.r2.example.com"
    )
    return R2StorageAdapter()


def _answers_with(code: str):
    def _head_bucket(**_kwargs):
        raise ClientError({"Error": {"Code": code}}, "HeadBucket")

    return _head_bucket


async def test_a_missing_space_stops_the_startup_with_its_own_error(adapter, monkeypatch):
    monkeypatch.setattr(adapter._server_client, "head_bucket", _answers_with("404"))

    with pytest.raises(StorageNotReadyError):
        await adapter.ensure_ready()


async def test_a_missing_space_is_not_reported_as_an_unreachable_storage(adapter, monkeypatch):
    """Two causes with two fixes: this one is fixed at the provider, so it
    must not arrive as the error that sends the reader to the network.
    """
    monkeypatch.setattr(adapter._server_client, "head_bucket", _answers_with("NoSuchBucket"))

    with pytest.raises(StorageNotReadyError):
        await adapter.ensure_ready()
    with pytest.raises(StorageNotReadyError):
        await adapter.ensure_ready()


async def test_a_storage_that_answers_something_else_is_reported_as_unreachable(
    adapter, monkeypatch
):
    monkeypatch.setattr(adapter._server_client, "head_bucket", _answers_with("AccessDenied"))

    with pytest.raises(StorageUnavailableError):
        await adapter.ensure_ready()


async def test_a_space_that_is_there_prepares_without_creating_anything(adapter, monkeypatch):
    def _forbidden_create(**_kwargs):
        raise AssertionError("ensure_ready must never create this provider's space")

    monkeypatch.setattr(adapter._server_client, "head_bucket", lambda **_kwargs: {})
    monkeypatch.setattr(adapter._server_client, "create_bucket", _forbidden_create)

    await adapter.ensure_ready()
    await adapter.ensure_ready()
