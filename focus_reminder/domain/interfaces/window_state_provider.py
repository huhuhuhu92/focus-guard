from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional


class IWindowStateProvider(ABC):
    @abstractmethod
    def get_foreground_process_name(self) -> Optional[str]:
        raise NotImplementedError

    @abstractmethod
    def get_foreground_window_title(self) -> Optional[str]:
        raise NotImplementedError

