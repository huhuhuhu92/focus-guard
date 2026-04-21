from __future__ import annotations

import unittest

from focus_reminder.domain.enums.media_state import MediaState
from focus_reminder.domain.enums.reminder_decision import ReminderDecision
from focus_reminder.domain.models.config import FocusConfig
from focus_reminder.domain.models.runtime_state import RuntimeState
from focus_reminder.domain.services.rule_engine import ReminderRuleEngine


class RuleEngineTests(unittest.TestCase):
    def test_pre_reminder_triggered_before_fullscreen(self) -> None:
        engine = ReminderRuleEngine()
        cfg = FocusConfig(idle_threshold_seconds=300, pre_reminder_seconds=60)
        state = RuntimeState(last_active_time=0.0, pre_reminder_shown=False)

        result = engine.evaluate(
            config=cfg,
            runtime_state=state,
            idle_seconds=250,
            media_state=MediaState.NONE,
            now_monotonic=250.0,
        )
        self.assertEqual(result.decision, ReminderDecision.PRE_REMINDER)

    def test_video_playing_exempts_reminder(self) -> None:
        engine = ReminderRuleEngine()
        cfg = FocusConfig(idle_threshold_seconds=300, pre_reminder_seconds=60)
        state = RuntimeState(last_active_time=0.0, pre_reminder_shown=False)

        result = engine.evaluate(
            config=cfg,
            runtime_state=state,
            idle_seconds=320,
            media_state=MediaState.VIDEO_PLAYING,
            now_monotonic=320.0,
        )
        self.assertEqual(result.decision, ReminderDecision.NONE)

    def test_fullscreen_triggered_when_idle_threshold_reached(self) -> None:
        engine = ReminderRuleEngine()
        cfg = FocusConfig(idle_threshold_seconds=300, pre_reminder_seconds=60)
        state = RuntimeState(last_active_time=0.0, pre_reminder_shown=True)

        result = engine.evaluate(
            config=cfg,
            runtime_state=state,
            idle_seconds=300,
            media_state=MediaState.NONE,
            now_monotonic=300.0,
        )
        self.assertEqual(result.decision, ReminderDecision.FULLSCREEN_REMINDER)

    def test_audio_only_does_not_exempt_fullscreen(self) -> None:
        engine = ReminderRuleEngine()
        cfg = FocusConfig(idle_threshold_seconds=300, pre_reminder_seconds=60)
        state = RuntimeState(last_active_time=0.0, pre_reminder_shown=False)

        result = engine.evaluate(
            config=cfg,
            runtime_state=state,
            idle_seconds=310,
            media_state=MediaState.AUDIO_ONLY,
            now_monotonic=310.0,
        )
        self.assertEqual(result.decision, ReminderDecision.FULLSCREEN_REMINDER)


if __name__ == "__main__":
    unittest.main()
