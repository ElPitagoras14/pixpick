"""Enforces the two code conventions no tool brings configured
(code-conventions spec): the form of an internal import, and the fact
that the markup the backend serves lives in a template rather than in a
literal.

The first one, in detail: a module living under the importing file's
(code-conventions spec, D1/D3): a module living under the importing file's
own package is imported relatively, so the form of an import follows
from where its target is and from nothing else. Ruff's TID252 covers the other
half -- a relative import never climbs to a parent -- so between the two
the rule stops depending on someone noticing it during review.

It lives in the suite rather than in a standalone script for the same
reason as the schema checks next to it: a script has to be remembered.
"""

import ast
from pathlib import Path

_BACKEND = Path(__file__).resolve().parents[1]
_SRC = _BACKEND / "src"
_ROOT_PACKAGE = _SRC.name


def _package_of(path: Path) -> str:
    """The package a file's relative imports resolve against: the dotted
    path of the directory holding it (for `__init__.py` too, since it *is*
    that package)."""
    return ".".join(path.relative_to(_BACKEND).parts[:-1])


def _absolute_imports_into_own_subtree(path: Path) -> list[tuple[int, str]]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    package = _package_of(path)
    offenders = []
    for node in ast.walk(tree):
        # `import src.x` is left out on purpose: it has no relative form,
        # so there is no other way to write it. Only `from ... import ...`
        # gets to choose, and only when it names a module of this project.
        if not isinstance(node, ast.ImportFrom) or node.level or node.module is None:
            continue
        module = node.module
        if module != _ROOT_PACKAGE and not module.startswith(f"{_ROOT_PACKAGE}."):
            continue
        # The package itself counts: `from src.packages.albums import
        # repository` written from inside that package reaches a sibling
        # module, which the rule says is relative.
        if module == package or module.startswith(f"{package}."):
            offenders.append((node.lineno, module))
    return offenders


def test_a_module_under_the_files_own_package_is_imported_relatively():
    offenders = [
        f"  {path.relative_to(_BACKEND).as_posix()}:{line}: from {module} import ..."
        for path in sorted(_SRC.rglob("*.py"))
        for line, module in _absolute_imports_into_own_subtree(path)
    ]
    assert not offenders, (
        "absolute imports whose target lives under the importing file's own "
        "package; write them relative instead:\n" + "\n".join(offenders)
    )


# Enough of a sample to catch a page coming back into the code: a literal
# holding any of these is markup, not a string that happens to have an
# angle bracket in it.
_MARKUP_MARKERS = ("<!doctype", "<html", "<body", "<form", "<script", "<div")


def _markup_literals(path: Path) -> list[tuple[int, str]]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    # Keyed by line: an f-string reports once, not twice, since its
    # literal halves are `Constant` nodes of their own as well.
    found: dict[int, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            lowered = node.value.lower()
            for marker in _MARKUP_MARKERS:
                if marker in lowered:
                    found.setdefault(node.lineno, marker)
                    break
        # An f-string is walked as its literal halves too, so joining them
        # is what catches markup that only reads as markup once assembled
        # -- the twenty-line page this rule exists for was exactly that.
        elif isinstance(node, ast.JoinedStr):
            text = "".join(
                part.value.lower()
                for part in node.values
                if isinstance(part, ast.Constant) and isinstance(part.value, str)
            )
            for marker in _MARKUP_MARKERS:
                if marker in text:
                    found.setdefault(node.lineno, marker)
                    break
    return sorted(found.items())


def test_the_markup_the_backend_serves_does_not_live_in_the_code():
    """A page's markup belongs in a template, where it has highlighting,
    a formatter, and escaping by construction (code-conventions spec, D5).
    """
    offenders = [
        f"  {path.relative_to(_BACKEND).as_posix()}:{line}: a literal holding {marker!r}"
        for path in sorted(_SRC.rglob("*.py"))
        for line, marker in _markup_literals(path)
    ]
    assert not offenders, "markup embedded in the code; move it to a template:\n" + "\n".join(
        offenders
    )
