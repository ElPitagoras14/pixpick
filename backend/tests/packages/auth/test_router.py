from urllib.parse import parse_qs, urlparse


def _extract_state(location: str) -> str:
    return parse_qs(urlparse(location).query)["state"][0]


def test_login_sets_short_lived_cookies_and_redirects_to_the_provider(client):
    response = client.get("/api/auth/login", params={"return_to": "/albums/42"})

    assert response.status_code == 302
    location = response.headers["location"]
    assert location.startswith("/api/auth/local/dev-login")
    assert "auth_state" in client.cookies
    assert "auth_return_to" in client.cookies


def test_callback_without_a_state_cookie_is_rejected(client):
    response = client.get("/api/auth/callback", params={"state": "anything", "code": "anything"})

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_state"
    assert "session" not in client.cookies


def test_callback_with_a_mismatched_state_is_rejected(client):
    client.get("/api/auth/login", params={"return_to": "/"})

    response = client.get("/api/auth/callback", params={"state": "not-the-real-state", "code": "x"})

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_state"
    assert "session" not in client.cookies


def test_the_full_cycle_establishes_a_session_and_honors_return_to(client):
    login_response = client.get("/api/auth/login", params={"return_to": "/albums/42"})
    state = _extract_state(login_response.headers["location"])

    dev_login_response = client.post(
        "/api/auth/local/dev-login",
        data={"state": state, "email": "person@example.com", "name": "Person"},
    )
    assert dev_login_response.status_code == 303

    callback_response = client.get(dev_login_response.headers["location"])
    assert callback_response.status_code == 302
    assert callback_response.headers["location"].endswith("/albums/42")
    assert "session" in client.cookies
    # The one-time cookies are gone once the cycle completes.
    assert client.cookies.get("auth_state") is None
    assert client.cookies.get("auth_return_to") is None

    me_response = client.get("/api/auth/me")
    assert me_response.status_code == 200
    me_body = me_response.json()["data"]
    assert me_body["email"] == "person@example.com"
    assert "sessionId" not in me_body
    assert "sessionHash" not in me_body

    logout_response = client.post("/api/auth/logout")
    assert logout_response.status_code == 200
    assert logout_response.json() == {"data": None, "error": None}

    after_logout = client.get("/api/auth/me")
    assert after_logout.status_code == 401


def test_without_a_saved_destination_login_ends_at_the_default(client):
    login_response = client.get("/api/auth/login")
    state = _extract_state(login_response.headers["location"])

    dev_login_response = client.post(
        "/api/auth/local/dev-login",
        data={"state": state, "email": "nobody@example.com", "name": ""},
    )
    callback_response = client.get(dev_login_response.headers["location"])

    assert callback_response.headers["location"].endswith("/home")


def test_me_without_a_session_is_unauthenticated(client):
    response = client.get("/api/auth/me")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthenticated"


def test_logout_is_a_write_and_does_not_respond_to_a_read(client):
    """With SameSite=Lax cookies, a GET could be triggered by another site;
    only an explicit method that isn't a plain read reaches this endpoint at
    all."""
    response = client.get("/api/auth/logout")
    assert response.status_code == 405


def test_the_final_redirect_uses_the_configured_scheme_not_the_requests(client, monkeypatch):
    monkeypatch.setattr("src.packages.auth.router.settings.public_url", "https://pixpick.example")

    login_response = client.get("/api/auth/login", params={"return_to": "/gallery"})
    state = _extract_state(login_response.headers["location"])
    dev_login_response = client.post(
        "/api/auth/local/dev-login",
        data={"state": state, "email": "scheme@example.com", "name": ""},
    )

    callback_response = client.get(dev_login_response.headers["location"])

    assert callback_response.headers["location"] == "https://pixpick.example/gallery"
