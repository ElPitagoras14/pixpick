class DatabaseError(Exception):
    """Base class for data-layer failures translated for the rest of the app.

    Consumers SHALL see one of these, never the driver's or the access
    layer's original exception (database-access spec).
    """


class DatabaseUnavailableError(DatabaseError):
    """Raised when a connection to the database could not be established."""


class QueryExecutionError(DatabaseError):
    """Raised when a query fails once a connection was already obtained."""


# --- Domain-level failures every endpoint's error handling maps to a
# status code (api-conventions spec). ---


class UnauthenticatedError(Exception):
    """Raised when an endpoint that requires a session gets none, or one
    that has expired -- the two are treated identically (session-management
    spec)."""


class ForbiddenError(Exception):
    """Raised when a valid session lacks authorization over the resource
    it asked for, once its existence is already known to the caller."""


class NotFoundError(Exception):
    """Raised when the requested resource does not exist.

    For a resource reached by an opaque identifier, this is also what a
    handler SHALL raise for one that exists but the caller has no access
    to (api-conventions spec) -- the two situations are indistinguishable
    on purpose.
    """


class ValidationFailedError(Exception):
    """Raised for a domain validation failure that isn't expressible as
    a request body's own schema, naming the field responsible."""

    def __init__(self, field: str, message: str) -> None:
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")


class InsufficientCapacityError(Exception):
    """Raised when a well-formed, authorized request can't be served
    because a shared resource is saturated -- the connection pool
    exhausted, for now (request-throttling spec, api-conventions spec) --
    rather than because of anything about the request itself. Answered
    with 503 and a retry-after, never as a validation failure or as an
    unforeseen error (api-conventions spec): the three call for different
    reactions from whoever's asking, and this one calls only for trying
    the same request again once the wait is over.
    """

    def __init__(self, retry_after_seconds: int) -> None:
        self.retry_after_seconds = retry_after_seconds
        super().__init__(f"insufficient capacity, retry after {retry_after_seconds}s")


class StateConflictError(Exception):
    """Raised when a well-formed request cannot proceed because of the
    state of the resource it targets -- never because of what was sent
    (api-conventions spec, added by add-albums-and-upload for the
    album-full case). Always answered with 409, which is what tells a
    client this apart from a validation failure (422): the fix is to
    change the resource's state and retry the same request unmodified,
    not to correct the request.
    """

    def __init__(self, code: str, message: str, *, details: dict | None = None) -> None:
        self.code = code
        self.message = message
        self.details = details
        super().__init__(f"{code}: {message}")
