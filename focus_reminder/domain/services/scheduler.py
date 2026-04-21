from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from focus_reminder.domain.enums.media_state import MediaState
from focus_reminder.domain.enums.reminder_decision import ReminderDecision
from focus_reminder.domain.models.config import FocusConfig
from focus_reminder.domain.models.runtime_state import RuntimeState
from focus_reminder.domain.services.idle_service import IdleService
from focus_reminder.domain.services.rule_engine import ReminderRuleEngine
from focus_reminder.domain.interfaces.media_state_provider import IMediaStateProvider
from focus_reminder.domain.interfaces.window_state_provider import IWindowStateProvider


@dataclass(slots=True)
class TickResult:
    decision: ReminderDecision
    reason: str
    idle_seconds: int
    media_state: MediaState
    foreground_app: Optional[str]
    foreground_title: Optional[str]


class ReminderScheduler:
    def __init__(
        self,
        config: FocusConfig,
        runtime_state: RuntimeState,
        idle_service: IdleService,
        rule_engine: ReminderRuleEngine,
        media_state_provider: IMediaStateProvider,
        window_state_provider: IWindowStateProvider,
    ) -> None:
        self._config = config
        self._state = runtime_state
        self._idle_service = idle_service
        self._rule_engine = rule_engine
        self._media_state_provider = media_state_provider
        self._window_state_provider = window_state_provider

    @property
    def state(self) -> RuntimeState:
        return self._state

    @property
    def config(self) -> FocusConfig:
        return self._config

    def update_config(self, config: FocusConfig) -> None:
        self._config = config
        if not config.monitor_enabled:
            self._state.pre_reminder_shown = False
            self._state.fullscreen_active = False

    def pause_monitoring(self, now_monotonic: float, duration_seconds: Optional[int]) -> None:
        self._state.monitoring_paused = True
        self._state.pause_until = (
            now_monotonic + max(0, duration_seconds) if duration_seconds is not None else None
        )

    def resume_monitoring(self) -> None:
        self._state.monitoring_paused = False
        self._state.pause_until = None

    def on_activity(self, now_monotonic: float) -> bool:
        self._state.last_active_time = now_monotonic
        self._state.pre_reminder_shown = False
        return self._state.fullscreen_active and self._config.dismiss_mode.value == "activity"

    def mark_pre_reminder_displayed(self) -> None:
        self._state.pre_reminder_shown = True

    def mark_fullscreen_displayed(self) -> None:
        self._state.fullscreen_active = True

    def mark_fullscreen_dismissed(self, now_monotonic: float, dismiss_reason: str) -> None:
        self._state.fullscreen_active = False
        self._state.cooldown_until = now_monotonic + self._config.cooldown_seconds
        self._state.pre_reminder_shown = False
        if dismiss_reason == "manual":
            self._state.last_active_time = now_monotonic

    def tick(self, now_monotonic: float) -> TickResult:
        if self._state.pause_until is not None and now_monotonic >= self._state.pause_until:
            self.resume_monitoring()

        idle_seconds = self._idle_service.get_idle_seconds(self._state.last_active_time, now_monotonic)
        media_state = self._media_state_provider.get_media_state()
        self._state.current_media_state = media_state.value

        evaluation = self._rule_engine.evaluate(
            config=self._config,
            runtime_state=self._state,
            idle_seconds=idle_seconds,
            media_state=media_state,
            now_monotonic=now_monotonic,
        )

        if evaluation.decision == ReminderDecision.PRE_REMINDER:
            self.mark_pre_reminder_displayed()
        elif evaluation.decision == ReminderDecision.FULLSCREEN_REMINDER:
            self.mark_fullscreen_displayed()

        foreground_app = None
        foreground_title = None
        if evaluation.decision in (
            ReminderDecision.PRE_REMINDER,
            ReminderDecision.FULLSCREEN_REMINDER,
        ):
            foreground_app = self._window_state_provider.get_foreground_process_name()
            foreground_title = self._window_state_provider.get_foreground_window_title()

        return TickResult(
            decision=evaluation.decision,
            reason=evaluation.reason,
            idle_seconds=idle_seconds,
            media_state=media_state,
            foreground_app=foreground_app,
            foreground_title=foreground_title,
        )
