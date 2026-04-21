from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from focus_reminder.domain.enums.dismiss_mode import DismissMode
from focus_reminder.domain.enums.media_state import MediaState
from focus_reminder.domain.enums.reminder_level import ReminderLevel


@dataclass(slots=True)
class ReminderEvent:
    event_id: str
    level: ReminderLevel
    triggered_at: datetime
    idle_seconds: int
    media_state: MediaState
    dismiss_mode: DismissMode
    trigger_reason: Optional[str] = None
    dismiss_reason: Optional[str] = None
    popup_duration_ms: Optional[int] = None
    foreground_app: Optional[str] = None
    foreground_title: Optional[str] = None
