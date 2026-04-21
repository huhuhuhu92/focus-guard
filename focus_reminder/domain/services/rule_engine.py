from __future__ import annotations

from dataclasses import dataclass

from focus_reminder.domain.enums.media_state import MediaState
from focus_reminder.domain.enums.reminder_decision import ReminderDecision
from focus_reminder.domain.models.config import FocusConfig
from focus_reminder.domain.models.runtime_state import RuntimeState


@dataclass(slots=True)
class RuleEvaluation:
    decision: ReminderDecision
    reason: str


class ReminderRuleEngine:
    def evaluate(
        self,
        config: FocusConfig,
        runtime_state: RuntimeState,
        idle_seconds: int,
        media_state: MediaState,
        now_monotonic: float,
    ) -> RuleEvaluation:
        if not config.monitor_enabled:
            return RuleEvaluation(ReminderDecision.NONE, "monitor_disabled")

        if runtime_state.monitoring_paused:
            return RuleEvaluation(ReminderDecision.NONE, "monitor_paused")

        if runtime_state.cooldown_until is not None and now_monotonic < runtime_state.cooldown_until:
            return self._evaluate_pre_only_during_cooldown(config, runtime_state, idle_seconds)

        if runtime_state.fullscreen_active:
            return RuleEvaluation(ReminderDecision.NONE, "fullscreen_active")

        if media_state == MediaState.VIDEO_PLAYING:
            return RuleEvaluation(ReminderDecision.NONE, "video_exempt")

        if idle_seconds >= config.idle_threshold_seconds:
            return RuleEvaluation(ReminderDecision.FULLSCREEN_REMINDER, "idle_reached_fullscreen_threshold")

        if (
            config.enable_pre_reminder
            and not runtime_state.pre_reminder_shown
            and idle_seconds >= config.pre_threshold_seconds
        ):
            return RuleEvaluation(ReminderDecision.PRE_REMINDER, "idle_reached_pre_threshold")

        return RuleEvaluation(ReminderDecision.NONE, "no_rule_matched")

    def _evaluate_pre_only_during_cooldown(
        self,
        config: FocusConfig,
        runtime_state: RuntimeState,
        idle_seconds: int,
    ) -> RuleEvaluation:
        if (
            config.enable_pre_reminder
            and not runtime_state.pre_reminder_shown
            and idle_seconds >= config.pre_threshold_seconds
            and idle_seconds < config.idle_threshold_seconds
        ):
            return RuleEvaluation(ReminderDecision.PRE_REMINDER, "cooldown_pre_reminder")

        return RuleEvaluation(ReminderDecision.NONE, "cooldown_blocking_fullscreen")

