from __future__ import annotations

import ctypes
import sys
import time
from ctypes import wintypes

from PySide6.QtCore import QObject, QTimer, Signal


class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.UINT),
        ("dwTime", wintypes.DWORD),
    ]


class WinLastInputMonitor(QObject):
    activity_detected = Signal(float)

    def __init__(self, poll_interval_ms: int = 250) -> None:
        super().__init__()
        self._user32 = self._load_user32()
        self._timer = QTimer(self)
        self._timer.setInterval(max(50, int(poll_interval_ms)))
        self._timer.timeout.connect(self._on_poll)
        self._last_tick: int | None = None

    @property
    def available(self) -> bool:
        return self._user32 is not None

    def start(self) -> None:
        if not self.available or self._timer.isActive():
            return
        self._last_tick = self._read_last_input_tick()
        self._timer.start()

    def stop(self) -> None:
        self._timer.stop()

    def set_poll_interval_ms(self, interval_ms: int) -> None:
        self._timer.setInterval(max(50, int(interval_ms)))

    def _on_poll(self) -> None:
        current_tick = self._read_last_input_tick()
        if current_tick is None:
            return
        if self._last_tick is None:
            self._last_tick = current_tick
            return
        if current_tick != self._last_tick:
            self._last_tick = current_tick
            self.activity_detected.emit(time.monotonic())

    def _read_last_input_tick(self) -> int | None:
        if self._user32 is None:
            return None
        info = LASTINPUTINFO()
        info.cbSize = ctypes.sizeof(LASTINPUTINFO)
        ok = self._user32.GetLastInputInfo(ctypes.byref(info))
        if not ok:
            return None
        return int(info.dwTime)

    def _load_user32(self):
        if sys.platform != "win32":
            return None
        try:
            return ctypes.windll.user32
        except Exception:
            return None
