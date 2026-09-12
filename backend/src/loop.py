"""Custom event loop factory for uvicorn.

psycopg3's async mode cannot run on asyncio's `ProactorEventLoop`, which is
what uvicorn's "auto" loop setup picks on Windows (there is no `uvloop` for
that platform). On every other platform, `uvloop` is what "auto" already
picks, so this only overrides the loop on Windows and otherwise defers to
uvicorn's own selection -- native mode doesn't lose uvloop on Linux/macOS to
fix a problem that's Windows-only.

Wired in via uvicorn's `--loop` flag (see backend/Dockerfile, compose.dev.yaml,
and README.md) instead of `fastapi run`/`fastapi dev`, which do not expose it.
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
