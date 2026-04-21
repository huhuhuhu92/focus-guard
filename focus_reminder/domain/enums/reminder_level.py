from __future__ import annotations

from enum import Enum


class ReminderLevel(str, Enum):
    PRE_REMINDER = "pre_reminder"
    FULLSCREEN_REMINDER = "fullscreen_reminder"

