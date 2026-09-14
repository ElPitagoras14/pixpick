from html.parser import HTMLParser
from urllib.parse import parse_qs, urlparse

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.identity.adapters.local import LocalAuthAdapter, router
from src.identity.exceptions import InvalidCodeError


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(router, prefix="/api")
    return TestClient(app, follow_redirects=False)


async def test_the_cycle_produces_an_identity_with_provider_and_subject():
    adapter = LocalAuthAdapter()

    authorization_url = adapter.authorization_url(state="the-state")
    assert "state=the-state" in authorization_url

    response = _client().post(
        "/api/auth/local/dev-login",
        data={"state": "the-state", "email": "person@example.com", "name": "Person"},
    )
    assert response.status_code == 303

    redirect = urlparse(response.headers["location"])
    query = parse_qs(redirect.query)
    assert query["state"] == ["the-state"]
    code = query["code"][0]

    identity = await adapter.exchange_code(code=code)

    assert identity.provider == "local"
    assert identity.provider_user_id == "person@example.com"
    assert identity.email == "person@example.com"


async def test_a_code_cannot_be_exchanged_twice():
    adapter = LocalAuthAdapter()
    response = _client().post(
        "/api/auth/local/dev-login",
        data={"state": "s", "email": "once@example.com", "name": ""},
    )
    code = parse_qs(urlparse(response.headers["location"]).query)["code"][0]

    await adapter.exchange_code(code=code)

    with pytest.raises(InvalidCodeError):
        await adapter.exchange_code(code=code)


class _Markup(HTMLParser):
    """Collects the page's shape -- the tags it opens -- and whatever the
    form carries as `state`, which is the only value the address decides.
    """

    def __init__(self) -> None:
        super().__init__()
        self.tags: list[str] = []
        self.state_values: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.tags.append(tag)
        attributes = dict(attrs)
        if attributes.get("name") == "state":
            self.state_values.append(attributes.get("value") or "")


def _parse(html: str) -> _Markup:
    parser = _Markup()
    parser.feed(html)
    return parser


async def test_a_state_with_markup_characters_reaches_the_page_as_text():
    """The address is what decides `state`, so a value written on purpose
    must not be able to close the attribute it lands in and add markup of
    its own (code-conventions spec, D6).
    """
    hostile = '"><script>alert("x")</script><input name="evil'

    page = _client().get("/api/auth/local/dev-login", params={"state": hostile}).text
    benign = _client().get("/api/auth/local/dev-login", params={"state": "plain"}).text

    parsed = _parse(page)
    assert parsed.state_values == [hostile], "the form no longer carries the state it received"
    assert parsed.tags == _parse(benign).tags, "the value added or closed an element"
    assert "<script>" not in page
