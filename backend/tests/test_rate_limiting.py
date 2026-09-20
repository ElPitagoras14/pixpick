"""Real stack only: requires `docker compose -f compose.dev.yaml up -d
--build` already running. The limits are fixed in nginx/nginx.conf.template,
not configurable: 600 requests/minute general (burst 50), 30 requests/minute
for grants (burst 5).

Exercised over real concurrent HTTP against nginx, not through Python: what
is under test is nginx's own `limit_req` zones and the JSON body it answers
with by itself, neither reachable by importing this project's code.
"""

import asyncio
import os

import httpx

_NGINX_PORT = os.environ["NGINX_PORT"]
_BASE_URL = f"http://127.0.0.1:{_NGINX_PORT}"


async def _burst(path: str, count: int, *, method: str = "GET") -> list[httpx.Response]:
    async with httpx.AsyncClient(timeout=30) as client:
        return await asyncio.gather(
            *(client.request(method, f"{_BASE_URL}{path}") for _ in range(count))
        )


async def test_a_normal_pace_is_never_rejected(running_stack):
    """Scenario: a client below the ceiling is unaffected."""
    responses = await _burst("/api/health", 5)
    assert all(r.status_code == 200 for r in responses)


async def test_the_grants_endpoint_has_its_own_stricter_ceiling(running_stack):
    """Granting exhausts its own, stricter zone well before the general one,
    and doing so never blocks a different operation from the same client --
    the two zones count separately.

    Ordered before the general-ceiling test below on purpose: every test in
    this file shares one real client address (this machine's), so a burst
    that deliberately exhausts the *general* zone would leave it without the
    budget this test also needs, for as long as the zone takes to refill
    (the zones refill as token buckets) -- exhausting only
    the *grants* zone here does not.
    """
    grants_path = "/api/albums/00000000-0000-0000-0000-000000000000/photos/grants"
    grants_responses = await _burst(grants_path, 40, method="POST")
    assert any(r.status_code == 429 for r in grants_responses)
    # Some non-429 responses got through (401, unauthenticated) before the
    # stricter budget ran out -- proof this zone was actually exercised,
    # not the general one answering for it.
    assert any(r.status_code != 429 for r in grants_responses)

    other_responses = await _burst("/api/health", 5)
    assert all(r.status_code == 200 for r in other_responses)


async def test_a_burst_over_the_general_ceiling_is_rejected_with_the_common_body(running_stack):
    """A burst past the general zone's own budget gets
    some 429s, each in the API's own envelope shape, distinguishable from
    a validation failure (no field) and carrying a retry-after both as
    the header and inside the body. Runs last (see the previous test's
    own docstring): this is the one that deliberately exhausts the
    general zone for whichever real address is making the request.
    """
    responses = await _burst("/api/health", 200)
    rejected = [r for r in responses if r.status_code == 429]
    assert rejected, "expected at least one rejection from a burst this size"

    body = rejected[0].json()
    assert body["data"] is None
    assert body["error"]["code"] == "rate_limited"
    assert body["error"]["field"] is None
    assert body["error"]["retryAfterSeconds"] > 0
    assert rejected[0].headers["retry-after"] == str(body["error"]["retryAfterSeconds"])
