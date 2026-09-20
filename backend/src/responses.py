from .models import ApiModel


class ErrorBody(ApiModel):
    """What an error response names: a machine-readable `code`, a message
    a person could read, and situational extras that stay `None` when
    they don't apply -- `field` for a validation failure, `request_id`
    for an unforeseen one, `details` for whatever a state conflict has
    that's quantifiable, such as how much room is left, `retry_after_seconds`
    for a rejection caused by a lack of capacity rather than by either of
    those (api-conventions spec, harden-local-profile).
    """

    code: str
    message: str
    field: str | None = None
    request_id: str | None = None
    details: dict | None = None
    retry_after_seconds: int | None = None


class Envelope[T](ApiModel):
    """The one shape every endpoint's body has (api-conventions spec):
    `data` on success, `error` on failure, and the other always `None` --
    never both, never neither. A client tells success from failure from
    this shape alone, without knowing the endpoint.
    """

    data: T | None = None
    error: ErrorBody | None = None


def error_envelope(
    code: str,
    message: str,
    *,
    field: str | None = None,
    request_id: str | None = None,
    details: dict | None = None,
    retry_after_seconds: int | None = None,
) -> dict:
    """The JSON-ready body for an error response. A plain dict, not a
    `JSONResponse`: exception handlers own the status code, this only
    owns the shape.
    """
    body = Envelope(
        error=ErrorBody(
            code=code,
            message=message,
            field=field,
            request_id=request_id,
            details=details,
            retry_after_seconds=retry_after_seconds,
        )
    )
    return body.model_dump(mode="json", by_alias=True)
