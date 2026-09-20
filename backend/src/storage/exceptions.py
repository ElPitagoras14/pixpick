class StorageError(Exception):
    """Base class for object storage failures translated for the rest of the
    app.

    Consumers SHALL see one of these, never the provider's own exception or
    message (a storage failure arrives as a domain error).
    """


class StorageUnavailableError(StorageError):
    """Raised when the storage cannot be reached, or rejects an operation
    for a reason its caller has no business seeing."""


class StorageNotReadyError(StorageError):
    """Raised when the storage answers but the space this project keeps its
    objects in isn't there.

    Its own type, not `StorageUnavailableError`: the two are fixed
    differently -- this one by creating the bucket at the provider, that one
    by looking at the network or the service -- so sharing a type would send
    the reader of a startup error to the wrong place.
    """
