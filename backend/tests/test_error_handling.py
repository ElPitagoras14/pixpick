"""Exercises the API-wide response envelope and exception handling against a
throwaway app: none of this depends on a real domain endpoint existing yet,
and it must keep working unchanged once one does.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src import handlers as handlers_module
from src.exceptions import (
    ForbiddenError,
    InsufficientCapacityError,
    NotFoundError,
    StateConflictError,
    UnauthenticatedError,
    ValidationFailedError,
)
from src.handlers import register_exception_handlers
from src.models import ApiModel
from src.responses import Envelope


class _Widget(ApiModel):
    the_value: int


class _Gadget(ApiModel):
    another_value: str


def _build_app() -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/widget")
    def get_widget() -> Envelope[_Widget]:
        return Envelope(data=_Widget(the_value=1))

    @app.get("/gadget")
    def get_gadget() -> Envelope[_Gadget]:
        return Envelope(data=_Gadget(another_value="hi"))

    @app.get("/needs-auth")
    def needs_auth():
        raise UnauthenticatedError()

    @app.get("/needs-permission")
    def needs_permission():
        raise ForbiddenError()

    @app.get("/missing")
    def missing():
        raise NotFoundError()

    @app.get("/bad-field")
    def bad_field():
        raise ValidationFailedError("email", "must be a valid address")

    # Covered here rather than through a domain endpoint: no flow raises
    # this today -- the one that did, a batch that doesn't fit, became a
    # partial grant instead -- and the shape a state conflict
    # answers with is still the API's own contract, so it keeps being
    # exercised where the rest of the handlers are.
    @app.get("/conflicted")
    def conflicted():
        raise StateConflictError(
            "out_of_room", "there is room for 1 more", details={"remaining": 1}
        )

    @app.post("/echo")
    def echo(payload: _Widget) -> Envelope[_Widget]:
        return Envelope(data=payload)

    @app.get("/boom")
    def boom():
        raise RuntimeError("leaked detail nobody should see, select * from users")

    @app.get("/busy")
    def busy():
        raise InsufficientCapacityError(retry_after_seconds=5)

    return app


def _client() -> TestClient:
    return TestClient(_build_app(), raise_server_exceptions=False)


def test_two_distinct_successful_endpoints_share_the_same_structure():
    client = _client()

    widget = client.get("/widget").json()
    gadget = client.get("/gadget").json()

    assert set(widget.keys()) == {"data", "error"} == set(gadget.keys())
    assert widget["error"] is None
    assert gadget["error"] is None


def test_a_client_tells_success_from_error_by_the_shape_alone():
    client = _client()

    ok_body = client.get("/widget").json()
    error_body = client.get("/missing").json()

    assert ok_body["data"] is not None and ok_body["error"] is None
    assert error_body["data"] is None and error_body["error"] is not None


def test_camel_case_is_the_client_facing_convention_and_the_schema_name_does_not_leak():
    client = _client()

    body = client.get("/widget").json()

    assert "theValue" in body["data"]
    assert "the_value" not in body["data"]


def test_unauthenticated_responds_401():
    response = _client().get("/needs-auth")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthenticated"


def test_forbidden_responds_403():
    response = _client().get("/needs-permission")
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "forbidden"


def test_not_found_responds_404():
    response = _client().get("/missing")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_validation_failure_names_the_field_and_reason():
    response = _client().get("/bad-field")
    body = response.json()

    assert response.status_code == 422
    assert body["error"]["field"] == "email"
    assert "must be a valid address" in body["error"]["message"]


def test_a_malformed_request_body_names_the_field_too():
    response = _client().post("/echo", json={"theValue": "not-an-int"})
    body = response.json()

    assert response.status_code == 422
    assert body["error"]["field"]


def test_an_unforeseen_failure_is_generic_and_carries_a_request_id():
    response = _client().get("/boom")
    body = response.json()

    assert response.status_code == 500
    assert body["error"]["requestId"]
    error_text = str(body["error"])
    assert "select" not in error_text.lower()
    assert "RuntimeError" not in error_text
    assert "leaked detail" not in error_text


def test_an_unmatched_route_still_comes_back_in_the_project_shape():
    response = _client().get("/does-not-exist")

    assert response.status_code == 404
    body = response.json()
    assert set(body.keys()) == {"data", "error"}


def test_insufficient_capacity_responds_503_with_a_retry_after(monkeypatch):
    """Distinguishable from both a validation failure
    (no field named) and an unforeseen error (no request id, and --
    unlike /boom above, which does call it -- nothing logged as an
    error, since this is an expected, load-shedding response and not a
    defect to investigate), and it carries how long to wait before
    trying again."""
    monkeypatch.setattr(handlers_module.logger, "error", lambda *a, **k: pytest.fail("logged"))

    response = _client().get("/busy")
    body = response.json()

    assert response.status_code == 503
    assert response.headers["retry-after"] == "5"
    assert body["error"]["code"] == "insufficient_capacity"
    assert body["error"]["retryAfterSeconds"] == 5
    assert body["error"]["field"] is None
    assert body["error"]["requestId"] is None


def test_a_state_conflict_is_not_presented_as_a_validation_failure():
    """A state conflict is resolved by changing the resource and retrying
    the same request, a validation failure by changing the request -- so
    they answer with different statuses, and the conflict names no field.
    """
    response = _client().get("/conflicted")

    assert response.status_code == 409
    error = response.json()["error"]
    assert error["code"] == "out_of_room"
    assert error["field"] is None
    assert error["details"] == {"remaining": 1}
