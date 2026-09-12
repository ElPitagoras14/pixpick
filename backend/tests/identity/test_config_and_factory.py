import pytest
from pydantic import ValidationError

from src.identity.config import IdentitySettings
from src.identity.factory import LocalProviderNotAllowedError, build_auth_port


def test_an_unrecognized_provider_fails_to_validate():
    """Startup fails naming the accepted values (identity-provider spec):
    this is what a Literal's own validation error already does."""
    with pytest.raises(ValidationError):
        IdentitySettings(identity_provider="bogus")


def test_local_provider_refuses_outside_development(monkeypatch):
    monkeypatch.setattr("src.identity.factory.settings.environment", "production")
    monkeypatch.setattr("src.identity.factory.identity_settings.identity_provider", "local")

    with pytest.raises(LocalProviderNotAllowedError):
        build_auth_port()


def test_local_provider_is_allowed_in_development(monkeypatch):
    monkeypatch.setattr("src.identity.factory.settings.environment", "development")
    monkeypatch.setattr("src.identity.factory.identity_settings.identity_provider", "local")

    assert build_auth_port() is not None
