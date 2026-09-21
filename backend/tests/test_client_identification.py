"""Real stack only: requires `docker compose -f compose.dev.yaml up -d
--build` already running, with the network's fixed subnet and `ip_range`
from that file. Exercised against the containers themselves, not through
Python, because what is under test is nginx's own `set_real_ip_from` and
uvicorn's own `forwarded_allow_ips` -- neither is reachable by importing
this project's code.
"""

import re
import subprocess
import uuid

import httpx

_COMPOSE = ["docker", "compose", "-f", "compose.dev.yaml"]


def _nginx_log_tail(lines: int = 50) -> str:
    result = subprocess.run(
        [*_COMPOSE, "logs", "pixpick-nginx", "--no-color", "--tail", str(lines)],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


def _backend_log_tail(lines: int = 50) -> str:
    result = subprocess.run(
        [*_COMPOSE, "logs", "pixpick-backend", "--no-color", "--tail", str(lines)],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


def _address_logging_for(log_text: str, marker: str) -> str | None:
    """The address nginx/uvicorn's own access log attributes to the
    request carrying `marker` in its path -- the first token of whichever
    line mentions it, which is where both log formats put the address."""
    for line in log_text.splitlines():
        if marker in line:
            match = re.search(r"(\d{1,3}(?:\.\d{1,3}){3})", line)
            return match.group(1) if match else None
    return None


async def test_a_forged_header_from_outside_the_network_is_ignored(running_stack):
    """A request that never went through the platform's own proxy -- here,
    one that reaches nginx through compose.dev.yaml's own published port,
    which arrives as the network's gateway address, kept out of the trusted
    `ip_range` on purpose -- has its own X-Forwarded-For ignored by both
    nginx and the backend behind it.
    """
    marker = f"probe-{uuid.uuid4().hex}"
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"http://127.0.0.1:8080/api/health?{marker}=1",
            headers={"X-Forwarded-For": "6.6.6.6"},
        )
    assert response.status_code == 200

    nginx_address = _address_logging_for(_nginx_log_tail(), marker)
    backend_address = _address_logging_for(_backend_log_tail(), marker)
    assert nginx_address is not None and nginx_address != "6.6.6.6"
    assert backend_address is not None and backend_address != "6.6.6.6"


async def test_a_declared_address_from_inside_the_network_is_trusted(running_stack):
    """A request that does arrive from the trusted
    `ip_range` -- simulated here from the backend container itself,
    itself a member of it, standing in for the platform's own proxy --
    has the address it declares recorded by both nginx and the backend,
    instead of the connecting peer's own.
    """
    marker = f"probe-{uuid.uuid4().hex}"
    script = (
        "import httpx;"
        f"httpx.get('http://pixpick-nginx/api/health?{marker}=1', "
        "headers={'X-Forwarded-For': '9.9.9.9'})"
    )
    subprocess.run(
        [*_COMPOSE, "exec", "-T", "pixpick-backend", "python", "-c", script],
        capture_output=True,
        text=True,
        check=True,
    )

    nginx_address = _address_logging_for(_nginx_log_tail(), marker)
    backend_address = _address_logging_for(_backend_log_tail(), marker)
    assert nginx_address == "9.9.9.9"
    assert backend_address == "9.9.9.9"
