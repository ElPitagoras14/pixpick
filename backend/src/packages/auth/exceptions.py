class InvalidStateError(Exception):
    """Raised when the callback's state doesn't match the one the login
    cookie recorded, is missing entirely, or was already consumed."""
