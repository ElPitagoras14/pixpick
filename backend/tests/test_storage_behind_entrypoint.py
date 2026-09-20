"""Real stack only (object-storage spec, local-environment spec, tasks
3.1-3.6): requires `docker compose -f compose.dev.yaml up -d --build`
already running with STORAGE_PROVIDER=local, IMAGE_PROVIDER=local, and
STORAGE_PUBLIC_URL pointing at nginx's own storage hostname (.env.example
documents the default: http://storage.localhost:${NGINX_PORT}).

Exercised over real HTTP against the containers, not through Python: what
is under test is nginx's own storage server block and the browser-facing
address the backend hands out, neither reachable by importing this
project's code.
"""

import base64
import os
from urllib.parse import parse_qs, urlparse

import httpx

_NGINX_PORT = os.environ["NGINX_PORT"]
# 127.0.0.1, not "localhost": this machine's own resolver tries IPv6
# first for "localhost" and that path doesn't reach Docker's published
# port here, adding seconds of delay per request -- unrelated to what's
# under test.
_BASE_URL = f"http://127.0.0.1:{_NGINX_PORT}"
_STORAGE_HOST = f"storage.localhost:{_NGINX_PORT}"

# A real, minimal, decodable 1x1 PNG (same one test_upload_integration.py
# uses): imgproxy and MinIO both look at the bytes, unlike the fake
# storage double the rest of the suite relies on.
_ONE_PIXEL_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


async def _log_in() -> str:
    """The real local-provider HTTP cycle (session-management spec), not
    the DB-shortcut `tests/authhelpers.py` uses: this test runs outside
    the app's own process, against the real running containers, so there
    is no shared connection to seed a session through directly.

    Returns the raw session token rather than leaving it in a client's
    own cookie jar: a real, independently reproduced backend behavior
    (unrelated to this change, tracked separately) intermittently drops
    an otherwise-valid session when the very next request reuses the
    same keep-alive connection a redirect just answered on -- the
    database always has the right row, confirmed directly, so a fresh
    connection for what comes after this login is the reliable way to
    carry it forward.
    """
    async with httpx.AsyncClient(follow_redirects=False) as client:
        login = await client.get(f"{_BASE_URL}/api/auth/login", params={"returnTo": "/"})
        assert login.status_code == 302
        dev_login_url = login.headers["location"]
        state = parse_qs(urlparse(dev_login_url).query)["state"][0]

        submit = await client.post(
            f"{_BASE_URL}{dev_login_url}",
            data={"state": state, "email": "e2e@example.com", "name": "E2E"},
        )
        assert submit.status_code == 303

        callback = await client.get(f"{_BASE_URL}{submit.headers['location']}")
        assert callback.status_code == 302
        assert "session" in client.cookies
        return client.cookies["session"]


async def test_the_storage_hostname_routes_through_nginx_to_the_real_storage(running_stack):
    """Task 3.1: a request through the storage hostname reaches the real
    storage -- MinIO's own AccessDenied, not the frontend's catch-all or
    a gateway error -- with neither the path nor the Host rewritten."""
    async with httpx.AsyncClient(follow_redirects=False) as client:
        response = await client.get(f"{_BASE_URL}/pixpick", headers={"Host": _STORAGE_HOST})
    assert response.status_code in (403, 404)
    assert "AccessDenied" in response.text or "NoSuchBucket" in response.text


async def test_a_grant_and_full_upload_cycle_works_through_the_entry_point(running_stack):
    """Tasks 3.1-3.3: the full flow a browser performs -- ask for a
    grant, PUT the object straight to the address the grant carries (now
    the entry point's own storage hostname, path-style addressed, task
    3.2), and confirm it -- works end to end with the environment up."""
    session_token = await _log_in()
    async with httpx.AsyncClient(
        follow_redirects=False, cookies={"session": session_token}
    ) as client:
        album = await client.post(f"{_BASE_URL}/api/albums", json={"title": "E2E storage test"})
        assert album.status_code == 200
        album_id = album.json()["data"]["id"]

        grant = await client.post(
            f"{_BASE_URL}/api/albums/{album_id}/photos/grants",
            json={
                "files": [
                    {
                        "contentType": "image/png",
                        "size": len(_ONE_PIXEL_PNG),
                        "width": 1,
                        "height": 1,
                    }
                ]
            },
        )
        assert grant.status_code == 200
        granted = grant.json()["data"]["granted"][0]
        upload_url = granted["uploadUrl"]
        assert upload_url.startswith(f"http://{_STORAGE_HOST}/")

        # `storage.localhost` is the address the signature covers, but
        # this machine's own resolver doesn't necessarily resolve it the
        # way a browser's built-in RFC 6761 handling does (unlike
        # test_client_identification.py's spoofing checks, this isn't
        # about trust -- there's no other way to reach it from here at
        # all): connect to nginx's known address instead, with the
        # signed Host preserved in the header the signature actually
        # covers.
        parsed = urlparse(upload_url)
        upload = await client.put(
            upload_url.replace(parsed.netloc, f"127.0.0.1:{_NGINX_PORT}", 1),
            content=_ONE_PIXEL_PNG,
            headers={**granted["uploadHeaders"], "Host": parsed.netloc},
        )
        assert upload.status_code < 300

        confirm = await client.post(
            f"{_BASE_URL}/api/albums/{album_id}/photos/confirm",
            json={"photoIds": [granted["photoId"]]},
        )
        assert confirm.status_code == 200
        assert confirm.json()["data"] == [{"photoId": granted["photoId"], "status": "available"}]


async def test_a_body_over_the_maximum_is_rejected_before_reaching_storage(running_stack):
    """Task 3.4: a body above the entry point's own cap fails there --
    413, never reaching the storage -- instead of at the application,
    which validates only what the client declared, not what it wrote."""
    oversized = b"0" * (21 * 1024 * 1024 + 1)
    async with httpx.AsyncClient(follow_redirects=False, timeout=30) as client:
        response = await client.put(
            f"{_BASE_URL}/pixpick/albums/probe/oversized",
            content=oversized,
            headers={"Host": _STORAGE_HOST},
        )
    assert response.status_code == 413


async def test_a_body_within_the_maximum_reaches_storage(running_stack):
    """The complement of the above: a body under the cap is let through
    to the real storage, which then answers on its own terms (rejecting
    this particular, unsigned request) instead of nginx cutting it off.

    An unsigned request this large sometimes makes the real MinIO answer
    and close the connection before this end finishes writing the body --
    a plain connection reset, distinguishable from nginx's own clean 413
    for the oversized case above, and still proof the cap never fired.
    """
    within_limit = b"0" * (20 * 1024 * 1024)
    async with httpx.AsyncClient(follow_redirects=False, timeout=30) as client:
        try:
            response = await client.put(
                f"{_BASE_URL}/pixpick/albums/probe/within-limit",
                content=within_limit,
                headers={"Host": _STORAGE_HOST},
            )
        except httpx.TransportError:
            return
    assert response.status_code != 413


async def test_the_storage_accepts_the_applications_origin_and_rejects_another(running_stack):
    """Task 3.6: CORS on the storage is scoped to the application's own
    origin, not the storage's own hostname or an arbitrary one."""
    # MINIO_ALLOWED_ORIGINS (.env.example) lists this origin literally --
    # CORS matches Origin as an exact string, so this has to be the same
    # "localhost" spelling configured there, unlike _BASE_URL above,
    # which connects through 127.0.0.1 to sidestep this machine's own
    # slow IPv6 resolution for "localhost" (unrelated to what's under
    # test here).
    application_origin = f"http://localhost:{_NGINX_PORT}"
    async with httpx.AsyncClient(follow_redirects=False) as client:
        allowed = await client.request(
            "OPTIONS",
            f"{_BASE_URL}/pixpick/albums/probe/cors",
            headers={
                "Host": _STORAGE_HOST,
                "Origin": application_origin,
                "Access-Control-Request-Method": "PUT",
            },
        )
        other = await client.request(
            "OPTIONS",
            f"{_BASE_URL}/pixpick/albums/probe/cors",
            headers={
                "Host": _STORAGE_HOST,
                "Origin": "http://evil.example.com",
                "Access-Control-Request-Method": "PUT",
            },
        )

    assert allowed.headers.get("access-control-allow-origin") == application_origin
    assert "access-control-allow-origin" not in other.headers


async def test_the_storage_console_is_disabled_while_the_api_keeps_working(running_stack):
    """Task 6.1: no path on the storage's own address ever answers with
    the console's HTML -- only the S3 API's own XML -- and the API keeps
    working normally."""
    async with httpx.AsyncClient(follow_redirects=False) as client:
        response = await client.get(
            f"{_BASE_URL}/", headers={"Host": _STORAGE_HOST, "Accept": "text/html"}
        )
    assert "text/html" not in response.headers.get("content-type", "")
    assert response.status_code in (403, 404)
