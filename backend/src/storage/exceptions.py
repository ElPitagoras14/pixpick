class StorageError(Exception):
    """Base class for object-storage failures translated for the rest of
    the app.

    Consumers SHALL see one of these, never the provider's own exception
    or message (object-storage spec: "un fallo del almacenamiento llega
    como error de dominio").
    """


class StorageUnavailableError(StorageError):
    """Raised when the storage cannot be reached, or rejects an operation
    for a reason its caller has no business seeing."""
