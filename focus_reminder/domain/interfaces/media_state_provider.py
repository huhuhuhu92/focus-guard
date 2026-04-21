from __future__ import annotations

from abc import ABC, abstractmethod

from focus_reminder.domain.enums.media_state import MediaState


class IMediaStateProvider(ABC):
    @abstractmethod
    def get_media_state(self) -> MediaState:
        raise NotImplementedError

