from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from focus_reminder.domain.enums.dismiss_mode import DismissMode


@dataclass(slots=True)
class FocusConfig:
    idle_threshold_seconds: int = 5 * 60
    pre_reminder_seconds: int = 60
    enable_pre_reminder: bool = True
    cooldown_seconds: int = 60
    dismiss_mode: DismissMode = DismissMode.ACTIVITY
    enable_history: bool = True
    monitor_enabled: bool = True
    poll_interval_ms: int = 1000
    pre_reminder_message: str = "你已接近低专注状态，请尝试回到当前任务。"
    fullscreen_message: str = "请回到当前任务，重启专注状态。"
    fullscreen_topmost: bool = True
    fullscreen_overlay: bool = True
    start_minimized_to_tray: bool = True

    @property
    def pre_threshold_seconds(self) -> int:
        return max(0, self.idle_threshold_seconds - self.pre_reminder_seconds)

    def sanitized(self) -> "FocusConfig":
        defaults = FocusConfig()
        idle_threshold = max(30, int(self.idle_threshold_seconds))
        pre_seconds = max(0, int(self.pre_reminder_seconds))
        cooldown = max(0, int(self.cooldown_seconds))
        poll_interval = max(250, int(self.poll_interval_ms))
        return FocusConfig(
            idle_threshold_seconds=idle_threshold,
            pre_reminder_seconds=pre_seconds,
            enable_pre_reminder=bool(self.enable_pre_reminder),
            cooldown_seconds=cooldown,
            dismiss_mode=self.dismiss_mode,
            enable_history=bool(self.enable_history),
            monitor_enabled=bool(self.monitor_enabled),
            poll_interval_ms=poll_interval,
            pre_reminder_message=self.pre_reminder_message.strip() or defaults.pre_reminder_message,
            fullscreen_message=self.fullscreen_message.strip() or defaults.fullscreen_message,
            fullscreen_topmost=bool(self.fullscreen_topmost),
            fullscreen_overlay=bool(self.fullscreen_overlay),
            start_minimized_to_tray=bool(self.start_minimized_to_tray),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "idle_threshold_seconds": self.idle_threshold_seconds,
            "pre_reminder_seconds": self.pre_reminder_seconds,
            "enable_pre_reminder": self.enable_pre_reminder,
            "cooldown_seconds": self.cooldown_seconds,
            "dismiss_mode": self.dismiss_mode.value,
            "enable_history": self.enable_history,
            "monitor_enabled": self.monitor_enabled,
            "poll_interval_ms": self.poll_interval_ms,
            "pre_reminder_message": self.pre_reminder_message,
            "fullscreen_message": self.fullscreen_message,
            "fullscreen_topmost": self.fullscreen_topmost,
            "fullscreen_overlay": self.fullscreen_overlay,
            "start_minimized_to_tray": self.start_minimized_to_tray,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FocusConfig":
        defaults = cls()
        dismiss_raw = str(data.get("dismiss_mode", DismissMode.ACTIVITY.value))
        try:
            dismiss_mode = DismissMode(dismiss_raw)
        except ValueError:
            dismiss_mode = DismissMode.ACTIVITY

        cfg = cls(
            idle_threshold_seconds=int(data.get("idle_threshold_seconds", defaults.idle_threshold_seconds)),
            pre_reminder_seconds=int(data.get("pre_reminder_seconds", defaults.pre_reminder_seconds)),
            enable_pre_reminder=bool(data.get("enable_pre_reminder", defaults.enable_pre_reminder)),
            cooldown_seconds=int(data.get("cooldown_seconds", defaults.cooldown_seconds)),
            dismiss_mode=dismiss_mode,
            enable_history=bool(data.get("enable_history", defaults.enable_history)),
            monitor_enabled=bool(data.get("monitor_enabled", defaults.monitor_enabled)),
            poll_interval_ms=int(data.get("poll_interval_ms", defaults.poll_interval_ms)),
            pre_reminder_message=str(data.get("pre_reminder_message", defaults.pre_reminder_message)),
            fullscreen_message=str(data.get("fullscreen_message", defaults.fullscreen_message)),
            fullscreen_topmost=bool(data.get("fullscreen_topmost", defaults.fullscreen_topmost)),
            fullscreen_overlay=bool(data.get("fullscreen_overlay", defaults.fullscreen_overlay)),
            start_minimized_to_tray=bool(data.get("start_minimized_to_tray", defaults.start_minimized_to_tray)),
        )
        return cfg.sanitized()
