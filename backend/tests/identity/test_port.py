import pytest
from pydantic import ValidationError

from src.identity.port import ExternalIdentity


def test_provider_and_provider_user_id_are_required():
    with pytest.raises(ValidationError):
        ExternalIdentity(email="person@example.com")


def test_descriptive_fields_may_be_absent():
    identity = ExternalIdentity(provider="local", provider_user_id="1")

    assert identity.email is None
    assert identity.name is None
    assert identity.avatar_url is None
