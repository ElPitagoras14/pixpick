"""Task 4.6 (request-throttling spec): the pool's own exhaustion is
translated at the one place every write and read goes through, so it
never surfaces as `database/client.py`'s generic `QueryExecutionError` --
and from there, `DatabaseError`'s own 503 -- which would read as the
database itself being down rather than merely busy.
"""

import pytest
from sqlalchemy.exc import TimeoutError as SATimeoutError

from src.database.utils import transaction
from src.exceptions import InsufficientCapacityError


class _RaisingBegin:
    async def __aenter__(self):
        raise SATimeoutError("QueuePool limit of size 20 overflow 0 reached")

    async def __aexit__(self, *exc_info):
        return False


class _ExhaustedEngine:
    """Stands in for `AsyncEngine`: only `begin()` is ever called by
    `transaction()`, and this raises exactly what a real engine does when
    every pooled connection is checked out and none frees up in time."""

    def begin(self):
        return _RaisingBegin()


async def test_a_pool_checkout_timeout_becomes_insufficient_capacity():
    with pytest.raises(InsufficientCapacityError) as excinfo:
        async with transaction(engine=_ExhaustedEngine()):
            pytest.fail("the body SHALL NOT run when the checkout itself times out")

    assert excinfo.value.retry_after_seconds > 0
