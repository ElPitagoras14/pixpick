"""Every storage failure reaches the rest of the app as one type
(object-storage spec), so a consumer catches the base class and never
has to know which ones exist."""

import pytest

from src.storage.exceptions import (
    StorageError,
    StorageNotReadyError,
    StorageUnavailableError,
)


@pytest.mark.parametrize("failure", [StorageNotReadyError, StorageUnavailableError])
def test_a_consumer_catching_the_base_class_catches_it(failure):
    with pytest.raises(StorageError):
        raise failure("something went wrong")


def test_a_missing_space_is_not_confused_with_an_unreachable_storage():
    """Two causes with two fixes (D3): catching one never catches the
    other."""
    assert not issubclass(StorageNotReadyError, StorageUnavailableError)
    assert not issubclass(StorageUnavailableError, StorageNotReadyError)
