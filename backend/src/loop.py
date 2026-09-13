"""Makes psycopg3's async mode work under asyncio on Windows.

psycopg3's async mode cannot run on asyncio's `ProactorEventLoop`, which
is the default event loop policy on Windows (there's no `uvloop` for that
platform to override it with, unlike every other OS, which already gets
a compatible loop from its own default policy and needs nothing from
this module).

Two ways to get a compatible loop, for two different situations:

- `loop_factory`: a callable that returns one, passed directly to
  whoever creates the loop *for* this process -- `main.py`'s own
  `uvicorn.run(..., loop=loop_factory)` (see its `if __name__ ==
  "__main__":` block) and `reconcile.py`'s own `asyncio.run(...,
  loop_factory=loop_factory)`. Passed as the actual callable, not a
  dotted path for uvicorn to resolve on its own: uvicorn (like
  `asyncio.run`) creates its loop *before* this app's own code would
  otherwise get a chance to run, so only a factory the caller already
  has in hand at that point -- never something this app's own import-time
  code sets up for uvicorn to discover later -- can reach it.
- `ensure_compatible_event_loop_policy()`: sets the *process-wide* event
  loop policy instead, for a caller that only creates its loop later,
  well after calling this -- `tests/conftest.py`, ahead of pytest-asyncio
  creating its own loop through whatever policy is current by then.
"""

import asyncio
import sys


def loop_factory(use_subprocess: bool = False) -> asyncio.AbstractEventLoop:
    # uvicorn only double-indirects (factory-of-factory) for its own
    # built-in --loop names; a custom dotted path like this one is called
    # once and must return a ready event loop instance, not a class.
    if sys.platform == "win32":
        return asyncio.SelectorEventLoop()

    from uvicorn.loops.auto import auto_loop_factory

    return auto_loop_factory(use_subprocess=use_subprocess)()


def ensure_compatible_event_loop_policy() -> None:
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
