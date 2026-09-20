from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncConnection

from src.database.utils import transaction
from src.exceptions import NotFoundError, ValidationFailedError
from src.packages.albums import repository as albums_repository
from src.packages.albums import service as albums_service
from src.packages.auth import repository as auth_repository
from src.packages.quota import repository as quota_repository
from src.storage.factory import storage_port
from src.storage.port import object_key

from . import repository
from .config import (
    ALLOWED_CONTENT_TYPES,
    MAX_FILE_SIZE,
    UPLOAD_GRANT_TTL,
    photos_settings,
)
from .schemas import (
    AvailablePhotoRow,
    ConfirmationOutcome,
    DeniedFile,
    GalleryCounts,
    GalleryResult,
    GrantBatchResult,
    GrantedFile,
    GrantFileInput,
    RatingFilter,
)


def _validate_files(files: list[GrantFileInput]) -> None:
    """A rejection here means the client's own filtering missed something:
    it already knows every file's type and size before asking."""
    for index, file in enumerate(files):
        if file.content_type not in ALLOWED_CONTENT_TYPES:
            raise ValidationFailedError(
                field=f"files.{index}.contentType",
                message=f"content type {file.content_type!r} is not allowed",
            )
        # A non-positive size would grow what's available instead of
        # consuming it. Checked here as well as in the router's schema, for
        # a caller that reaches this directly.
        if file.size <= 0:
            raise ValidationFailedError(
                field=f"files.{index}.size", message="size must be a positive number of bytes"
            )
        if file.size > MAX_FILE_SIZE:
            raise ValidationFailedError(
                field=f"files.{index}.size",
                message=f"file exceeds the maximum size of {MAX_FILE_SIZE} bytes",
            )


async def grant_batch(
    connection: AsyncConnection, *, album_id: UUID, owner_id: UUID, files: list[GrantFileInput]
) -> GrantBatchResult:
    """Grants what fits and explains what does not. A file needs room in all
    three limits -- the album's photo count, the owner's storage and the
    instance's -- and running out of any of them is a fact about state, not
    a mistake in the request, so the batch is never rejected whole. An
    inadmissible file, checked above, still is."""
    _validate_files(files)

    # Global, not the owner's row: the instance limit spans every account,
    # so two owners' batches have to serialize against each other too. This
    # also covers the position and occupancy counting below.
    await quota_repository.acquire_instance_lock(connection)
    # A session from an account deleted after it signed in gets
    # `NotFoundError` here.
    if not await auth_repository.user_exists(connection, user_id=owner_id):
        raise NotFoundError()

    album = await albums_repository.get_owned_album(
        connection, album_id=album_id, owner_id=owner_id
    )
    if album is None:
        raise NotFoundError()

    occupied = await repository.count_occupied_slots(connection, album_id=album_id)
    used_bytes = await quota_repository.account_used_bytes(connection, owner_id=owner_id)
    instance_used_bytes = await quota_repository.instance_used_bytes(connection)
    remaining_photos = max(photos_settings.album_max_photos - occupied, 0)
    remaining_bytes = max(photos_settings.account_max_bytes - used_bytes, 0)
    remaining_instance_bytes = max(photos_settings.instance_max_bytes - instance_used_bytes, 0)

    base_position = await repository.next_position(connection, album_id=album_id)
    expires_at = datetime.now(UTC) + UPLOAD_GRANT_TTL

    granted: list[GrantedFile] = []
    denied: list[DeniedFile] = []
    rows: list[dict] = []
    for index, file in enumerate(files):
        # First: a full album is full for every file left, so nothing is
        # gained by skipping ahead the way the two size limits do.
        if remaining_photos <= 0:
            denied.append(DeniedFile(index=index, reason="album_full", remaining_photos=0))
            continue
        if file.size > remaining_bytes:
            # Skipped, not stopped on: a smaller file further down may still
            # fit, and the order they were picked in shouldn't decide that.
            denied.append(
                DeniedFile(index=index, reason="account_full", remaining_bytes=remaining_bytes)
            )
            continue
        if file.size > remaining_instance_bytes:
            # After the account, so that when both are full the reason that
            # comes back is the one whoever is asking can act on.
            denied.append(
                DeniedFile(
                    index=index, reason="instance_full", remaining_bytes=remaining_instance_bytes
                )
            )
            continue

        photo_id = uuid4()
        position = base_position + len(granted)
        grant = storage_port.grant_upload(
            album_id=str(album_id),
            photo_id=str(photo_id),
            content_type=file.content_type,
            ttl_seconds=int(UPLOAD_GRANT_TTL.total_seconds()),
        )
        rows.append(
            {
                "id": photo_id,
                "album_id": album_id,
                "position": position,
                "declared_content_type": file.content_type,
                "declared_size": file.size,
                "width": file.width,
                "height": file.height,
                "upload_expires_at": expires_at,
            }
        )
        granted.append(GrantedFile(index=index, photo_id=photo_id, position=position, grant=grant))
        # Charged as the walk goes, so a batch can't outgrow a limit against
        # itself: a file occupies its slot from the moment it is granted.
        remaining_photos -= 1
        remaining_bytes -= file.size
        remaining_instance_bytes -= file.size

    if rows:
        await repository.insert_pending_photos(connection, rows)
    return GrantBatchResult(granted=granted, denied=denied)


async def list_photos(connection: AsyncConnection, *, album_id: UUID) -> list[AvailablePhotoRow]:
    return await repository.list_available_photos(connection, album_id=album_id)


async def get_gallery(
    connection: AsyncConnection, *, album_id: UUID, user_id: UUID, rating_filter: RatingFilter
) -> GalleryResult:
    """One pass, whatever the filter: the slice and the four counts come
    from the same rows, so they can never disagree."""
    rows = await repository.list_photos_with_rating(
        connection, album_id=album_id, user_id=user_id, rating_filter="all"
    )
    approved = [row for row in rows if row.approved is True]
    rejected = [row for row in rows if row.approved is False]
    unrated = [row for row in rows if row.approved is None]
    counts = GalleryCounts(
        total=len(rows), approved=len(approved), rejected=len(rejected), unrated=len(unrated)
    )
    selected = {"all": rows, "approved": approved, "rejected": rejected, "unrated": unrated}[
        rating_filter
    ]
    return GalleryResult(photos=selected, counts=counts)


async def confirm_batch(
    *, album_id: UUID, user_id: UUID, photo_ids: list[UUID]
) -> tuple[list[ConfirmationOutcome], list[str]]:
    """Verifies each photo against its real object, never against what the
    client declared. Each photo's write commits on its own, so no
    transaction is ever held open across a wait on storage."""
    async with transaction() as connection:
        # Owner-only, checked here rather than with `Depends(get_owned_album)`
        # at the router, because the rest of this runs outside a transaction.
        await albums_service.require_owned_album(connection, album_id=album_id, user_id=user_id)
        photos = await repository.get_owned_photos(
            connection, album_id=album_id, owner_id=user_id, photo_ids=photo_ids
        )
    assert photos is not None

    results: list[ConfirmationOutcome] = []
    warm_up_keys: list[str] = []
    rejected_keys: list[str] = []

    for photo in photos:
        if photo.available:
            # Reconfirming is inert and needs no call to storage at all.
            results.append(ConfirmationOutcome(photo_id=photo.id, status="available"))
            continue

        key = object_key(album_id=str(photo.album_id), photo_id=str(photo.id))
        metadata = await storage_port.get_object(object_key=key)

        if metadata is None:
            results.append(ConfirmationOutcome(photo_id=photo.id, status="pending"))
            continue

        mismatched = (
            metadata.size != photo.declared_size
            or metadata.content_type != photo.declared_content_type
        )
        if mismatched:
            results.append(ConfirmationOutcome(photo_id=photo.id, status="rejected"))
            rejected_keys.append(key)
            continue

        async with transaction() as connection:
            await repository.mark_photo_available(connection, photo_id=photo.id, size=metadata.size)
            # Same transaction as the one that makes the photo available, so
            # a confirmation that rolls back never moves the window either.
            await albums_repository.touch_renewed_at(connection, album_id=photo.album_id)
        results.append(ConfirmationOutcome(photo_id=photo.id, status="available"))
        warm_up_keys.append(key)

    if rejected_keys:
        await storage_port.delete_objects(object_keys=rejected_keys)

    return results, warm_up_keys


async def delete_photo(*, album_id: UUID, user_id: UUID, photo_id: UUID) -> None:
    """Its own transaction, committed before anything talks to storage, and
    owner-only checked here -- the same shape as `confirm_batch`."""
    async with transaction() as connection:
        await albums_service.require_owned_album(connection, album_id=album_id, user_id=user_id)
        deleted = await repository.delete_owned_photo(
            connection, album_id=album_id, owner_id=user_id, photo_id=photo_id
        )
    if not deleted:
        raise NotFoundError()
    key = object_key(album_id=str(album_id), photo_id=str(photo_id))
    await storage_port.delete_objects(object_keys=[key])
