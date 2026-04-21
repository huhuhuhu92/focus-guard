from __future__ import annotations

from focus_reminder.domain.enums.media_state import MediaState
from focus_reminder.domain.interfaces.media_state_provider import IMediaStateProvider


class MediaStateProviderStub(IMediaStateProvider):
    def get_media_state(self) -> MediaState:
        # V1.1: reserved extension point. Always treated as no media playing.
        return MediaState.NONE

