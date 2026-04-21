from __future__ import annotations

import time
from typing import Optional

from focus_reminder.domain.interfaces.window_state_provider import IWindowStateProvider

try:
    import win32gui  # type: ignore
    import win32process  # type: ignore
except ImportError:  # pragma: no cover - optional dependency on non-Windows env
    win32gui = None
    win32process = None

try:
    import psutil  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    psutil = None


class WindowStateProvider(IWindowStateProvider):
    def __init__(self, process_name_cache_ttl_seconds: float = 10.0) -> None:
        self._cache_ttl = max(0.5, float(process_name_cache_ttl_seconds))
        self._last_pid: Optional[int] = None
        self._last_process_name: Optional[str] = None
        self._last_process_name_lookup_ts: float = 0.0

    def get_foreground_process_name(self) -> Optional[str]:
        if win32gui is None or win32process is None:
            return None

        try:
            hwnd = win32gui.GetForegroundWindow()
            if not hwnd:
                return None
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            if not pid:
                return None
            if psutil is None:
                return f"pid:{pid}"
            now = time.monotonic()
            if (
                self._last_pid == pid
                and self._last_process_name is not None
                and (now - self._last_process_name_lookup_ts) <= self._cache_ttl
            ):
                return self._last_process_name

            process_name = psutil.Process(pid).name()
            self._last_pid = pid
            self._last_process_name = process_name
            self._last_process_name_lookup_ts = now
            return process_name
        except Exception:
            return None

    def get_foreground_window_title(self) -> Optional[str]:
        if win32gui is None:
            return None
        try:
            hwnd = win32gui.GetForegroundWindow()
            if not hwnd:
                return None
            title = win32gui.GetWindowText(hwnd)
            return title or None
        except Exception:
            return None
