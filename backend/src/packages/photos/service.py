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
) -> GrantBatchResult:
    """Grants what fits and explains what does not (D4, D5). Two
    independent capacity limits are evaluated per file -- the album's
    maximum number of photos and the owner's storage -- and a file is
    granted only if it fits in both.

    Neither one rejects the whole batch: running out of capacity is a
    fact about the account's state, not a mistake in what was asked, so
    what fits is granted and what does not comes back named and
    explained. An inadmissible *file*, checked above, still rejects the
    batch whole -- the client knows its own files' type and size before
    asking, so that one really is an inconsistency.
    """
    _validate_files(files)

    # Locks the *person* for the rest of this transaction (D1), where
    # granting used to lock the album: the account's limit spans every
    # album its owner has, so two batches in two of their albums have to
    # serialize against each other, which a lock on one album cannot do.
    # Every album has exactly one owner, so this still serializes the
    # position and occupancy counting the album lock protected.
    locked_owner = await auth_repository.lock_user_id(connection, user_id=owner_id)
    if locked_owner is None:
        raise NotFoundError()

    # Ownership as a query of its own, now that it no longer travels
    # attached to the lock (D1).
    album = await albums_repository.get_owned_album(
        connection, album_id=album_id, owner_id=owner_id
    )
    if album is None:
        raise NotFoundError()

    occupied = await repository.count_occupied_slots(connection, album_id=album_id)
    used_bytes = await quota_repository.account_used_bytes(connection, owner_id=owner_id)
    remaining_photos = max(photos_settings.album_max_photos - occupied, 0)
    remaining_bytes = max(photos_settings.account_max_bytes - used_bytes, 0)

    base_position = await repository.next_position(connection, album_id=album_id)
    expires_at = datetime.now(UTC) + UPLOAD_GRANT_TTL

    granted: list[GrantedFile] = []
    denied: list[DeniedFile] = []
    rows: list[dict] = []
    for index, file in enumerate(files):
        # The album is checked first: once it is full it is full for
        # every file left, so its own reason is the one that stands even
        # when the account has no space either (D5 -- for this limit
        # there is nothing to skip ahead to).
        if remaining_photos <= 0:
            denied.append(DeniedFile(index=index, reason="album_full", remaining_photos=0))
            continue
        if file.size > remaining_bytes:
            # Skipped, not stopped on (D5): a smaller file further down
            # the batch may still fit, and letting one large file at the
            # front discard the rest would waste space for no reason
            # other than the order they were picked in.
            denied.append(
                DeniedFile(index=index, reason="account_full", remaining_bytes=remaining_bytes)
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
        # Both limits are charged as the walk goes (photo-upload spec):
        # a file waiting to be confirmed occupies its slot and its
        # declared size from the moment its grant is issued, so a batch
        # cannot outgrow either limit against itself.
        remaining_photos -= 1
        remaining_bytes -= file.size

    if rows:
        await repository.insert_pending_photos(connection, rows)
    return GrantBatchResult(granted=granted, denied=denied)


async def list_photos(connection: AsyncConnection, *, album_id: UUID) -> list[AvailablePhotoRow]:
    return await repository.list_available_photos(connection, album_id=album_id)


async def get_gallery(
    connection: AsyncConnection, *, album_id: UUID, user_id: UUID, rating_filter: RatingFilter
) -> GalleryResult:
    """Fetches every available photo with `user_id`'s own rating exactly
    once, regardless of which filter was asked for (D1), and computes
    the four counts in that same pass (D2): the requested slice and the
    counts for the other three filters always come from the same rows,
    so they can never disagree with each other.
    """
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
    """Verifies each photo against its real object (photo-upload spec),
    never against what the client declared. Deliberately outside any
    single transaction the whole way through: each photo's DB write
    commits on its own, immediately before or after the one network call
    that photo needs, so nothing here ever holds a transaction open
    across a wait on storage (D6).
    """
    async with transaction() as connection:
        # Confirming, like granting, is owner-only (album-management spec,
        # modified by add-share-and-swipe): raises `ForbiddenError` for a
        # member who isn't the owner, `NotFoundError` for anyone else.
        # Deliberately not `Depends(get_owned_album)` at the router, per
        # D6 above, so the check happens here instead.
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
            # D4 in album-retention's design: the same transaction that
            # makes the photo available restarts its album's plazo, so
            # a confirmation that rolls back never moves it either.
            await albums_repository.touch_renewed_at(connection, album_id=photo.album_id)
        results.append(ConfirmationOutcome(photo_id=photo.id, status="available"))
        warm_up_keys.append(key)

    if rejected_keys:
        await storage_port.delete_objects(object_keys=rejected_keys)

    return results, warm_up_keys


async def delete_photo(*, album_id: UUID, user_id: UUID, photo_id: UUID) -> None:
    """Its own transaction, committed before anything talks to storage
    (D6) -- the same reasoning as `albums.service.delete_album`. Deleting
    a photo is owner-only (album-management spec, modified by
    add-share-and-swipe), checked here rather than through
    `Depends(get_owned_album)`, for the same D6 reason `confirm_batch` does.
    """
    async with transaction() as connection:
        await albums_service.require_owned_album(connection, album_id=album_id, user_id=user_id)
        deleted = await repository.delete_owned_photo(
            connection, album_id=album_id, owner_id=user_id, photo_id=photo_id
        )
    if not deleted:
        raise NotFoundError()
    key = object_key(album_id=str(album_id), photo_id=str(photo_id))
    await storage_port.delete_objects(object_keys=[key])
