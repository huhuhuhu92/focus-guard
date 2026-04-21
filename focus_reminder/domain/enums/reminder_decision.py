from __future__ import annotations

from enum import Enum


class ReminderDecision(str, Enum):
    NONE = "none"
    PRE_REMINDER = "pre_reminder"
    FULLSCREEN_REMINDER = "fullscreen_reminder"

