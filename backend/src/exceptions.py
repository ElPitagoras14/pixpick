class DatabaseError(Exception):
    """Consumers see one of these, never the driver's own exception."""


class DatabaseUnavailableError(DatabaseError):
    """Raised when a connection to the database could not be established."""


class QueryExecutionError(DatabaseError):
    """Raised when a query fails once a connection was already obtained."""


# --- Domain-level failures every endpoint's error handling maps to a status
# code. ---


class UnauthenticatedError(Exception):
    """No session, or an expired one -- the two are treated identically."""


class ForbiddenError(Exception):
    """A valid session without authorization over a resource the caller
    already knows exists."""


class NotFoundError(Exception):
    """Also what a resource reached by an opaque identifier raises when it
    exists but the caller has no access to it: the two are indistinguishable
    on purpose."""


class ValidationFailedError(Exception):
    """A validation failure a request body's own schema can't express."""

    def __init__(self, field: str, message: str) -> None:
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")


class InsufficientCapacityError(Exception):
    """A shared resource is saturated -- the connection pool, for now --
    not anything about the request. Answered with 503 and a retry-after, so
    the caller retries the same request unchanged."""

    def __init__(self, retry_after_seconds: int) -> None:
        self.retry_after_seconds = retry_after_seconds
        super().__init__(f"insufficient capacity, retry after {retry_after_seconds}s")


class StateConflictError(Exception):
    """The resource's state blocks the request, not what was sent. Answered
    with 409, not 422: the fix is to change the state and retry the same
    request."""

    def __init__(self, code: str, message: str, *, details: dict | None = None) -> None:
        self.code = code
        self.message = message
        self.details = details
        super().__init__(f"{code}: {message}")
