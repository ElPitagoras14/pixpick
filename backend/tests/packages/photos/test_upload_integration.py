"""End-to-end against the real storage, transformer and nginx (D9 in
add-media-ports-and-local-adapters' spirit, extended here): confirms that
warming a variant after a batch is confirmed actually leaves it in
nginx's own cache (task 4.3), not merely that the warm-up task didn't
raise. Requires `docker compose -f compose.dev.yaml up -d storage
transformer nginx` already running, the same expectation
`tests/storage/` and `tests/images/` already have.
"""

import base64

import httpx

from src.images.factory import image_port
from src.images.port import Variant
from src.packages.photos import service as photos_service
from src.packages.photos.warmup import warm_up_variants
from src.storage.factory import storage_port
from src.storage.port import object_key
from tests.factories import create_album, create_user

# A real, minimal, decodable 1x1 PNG -- imgproxy refuses to transform
# arbitrary bytes, unlike the fake storage double the rest of this
# package's tests use, which never looks at the content at all.
_ONE_PIXEL_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


async def test_confirming_a_batch_warms_the_rating_variant_in_the_real_edge_cache(
    committed_connection,
):
    user = await create_user(committed_connection)
    album = await create_album(committed_connection, owner_id=user.id)
    await committed_connection.commit()

    files = [
        photos_service.GrantFileInput(
            content_type="image/png", size=len(_ONE_PIXEL_PNG), width=1, height=1
        )
    ]
    result = await photos_service.grant_batch(
        committed_connection, album_id=album.id, owner_id=user.id, files=files
    )
    await committed_connection.commit()
    assert result.denied == []
    photo_id, grant = result.granted[0].photo_id, result.granted[0].grant
    key = object_key(album_id=str(album.id), photo_id=str(photo_id))

    try:
        # The real, direct-to-storage write a browser would perform
        # against the presigned grant (object-storage spec) -- never
        # through the API. A PUT with the file as the body (D9 in
        # add-cloud-media-adapters), with the signed headers sent
        # exactly as granted.
        upload_response = httpx.put(grant.url, content=_ONE_PIXEL_PNG, headers=grant.headers)
        assert upload_response.status_code < 300

        results, warm_up_keys = await photos_service.confirm_batch(
            album_id=album.id, user_id=user.id, photo_ids=[photo_id]
        )

        assert results[0].status == "available"
        assert warm_up_keys == [key]

        # The router schedules this as a background task after
        # responding (D7, task 4.5); awaited directly here since this
        # test only cares about nginx's cache afterward, not the
        # deferral itself.
        await warm_up_variants(warm_up_keys)

        variant_url = image_port.variant_url(object_key=key, variant=Variant.RATING)
        response = httpx.get(variant_url)
        assert response.status_code == 200
        assert response.headers["x-cache-status"] == "HIT"
    finally:
        # This test writes a real object to the real storage (unlike
        # the rest of this package's tests, which use the fake) -- it
        # cleans up after itself instead of leaving it behind.
        await storage_port.delete_objects(object_keys=[key])
