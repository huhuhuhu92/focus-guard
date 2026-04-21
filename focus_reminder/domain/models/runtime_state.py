from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from focus_reminder.domain.enums.media_state import MediaState


@dataclass(slots=True)
class RuntimeState:
    last_active_time: float
    pre_reminder_shown: bool = False
    fullscreen_active: bool = False
    monitoring_paused: bool = False
    cooldown_until: Optional[float] = None
    current_media_state: str = MediaState.NONE.value
    pause_until: Optional[float] = None

