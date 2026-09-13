import secrets


def generate_share_token() -> str:
    """An unpredictable token (album-sharing spec): from a cryptographic
    random source, and derived from nothing knowable -- not the album's
    id, not a counter, not the creation time. The same reasoning
    `auth.security.generate_session_token` applies to sessions.

    Stored in plain text, unlike a session token (see the migration's own
    comment): the owner SHALL be able to fetch the same live link back on
    demand, which a one-way hash would make impossible, and this token's
    blast radius if leaked is far smaller than a session's.
    """
    return secrets.token_urlsafe(32)
