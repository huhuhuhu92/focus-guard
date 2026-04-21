from __future__ import annotations

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
            return psutil.Process(pid).name()
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

