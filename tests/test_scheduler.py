from __future__ import annotations

import unittest

from focus_reminder.domain.enums.media_state import MediaState
from focus_reminder.domain.enums.reminder_decision import ReminderDecision
from focus_reminder.domain.interfaces.media_state_provider import IMediaStateProvider
from focus_reminder.domain.interfaces.window_state_provider import IWindowStateProvider
from focus_reminder.domain.models.config import FocusConfig
from focus_reminder.domain.models.runtime_state import RuntimeState
from focus_reminder.domain.services.idle_service import IdleService
from focus_reminder.domain.services.rule_engine import ReminderRuleEngine
from focus_reminder.domain.services.scheduler import ReminderScheduler


class FixedMediaStateProvider(IMediaStateProvider):
    def __init__(self, state: MediaState) -> None:
        self._state = state

    def get_media_state(self) -> MediaState:
        return self._state


class CountingWindowStateProvider(IWindowStateProvider):
    def __init__(self) -> None:
        self.process_calls = 0
        self.title_calls = 0

    def get_foreground_process_name(self) -> str | None:
        self.process_calls += 1
        return "test.exe"

    def get_foreground_window_title(self) -> str | None:
        self.title_calls += 1
        return "Test Window"


class SchedulerTests(unittest.TestCase):
    def test_does_not_query_window_when_no_reminder(self) -> None:
        window_provider = CountingWindowStateProvider()
        scheduler = ReminderScheduler(
            config=FocusConfig(idle_threshold_seconds=300, pre_reminder_seconds=60),
            runtime_state=RuntimeState(last_active_time=100.0),
            idle_service=IdleService(),
            rule_engine=ReminderRuleEngine(),
            media_state_provider=FixedMediaStateProvider(MediaState.NONE),
            window_state_provider=window_provider,
        )

        result = scheduler.tick(now_monotonic=120.0)
        self.assertEqual(result.decision, ReminderDecision.NONE)
        self.assertEqual(window_provider.process_calls, 0)
        self.assertEqual(window_provider.title_calls, 0)

    def test_queries_window_when_pre_reminder_triggered(self) -> None:
        window_provider = CountingWindowStateProvider()
        scheduler = ReminderScheduler(
            config=FocusConfig(idle_threshold_seconds=300, pre_reminder_seconds=60),
            runtime_state=RuntimeState(last_active_time=0.0),
            idle_service=IdleService(),
            rule_engine=ReminderRuleEngine(),
            media_state_provider=FixedMediaStateProvider(MediaState.NONE),
            window_state_provider=window_provider,
        )

        result = scheduler.tick(now_monotonic=250.0)
        self.assertEqual(result.decision, ReminderDecision.PRE_REMINDER)
        self.assertEqual(window_provider.process_calls, 1)
        self.assertEqual(window_provider.title_calls, 1)


if __name__ == "__main__":
    unittest.main()

