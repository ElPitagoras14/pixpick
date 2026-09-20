"""Keeps the two declarations of the environment from drifting apart
(local-environment spec).

The project declares its environment twice: `compose.yaml` consumes
published images, `compose.dev.yaml` builds them from source, and neither
is ever combined with the other. That independence is the point, and the
price is that everything else -- the variables each service receives, the
addresses the services reach each other by, the healthchecks, the
dependencies, the volumes -- is written twice and can quietly stop
agreeing. Nothing fails visibly when it does: each file keeps working on
its own, saying something different.

So the rule is narrow enough to check: the two files differ in exactly two
things, where each image comes from and which ports reach the host. Every
other field must be equal, service for service.

It lives in the suite rather than in a standalone script for the same
reason as the schema checks next to it: a script has to be remembered.
"""

from pathlib import Path

import pytest
import yaml

_REPO_ROOT = Path(__file__).resolve().parents[2]
_PUBLISHED = _REPO_ROOT / "compose.yaml"
_BUILT = _REPO_ROOT / "compose.dev.yaml"

# The only two fields a service is allowed to declare differently. Every
# other key is compared verbatim.
_MAY_DIFFER = frozenset({"image", "build", "ports"})

# `migrate` alone may also differ on these two (harden-local-profile):
# compose.dev.yaml already assumes the repo is checked out to build the
# image from source, so it also bind-mounts dbmate/ and drops
# --no-dump-schema, regenerating dbmate/schema.sql as part of coming up.
# compose.yaml consumes the published image specifically so a deployment
# never needs the repo checked out, which that mount would defeat.
_MIGRATE_MAY_ALSO_DIFFER = frozenset({"volumes", "command"})


def _load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def published() -> dict:
    return _load(_PUBLISHED)


@pytest.fixture(scope="module")
def built() -> dict:
    return _load(_BUILT)


def test_both_declarations_hold_the_same_services(published, built):
    assert sorted(published["services"]) == sorted(built["services"]), (
        "the two declarations of the environment list different services; each one "
        "has to be able to bring up the whole environment on its own"
    )


def _disagreements(where: str, here, there) -> list[str]:
    """Narrows a difference down to the smallest thing that actually
    differs, so one changed variable reports as that variable instead of
    as two whole `environment` blocks."""
    if here == there:
        return []
    if isinstance(here, dict) and isinstance(there, dict):
        return [
            line
            for key in sorted(set(here) | set(there))
            for line in _disagreements(f"{where}.{key}", here.get(key), there.get(key))
        ]
    return [f"  {where}:\n    compose.yaml:     {here!r}\n    compose.dev.yaml: {there!r}"]


def test_every_field_but_the_image_and_the_ports_is_identical(published, built):
    offenders = []
    for name in sorted(set(published["services"]) & set(built["services"])):
        here, there = published["services"][name], built["services"][name]
        may_differ = _MAY_DIFFER | _MIGRATE_MAY_ALSO_DIFFER if name == "migrate" else _MAY_DIFFER
        for field in sorted((set(here) | set(there)) - may_differ):
            offenders += _disagreements(f"{name}.{field}", here.get(field), there.get(field))
    assert not offenders, (
        "the two declarations disagree on something other than the image and the "
        "published ports; whichever one is right, the other is serving a different "
        "environment:\n" + "\n".join(offenders)
    )


def test_a_service_is_either_pulled_or_built_in_each_declaration(published, built):
    offenders = []
    for name in sorted(set(published["services"]) & set(built["services"])):
        here, there = published["services"][name], built["services"][name]
        if "image" not in here:
            offenders.append(f"  {name}: compose.yaml declares no image to pull")
        if "image" not in there and "build" not in there:
            offenders.append(f"  {name}: compose.dev.yaml declares neither image nor build")
    assert not offenders, (
        "a service has no way to obtain its image in one of the declarations:\n"
        + "\n".join(offenders)
    )


def test_a_third_party_image_is_pinned_to_the_same_version_in_both(published, built):
    """A service the project doesn't build names the same image in both.
    Only the project's own four differ, and only because one file builds
    them."""
    offenders = []
    for name in sorted(set(published["services"]) & set(built["services"])):
        here, there = published["services"][name], built["services"][name]
        if "build" in there:
            continue
        if here.get("image") != there.get("image"):
            offenders.append(f"  {name}: {here.get('image')!r} vs {there.get('image')!r}")
    assert not offenders, (
        "a third-party image is pinned to different versions in the two declarations:\n"
        + "\n".join(offenders)
    )


def test_only_the_built_declaration_reaches_the_host(published, built):
    """`compose.yaml` publishes no port: whatever runs it puts its own
    proxy in front. The ports belong to the developer's machine."""
    exposed = [name for name, service in published["services"].items() if "ports" in service]
    assert not exposed, (
        "compose.yaml publishes ports to the host, which only the development "
        f"declaration does: {', '.join(sorted(exposed))}"
    )


def test_neither_declaration_gates_a_service_behind_a_profile(published, built):
    """Which provider the application talks to is decided by its own
    variables, never by which services are declared, so a service is
    declared in both whether or not a given configuration queries it."""
    offenders = [
        f"  {path.name}: {name}"
        for path, document in ((_PUBLISHED, published), (_BUILT, built))
        for name, service in document["services"].items()
        if "profiles" in service
    ]
    assert not offenders, (
        "a service is gated behind a compose profile; declare it always instead:\n"
        + "\n".join(offenders)
    )


def test_the_networks_and_volumes_are_the_same(published, built):
    for section in ("networks", "volumes"):
        assert sorted(published.get(section) or {}) == sorted(built.get(section) or {}), (
            f"the two declarations define different {section}; a service moved between "
            "them would land somewhere else depending on which file was used"
        )


def test_every_service_declares_a_memory_ceiling_and_a_restart_policy(published, built):
    """Task 6.3 (local-environment spec): every service says on its own
    how much memory it can take and what happens if it ends unexpectedly,
    instead of some of them being left at whatever the runtime defaults
    to."""
    offenders = []
    for path, document in ((_PUBLISHED, published), (_BUILT, built)):
        for name, service in document["services"].items():
            if "mem_limit" not in service:
                offenders.append(f"  {path.name}: {name} declares no mem_limit")
            if "restart" not in service:
                offenders.append(f"  {path.name}: {name} declares no restart policy")
    assert not offenders, (
        "a service is missing a resource ceiling or a restart policy:\n" + "\n".join(offenders)
    )
