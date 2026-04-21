from __future__ import annotations

from abc import ABC, abstractmethod


class ISessionStateProvider(ABC):
    @abstractmethod
    def is_session_locked(self) -> bool:
        raise NotImplementedError

