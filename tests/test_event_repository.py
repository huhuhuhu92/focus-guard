from __future__ import annotations

import shutil
import unittest
import uuid
from datetime import datetime, timedelta
from pathlib import Path

from focus_reminder.domain.enums.dismiss_mode import DismissMode
from focus_reminder.domain.enums.media_state import MediaState
from focus_reminder.domain.enums.reminder_level import ReminderLevel
from focus_reminder.domain.models.reminder_event import ReminderEvent
from focus_reminder.infrastructure.storage.event_repository import ReminderEventRepository
from focus_reminder.infrastructure.storage.sqlite_manager import SQLiteManager


class EventRepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        base = Path("tests/.tmp")
        base.mkdir(parents=True, exist_ok=True)
        self._workdir = base / str(uuid.uuid4())
        self._workdir.mkdir(parents=True, exist_ok=True)
        self._sqlite = SQLiteManager(self._workdir / "focus_reminder.db")
        self._sqlite.initialize()
        self._repo = ReminderEventRepository(self._sqlite)

    def tearDown(self) -> None:
        shutil.rmtree(self._workdir, ignore_errors=True)

    def test_trigger_reason_is_persisted(self) -> None:
        event = ReminderEvent(
            event_id=str(uuid.uuid4()),
            level=ReminderLevel.PRE_REMINDER,
            triggered_at=datetime.now(),
            idle_seconds=250,
            media_state=MediaState.NONE,
            dismiss_mode=DismissMode.ACTIVITY,
            trigger_reason="idle_reached_pre_threshold",
            dismiss_reason="auto",
            popup_duration_ms=0,
        )
        self._repo.add_event(event)
        rows = self._repo.get_recent_events(limit=1)
        self.assertEqual(rows[0]["trigger_reason"], "idle_reached_pre_threshold")

    def test_reason_distribution_with_time_window(self) -> None:
        now = datetime.now()
        inside_event = ReminderEvent(
            event_id=str(uuid.uuid4()),
            level=ReminderLevel.FULLSCREEN_REMINDER,
            triggered_at=now - timedelta(days=1),
            idle_seconds=400,
            media_state=MediaState.NONE,
            dismiss_mode=DismissMode.ACTIVITY,
            trigger_reason="idle_reached_fullscreen_threshold",
            dismiss_reason="activity",
            popup_duration_ms=2000,
        )
        older_event = ReminderEvent(
            event_id=str(uuid.uuid4()),
            level=ReminderLevel.PRE_REMINDER,
            triggered_at=now - timedelta(days=12),
            idle_seconds=200,
            media_state=MediaState.NONE,
            dismiss_mode=DismissMode.ACTIVITY,
            trigger_reason="idle_reached_pre_threshold",
            dismiss_reason="auto",
            popup_duration_ms=0,
        )
        self._repo.add_event(inside_event)
        self._repo.add_event(older_event)

        reason_map = dict(self._repo.get_trigger_reason_distribution(days=7, now=now))
        self.assertEqual(reason_map.get("idle_reached_fullscreen_threshold"), 1)
        self.assertNotIn("idle_reached_pre_threshold", reason_map)


if __name__ == "__main__":
    unittest.main()

