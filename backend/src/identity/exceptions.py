class InvalidCodeError(Exception):
    """Raised when a provider's `exchange_code` cannot produce an
    identity: the code is invalid, doesn't belong to this provider, has
    expired, or was already exchanged once."""
