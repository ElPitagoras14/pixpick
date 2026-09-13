"""Internal data shapes: how a photo looks inside the backend, in the
schema's own naming. Never returned to a client as-is -- see responses.py
for what crosses the API boundary (api-conventions spec).
"""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class PhotoRecord(BaseModel):
    id: UUID
    album_id: UUID
    position: int
    available: bool
    declared_content_type: str
    declared_size: int
    size: int | None = None
    width: int | None = None
    height: int | None = None
    upload_expires_at: datetime


class AvailablePhotoRow(BaseModel):
    """What the grid needs (task 6.4): enough to render a thumbnail and
    reserve its space before it loads."""

    id: UUID
    position: int
    width: int | None = None
    height: int | None = None


class GrantFileInput(BaseModel):
    """One file of a batch request for upload grants, already validated
    by the request body's own schema -- everything `service.grant_batch`
    needs and nothing about the HTTP shape it arrived in."""

    content_type: str
    size: int
    width: int | None = None
    height: int | None = None


class ConfirmationOutcome(BaseModel):
    """One photo's result of a confirmation batch (photo-upload spec):
    the three outcomes confirming can produce, never a fourth."""

    photo_id: UUID
    status: Literal["available", "rejected", "pending"]
