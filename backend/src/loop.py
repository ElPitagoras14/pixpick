"""Makes psycopg3's async mode work under asyncio on Windows.

psycopg3 cannot run on `ProactorEventLoop`, which is Windows's default
policy. Every other platform already gets a compatible loop and needs
nothing from here.

Two ways in, for two moments:

- `loop_factory`, handed to whoever creates the loop for this process
  (`main.py`, `reconcile.py`). It has to be the callable itself: the loop
  is created before any of this app's own code would run, so a dotted
  path resolved later never reaches it.
- `ensure_compatible_event_loop_policy()`, which sets the process-wide
  policy instead, for a caller that creates its loop later --
  `tests/conftest.py`, ahead of pytest-asyncio.
"""

import asyncio
import sys


def loop_factory(use_subprocess: bool = False) -> asyncio.AbstractEventLoop:
    if sys.platform == "win32":
        return asyncio.SelectorEventLoop()

    from uvicorn.loops.auto import auto_loop_factory

    return auto_loop_factory(use_subprocess=use_subprocess)()


def ensure_compatible_event_loop_policy() -> None:
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
