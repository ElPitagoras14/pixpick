import secrets


def generate_share_token() -> str:
    """From a cryptographic random source, derived from nothing knowable --
    not the album's id, not a counter, not the creation time.

    Stored in plain text, unlike a session token: the owner has to be able
    to fetch the same live link back, and this one leaking is read access
    to one album, not an account."""
    return secrets.token_urlsafe(32)
