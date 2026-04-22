from __future__ import annotations

import logging
import sys
import time
import uuid
from datetime import datetime

from PySide6.QtCore import QObject, QTimer
from PySide6.QtWidgets import QApplication

from focus_reminder.app import constants
from focus_reminder.domain.enums.reminder_decision import ReminderDecision
from focus_reminder.domain.enums.reminder_level import ReminderLevel
from focus_reminder.domain.models.config import FocusConfig
from focus_reminder.domain.models.reminder_event import ReminderEvent
from focus_reminder.domain.models.runtime_state import RuntimeState
from focus_reminder.domain.services.idle_service import IdleService
from focus_reminder.domain.services.rule_engine import ReminderRuleEngine
from focus_reminder.domain.services.scheduler import ReminderScheduler
from focus_reminder.infrastructure.input.pynput_monitor import PynputInputMonitor
from focus_reminder.infrastructure.input.win_last_input_monitor import WinLastInputMonitor
from focus_reminder.infrastructure.storage.config_repository import ConfigRepository
from focus_reminder.infrastructure.storage.event_repository import ReminderEventRepository
from focus_reminder.infrastructure.storage.sqlite_manager import SQLiteManager
from focus_reminder.infrastructure.system.media_provider_heuristic import HeuristicMediaStateProvider
from focus_reminder.infrastructure.system.window_provider import WindowStateProvider
from focus_reminder.presentation.presenters.fullscreen_presenter import FullscreenPresenter
from focus_reminder.presentation.presenters.notification_presenter import NotificationPresenter
from focus_reminder.presentation.tray.tray_controller import TrayController
from focus_reminder.presentation.windows.fullscreen_popup import FullscreenPopup
from focus_reminder.presentation.windows.pre_reminder_popup import PreReminderPopup
from focus_reminder.presentation.windows.settings_window import SettingsWindow
from focus_reminder.presentation.windows.stats_window import StatsWindow

logger = logging.getLogger(__name__)


class AppBootstrap(QObject):
    def __init__(self, app: QApplication) -> None:
        super().__init__()
        self._app = app
        constants.DATA_DIR.mkdir(parents=True, exist_ok=True)

        self._config_repo = ConfigRepository(constants.CONFIG_PATH)
        self._config = self._config_repo.load()

        self._sqlite = SQLiteManager(constants.DB_PATH)
        self._sqlite.initialize()
        self._event_repo = ReminderEventRepository(self._sqlite)

        self._runtime_state = RuntimeState(last_active_time=time.monotonic())
        window_provider = WindowStateProvider()
        self._scheduler = ReminderScheduler(
            config=self._config,
            runtime_state=self._runtime_state,
            idle_service=IdleService(),
            rule_engine=ReminderRuleEngine(),
            media_state_provider=HeuristicMediaStateProvider(window_provider),
            window_state_provider=window_provider,
        )

        self._input_monitor = self._create_input_monitor()
        self._input_monitor.activity_detected.connect(self._on_activity_detected)

        self._pre_popup = PreReminderPopup()
        self._fullscreen_popup = FullscreenPopup()
        self._notification_presenter = NotificationPresenter(self._pre_popup)
        self._fullscreen_presenter = FullscreenPresenter(self._fullscreen_popup)
        self._fullscreen_presenter.dismissed.connect(self._on_fullscreen_dismissed)

        self._settings_window = SettingsWindow()
        self._settings_window.load_config(self._config)
        self._settings_window.config_saved.connect(self._on_config_saved)
        self._settings_window.clear_history_requested.connect(self._on_clear_history)

        self._stats_window = StatsWindow(self._event_repo)
        self._settings_window.open_stats_requested.connect(self.show_stats_window)
        self._stats_window.open_settings_requested.connect(self.show_settings_window)

        self._tray = TrayController(self._app)
        self._tray.open_settings_requested.connect(self.show_settings_window)
        self._tray.open_stats_requested.connect(self.show_stats_window)
        self._tray.pause_requested.connect(self._on_pause_requested)
        self._tray.resume_requested.connect(self._on_resume_requested)
        self._tray.quit_requested.connect(self.quit_app)
        self._notification_presenter.attach_tray_icon(self._tray.tray_icon)

        self._timer = QTimer(self)
        self._timer.setInterval(self._config.poll_interval_ms)
        self._timer.timeout.connect(self._on_tick)

        self._monitor_started = False
        self._active_fullscreen_event_id: str | None = None

    def start(self) -> None:
        self._tray.show()
        self._start_monitoring_if_needed()
        self._stats_window.refresh()

        if not self._input_monitor.available:
            self._tray.show_message(
                "Focus Reminder",
                "pynput 未安装，输入自动检测不可用。请先安装依赖。",
            )

        if not self._config.start_minimized_to_tray:
            self.show_settings_window()

    def quit_app(self) -> None:
        self.shutdown()
        self._app.quit()

    def shutdown(self) -> None:
        self._timer.stop()
        self._input_monitor.stop()
        self._tray.hide()

    def show_settings_window(self) -> None:
        self._settings_window.load_config(self._config)
        if self._stats_window.isVisible():
            self._settings_window.setGeometry(self._stats_window.geometry())
            self._stats_window.hide()
        self._settings_window.show()
        self._settings_window.raise_()
        self._settings_window.activateWindow()

    def show_stats_window(self) -> None:
        self._stats_window.refresh()
        if self._settings_window.isVisible():
            self._stats_window.setGeometry(self._settings_window.geometry())
            self._settings_window.hide()
        self._stats_window.show()
        self._stats_window.raise_()
        self._stats_window.activateWindow()

    def _start_monitoring_if_needed(self) -> None:
        if not self._config.monitor_enabled:
            self._stop_monitoring()
            return
        if not self._timer.isActive():
            self._timer.start()
        if not self._monitor_started and self._input_monitor.available:
            self._input_monitor.start()
            self._monitor_started = True

    def _stop_monitoring(self) -> None:
        self._timer.stop()
        if self._monitor_started:
            self._input_monitor.stop()
            self._monitor_started = False

    def _on_tick(self) -> None:
        result = self._scheduler.tick(time.monotonic())
        if result.decision == ReminderDecision.PRE_REMINDER:
            self._handle_pre_reminder(result)
        elif result.decision == ReminderDecision.FULLSCREEN_REMINDER:
            self._handle_fullscreen_reminder(result)

    def _handle_pre_reminder(self, result) -> None:
        self._notification_presenter.show_pre_reminder(self._config.pre_reminder_message)
        if not self._config.enable_history:
            return
        event = ReminderEvent(
            event_id=str(uuid.uuid4()),
            level=ReminderLevel.PRE_REMINDER,
            triggered_at=datetime.now(),
            idle_seconds=result.idle_seconds,
            media_state=result.media_state,
            dismiss_mode=self._config.dismiss_mode,
            trigger_reason=result.reason,
            dismiss_reason="auto",
            popup_duration_ms=0,
            foreground_app=result.foreground_app,
            foreground_title=result.foreground_title,
        )
        self._event_repo.add_event(event)

    def _handle_fullscreen_reminder(self, result) -> None:
        event_id = str(uuid.uuid4())
        self._active_fullscreen_event_id = event_id
        if self._config.enable_history:
            event = ReminderEvent(
                event_id=event_id,
                level=ReminderLevel.FULLSCREEN_REMINDER,
                triggered_at=datetime.now(),
                idle_seconds=result.idle_seconds,
                media_state=result.media_state,
                dismiss_mode=self._config.dismiss_mode,
                trigger_reason=result.reason,
                dismiss_reason=None,
                popup_duration_ms=None,
                foreground_app=result.foreground_app,
                foreground_title=result.foreground_title,
            )
            self._event_repo.add_event(event)

        self._fullscreen_presenter.show_fullscreen(
            message=self._config.fullscreen_message,
            dismiss_mode=self._config.dismiss_mode,
            topmost=self._config.fullscreen_topmost,
            overlay=self._config.fullscreen_overlay,
        )

    def _on_fullscreen_dismissed(self, reason: str, duration_ms: int) -> None:
        self._scheduler.mark_fullscreen_dismissed(time.monotonic(), reason)
        if self._active_fullscreen_event_id and self._config.enable_history:
            self._event_repo.complete_event(
                event_id=self._active_fullscreen_event_id,
                dismiss_reason=reason,
                popup_duration_ms=duration_ms,
            )
        self._active_fullscreen_event_id = None
        self._stats_window.refresh()

    def _on_activity_detected(self, ts: float) -> None:
        should_dismiss = self._scheduler.on_activity(ts)
        if should_dismiss:
            self._fullscreen_presenter.dismiss_by_activity()

    def _on_config_saved(self, config: FocusConfig) -> None:
        old_enabled = self._config.monitor_enabled
        self._config = config.sanitized()
        self._config_repo.save(self._config)
        self._scheduler.update_config(self._config)
        self._timer.setInterval(self._config.poll_interval_ms)
        self._update_input_monitor_interval()

        if old_enabled != self._config.monitor_enabled:
            if self._config.monitor_enabled:
                self._start_monitoring_if_needed()
            else:
                self._stop_monitoring()

        self._tray.show_message("Focus Reminder", "配置已保存")

    def _on_clear_history(self) -> None:
        self._event_repo.clear_all_events()
        self._stats_window.refresh()
        self._tray.show_message("Focus Reminder", "历史提醒已清空")

    def _on_pause_requested(self, duration_seconds: object) -> None:
        seconds = int(duration_seconds) if isinstance(duration_seconds, int) else None
        self._scheduler.pause_monitoring(time.monotonic(), seconds)
        if seconds is None:
            text = "已暂停提醒，等待手动恢复。"
        else:
            text = f"已暂停提醒 {seconds // 60} 分钟。"
        self._tray.show_message("Focus Reminder", text)

    def _on_resume_requested(self) -> None:
        self._scheduler.resume_monitoring()
        self._tray.show_message("Focus Reminder", "提醒已恢复。")
        logger.info("monitoring resumed from tray")

    def _create_input_monitor(self):
        if sys.platform == "win32":
            monitor = WinLastInputMonitor(poll_interval_ms=min(500, self._config.poll_interval_ms))
            if monitor.available:
                return monitor
        return PynputInputMonitor()

    def _update_input_monitor_interval(self) -> None:
        if hasattr(self._input_monitor, "set_poll_interval_ms"):
            interval_ms = min(500, self._config.poll_interval_ms)
            self._input_monitor.set_poll_interval_ms(interval_ms)
