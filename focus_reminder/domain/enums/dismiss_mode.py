from __future__ import annotations

from enum import Enum


class DismissMode(str, Enum):
    ACTIVITY = "activity"
    MANUAL = "manual"

