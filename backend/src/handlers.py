import uuid

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.exceptions import (
    DatabaseError,
    ForbiddenError,
    NotFoundError,
    UnauthenticatedError,
    ValidationFailedError,
)
from src.identity.exceptions import InvalidCodeError
from src.log import logger
from src.packages.auth.exceptions import InvalidStateError
from src.responses import error_envelope


async def _database_error_handler(request: Request, exc: DatabaseError) -> JSONResponse:
    """Translates any data-layer failure into a response with no trace of
    the query, the driver, or table/column names (database-access spec).
    """
    return JSONResponse(
        status_code=503,
        content=error_envelope("service_unavailable", "the service is temporarily unavailable"),
    )


async def _unauthenticated_handler(request: Request, exc: UnauthenticatedError) -> JSONResponse:
    return JSONResponse(
        status_code=401,
        content=error_envelope("unauthenticated", "authentication is required"),
    )


async def _forbidden_handler(request: Request, exc: ForbiddenError) -> JSONResponse:
    return JSONResponse(
        status_code=403,
        content=error_envelope("forbidden", "you are not allowed to do that"),
    )


async def _not_found_handler(request: Request, exc: NotFoundError) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content=error_envelope("not_found", "the requested resource does not exist"),
    )


async def _validation_failed_handler(request: Request, exc: ValidationFailedError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content=error_envelope("validation_failed", exc.message, field=exc.field),
    )


async def _invalid_state_handler(request: Request, exc: InvalidStateError) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content=error_envelope(
            "invalid_state", "the sign-in attempt could not be verified; please try again"
        ),
    )


async def _invalid_code_handler(request: Request, exc: InvalidCodeError) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content=error_envelope("invalid_code", "the sign-in code is invalid or expired"),
    )


async def _request_validation_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """FastAPI's own validation failure, reshaped into this project's
    envelope instead of its default body (api-conventions spec)."""
    first_error = exc.errors()[0]
    field = ".".join(str(part) for part in first_error["loc"] if part != "body")
    return JSONResponse(
        status_code=422,
        content=error_envelope("validation_failed", first_error["msg"], field=field or None),
    )


async def _http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Catches anything raised as a plain `HTTPException` -- including the
    framework's own 404 for an unmatched route -- so even those still
    come back in this project's shape (api-conventions spec)."""
    return JSONResponse(
        status_code=exc.status_code,
        content=error_envelope("http_error", str(exc.detail)),
    )


async def _unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Anything not previously matched is unforeseen: the response stays
    generic and carries an id that identifies the logged detail, instead
    of the exception's own message, traceback, or origin (api-conventions
    spec)."""
    request_id = str(uuid.uuid4())
    logger.opt(exception=exc).error(f"unhandled error, request_id={request_id}")
    return JSONResponse(
        status_code=500,
        content=error_envelope(
            "internal_error", "an unexpected error occurred", request_id=request_id
        ),
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(DatabaseError, _database_error_handler)
    app.add_exception_handler(UnauthenticatedError, _unauthenticated_handler)
    app.add_exception_handler(ForbiddenError, _forbidden_handler)
    app.add_exception_handler(NotFoundError, _not_found_handler)
    app.add_exception_handler(ValidationFailedError, _validation_failed_handler)
    app.add_exception_handler(InvalidStateError, _invalid_state_handler)
    app.add_exception_handler(InvalidCodeError, _invalid_code_handler)
    app.add_exception_handler(RequestValidationError, _request_validation_handler)
    app.add_exception_handler(StarletteHTTPException, _http_exception_handler)
    # Registered last (Starlette resolves by the most specific match in
    # the exception's MRO, not registration order) so anything with no
    # handler of its own still lands here instead of propagating as a
    # bare 500 with no body.
    app.add_exception_handler(Exception, _unhandled_error_handler)
