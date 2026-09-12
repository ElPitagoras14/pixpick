class DatabaseError(Exception):
    """Base class for data-layer failures translated for the rest of the app.

    Consumers SHALL see one of these, never the driver's or the access
    layer's original exception (database-access spec).
    """


class DatabaseUnavailableError(DatabaseError):
    """Raised when a connection to the database could not be established."""


class QueryExecutionError(DatabaseError):
    """Raised when a query fails once a connection was already obtained."""
