from urllib.parse import urlsplit

from .config import DEFAULT_RETURN_TO


def sanitize_return_to(value: str | None) -> str:
    """Accepts only a path on this same site: an absolute URL to another
    site (an explicit scheme, or the protocol-relative form a leading double
    slash produces) is discarded in favor of the default, never followed.
    """
    if not value:
        return DEFAULT_RETURN_TO
    if not value.startswith("/") or value.startswith("//"):
        return DEFAULT_RETURN_TO
    parsed = urlsplit(value)
    if parsed.scheme or parsed.netloc:
        return DEFAULT_RETURN_TO
    return value
