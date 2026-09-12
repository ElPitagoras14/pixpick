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
