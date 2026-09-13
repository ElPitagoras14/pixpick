from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncConnection

from src.database.utils import transaction
from src.exceptions import NotFoundError, StateConflictError, ValidationFailedError
from src.packages.albums import repository as albums_repository
from src.packages.photos import repository
from src.packages.photos.config import (
    ALLOWED_CONTENT_TYPES,
    MAX_FILE_SIZE,
    UPLOAD_GRANT_TTL,
    photos_settings,
)
from src.packages.photos.schemas import AvailablePhotoRow, ConfirmationOutcome, GrantFileInput
from src.storage.factory import storage_port
from src.storage.port import UploadGrant, object_key


def _validate_files(files: list[GrantFileInput]) -> None:
    """Before anything is granted, and before the album is even touched
    (D2, D3): the client already knows each file's type and size, so a
    rejection here means the client's own filtering missed something,
    not a normal case this flow needs to be lenient about.
    """
    for index, file in enumerate(files):
        if file.content_type not in ALLOWED_CONTENT_TYPES:
            raise ValidationFailedError(
                field=f"files.{index}.contentType",
                message=f"content type {file.content_type!r} is not allowed",
            )
        if file.size > MAX_FILE_SIZE:
            raise ValidationFailedError(
                field=f"files.{index}.size",
                message=f"file exceeds the maximum size of {MAX_FILE_SIZE} bytes",
            )


async def grant_batch(
    connection: AsyncConnection, *, album_id: UUID, owner_id: UUID, files: list[GrantFileInput]
) -> list[tuple[UUID, int, UploadGrant]]:
    _validate_files(files)

    # Locks the album for the rest of this transaction (D12, D14): a
    # second batch granted for the same album at the same time waits
    # here instead of computing the occupancy count or the next position
    # from a view of the album that's about to change.
    owner = await albums_repository.lock_owned_album_id(
        connection, album_id=album_id, owner_id=owner_id
    )
    if owner is None:
        raise NotFoundError()

    occupied = await repository.count_occupied_slots(connection, album_id=album_id)
    remaining = photos_settings.album_max_photos - occupied
    if len(files) > remaining:
        raise StateConflictError(
            code="album_full",
            message=f"the album has room for {max(remaining, 0)} more photo(s)",
            details={"remaining": max(remaining, 0)},
        )

    base_position = await repository.next_position(connection, album_id=album_id)
    expires_at = datetime.now(UTC) + UPLOAD_GRANT_TTL

    results: list[tuple[UUID, int, UploadGrant]] = []
    rows: list[dict] = []
    for offset, file in enumerate(files):
        photo_id = uuid4()
        position = base_position + offset
        grant = storage_port.grant_upload(
            album_id=str(album_id),
            photo_id=str(photo_id),
            content_type=file.content_type,
            max_size=MAX_FILE_SIZE,
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
        results.append((photo_id, position, grant))

    await repository.insert_pending_photos(connection, rows)
    return results


async def list_photos(connection: AsyncConnection, *, album_id: UUID) -> list[AvailablePhotoRow]:
    return await repository.list_available_photos(connection, album_id=album_id)


async def confirm_batch(
    *, album_id: UUID, owner_id: UUID, photo_ids: list[UUID]
) -> tuple[list[ConfirmationOutcome], list[str]]:
    """Verifies each photo against its real object (photo-upload spec),
    never against what the client declared. Deliberately outside any
    single transaction the whole way through: each photo's DB write
    commits on its own, immediately before or after the one network call
    that photo needs, so nothing here ever holds a transaction open
    across a wait on storage (D6).
    """
    async with transaction() as connection:
        photos = await repository.get_owned_photos(
            connection, album_id=album_id, owner_id=owner_id, photo_ids=photo_ids
        )
    if photos is None:
        raise NotFoundError()

    results: list[ConfirmationOutcome] = []
    warm_up_keys: list[str] = []
    rejected_keys: list[str] = []

    for photo in photos:
        if photo.available:
            # D4: reconfirming is inert and needs no call to storage at all.
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
        results.append(ConfirmationOutcome(photo_id=photo.id, status="available"))
        warm_up_keys.append(key)

    if rejected_keys:
        await storage_port.delete_objects(object_keys=rejected_keys)

    return results, warm_up_keys


async def delete_photo(*, album_id: UUID, owner_id: UUID, photo_id: UUID) -> None:
    """Its own transaction, committed before anything talks to storage
    (D6) -- the same reasoning as `albums.service.delete_album`.
    """
    async with transaction() as connection:
        deleted = await repository.delete_owned_photo(
            connection, album_id=album_id, owner_id=owner_id, photo_id=photo_id
        )
    if not deleted:
        raise NotFoundError()
    key = object_key(album_id=str(album_id), photo_id=str(photo_id))
    await storage_port.delete_objects(object_keys=[key])
