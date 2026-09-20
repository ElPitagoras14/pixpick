from uuid import UUID

from src.models import ApiModel


class ShareLinkResponse(ApiModel):
    """The album's current share link: a single absolute address, built from
    the configured public URL, never from the request's own scheme or host.
    """

    url: str


class EnterShareResponse(ApiModel):
    """What entering a link returns: the album the token granted entry to,
    so the client can navigate straight there without a second request.
    """

    album_id: UUID
