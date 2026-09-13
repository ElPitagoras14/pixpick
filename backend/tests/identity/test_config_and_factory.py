import pytest
from pydantic import ValidationError

from src.identity.config import IdentitySettings
from src.identity.factory import (
    LocalProviderNotAllowedError,
    MissingCredentialsError,
    build_auth_port,
)


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


def test_google_provider_without_credentials_fails_to_start(monkeypatch):
    monkeypatch.setattr("src.identity.factory.identity_settings.identity_provider", "google")
    monkeypatch.setattr("src.identity.factory.identity_settings.google_client_id", None)
    monkeypatch.setattr("src.identity.factory.identity_settings.google_client_secret", None)

    with pytest.raises(MissingCredentialsError, match="GOOGLE_CLIENT_ID.*GOOGLE_CLIENT_SECRET"):
        build_auth_port()


def test_an_empty_credential_is_treated_as_missing(monkeypatch):
    monkeypatch.setattr("src.identity.factory.identity_settings.identity_provider", "google")
    monkeypatch.setattr("src.identity.factory.identity_settings.google_client_id", "")
    monkeypatch.setattr("src.identity.factory.identity_settings.google_client_secret", "a-secret")

    with pytest.raises(MissingCredentialsError, match="GOOGLE_CLIENT_ID"):
        build_auth_port()


def test_google_provider_is_built_once_credentials_are_present(monkeypatch):
    monkeypatch.setattr("src.identity.factory.identity_settings.identity_provider", "google")
    monkeypatch.setattr("src.identity.factory.identity_settings.google_client_id", "client-id")
    monkeypatch.setattr("src.identity.factory.identity_settings.google_client_secret", "a-secret")

    assert build_auth_port() is not None


def test_the_inactive_google_providers_missing_credentials_do_not_block_local(monkeypatch):
    monkeypatch.setattr("src.identity.factory.settings.environment", "development")
    monkeypatch.setattr("src.identity.factory.identity_settings.identity_provider", "local")
    monkeypatch.setattr("src.identity.factory.identity_settings.google_client_id", None)
    monkeypatch.setattr("src.identity.factory.identity_settings.google_client_secret", None)

    assert build_auth_port() is not None
