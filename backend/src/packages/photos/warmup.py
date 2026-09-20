"""After a batch is confirmed, warm the rating variant's cache for every
photo that became available -- one deferred task per batch, never one per
photo, with bounded concurrency and a short timeout per request. A failure
here is logged and nothing else: it never reaches the client, and never
touches any photo's own state.
"""

import asyncio

import httpx

from src.images.factory import image_port
from src.images.port import Variant
from src.log import logger

WARMUP_CONCURRENCY = 5
WARMUP_TIMEOUT_SECONDS = 5.0


async def _warm_one(client: httpx.AsyncClient, semaphore: asyncio.Semaphore, key: str) -> None:
    # The address nginx's own cache is keyed by: requesting exactly this,
    # through the edge, is what a visitor's own request would look like.
    # Calling the transformer directly would produce the variant and discard
    # it, leaving the cache exactly as empty as before -- the mistake that
    # gives no symptom until someone measures a first view and it's still
    # slow.
    url = image_port.variant_url(object_key=key, variant=Variant.RATING)
    async with semaphore:
        try:
            response = await client.get(url, timeout=WARMUP_TIMEOUT_SECONDS)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            logger.opt(exception=exc).warning(f"failed to warm up the rating variant for {key!r}")


async def warm_up_variants(object_keys: list[str]) -> None:
    if not object_keys:
        return
    semaphore = asyncio.Semaphore(WARMUP_CONCURRENCY)
    async with httpx.AsyncClient() as client:
        await asyncio.gather(*(_warm_one(client, semaphore, key) for key in object_keys))
