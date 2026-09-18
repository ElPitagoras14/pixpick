"""D2 in album-retention's design: every read of `albums` across the
backend composes the one condition `albums.repository.ACTIVE_CONDITION`
defines, instead of writing its own. A view can't hold this the way
`available_photos` holds photos' availability -- the plazo is a runtime
setting, and a view takes no parameters -- so this scan is the
guarantee a later query can't quietly skip it (task 2.2).
"""

import ast
import re
from pathlib import Path

_BACKEND = Path(__file__).resolve().parents[1]
_SRC = _BACKEND / "src"

# A read of `albums`: the table named after `from` or `join`. A plain
# `delete from albums ...` also contains the substring "from albums",
# but it isn't a read this rule cares about -- see `_is_a_read` below.
_READS_ALBUMS = re.compile(r"\b(?:from|join)\s+albums\b", re.IGNORECASE)
_HAS_SELECT = re.compile(r"\bselect\b", re.IGNORECASE)
# The condition's own name has to appear as the *expression* an
# f-string interpolates, not as literal text -- the SQL it expands to
# only exists at runtime. `ast.unparse` on each `{...}` part's
# expression recovers that name from the source (see `_string_literals`).
_HAS_CONDITION = re.compile(r"\bACTIVE_CONDITION\b")


def _is_a_read(text: str) -> bool:
    """Only a query that actually selects rows counts: a bare `delete
    from albums where id = ... and owner_id = ...` names no row this
    query didn't already pin down by id, and carries no `select` at
    all, so it is excluded on purpose -- see the module docstring.
    """
    return bool(_HAS_SELECT.search(text) and _READS_ALBUMS.search(text))


class _LiteralCollector(ast.NodeVisitor):
    """Collects each string literal exactly once, as the query it
    actually reads as. Plain `ast.walk` would visit an f-string's own
    `Constant` fragments a second time, on their own -- each missing
    the `{ACTIVE_CONDITION}` part that completes it -- so this instead
    stops at `JoinedStr` and never calls `generic_visit` on it.
    """

    def __init__(self) -> None:
        self.literals: list[tuple[int, str]] = []

    def visit_Constant(self, node: ast.Constant) -> None:
        if isinstance(node.value, str):
            self.literals.append((node.lineno, node.value))

    def visit_JoinedStr(self, node: ast.JoinedStr) -> None:
        # Each `{expr}` part becomes its own source text --
        # `{ACTIVE_CONDITION}` becomes the word "ACTIVE_CONDITION" --
        # rather than being dropped, which is what would let a query
        # that composes the condition read as if it didn't.
        joined = "".join(
            part.value
            if isinstance(part, ast.Constant) and isinstance(part.value, str)
            else ast.unparse(part.value)
            for part in node.values
        )
        self.literals.append((node.lineno, joined))


def _string_literals(path: Path) -> list[tuple[int, str]]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    collector = _LiteralCollector()
    collector.visit(tree)
    return collector.literals


def _offending_queries(path: Path) -> list[tuple[int, str]]:
    offenders = []
    for lineno, text in _string_literals(path):
        if not _is_a_read(text) or _HAS_CONDITION.search(text):
            continue
        first_line = next((line for line in text.strip().splitlines() if line.strip()), text)
        offenders.append((lineno, first_line.strip()[:80]))
    return offenders


def test_every_read_of_albums_composes_the_retention_condition():
    offenders = [
        f"  {path.relative_to(_BACKEND).as_posix()}:{lineno}: {snippet}"
        for path in sorted(_SRC.rglob("*.py"))
        for lineno, snippet in _offending_queries(path)
    ]
    assert not offenders, (
        "a query reads the albums table without composing "
        "albums.repository.ACTIVE_CONDITION (album-retention design, D2):\n" + "\n".join(offenders)
    )
