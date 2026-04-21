from __future__ import annotations

import time

from PySide6.QtCore import QObject, Signal

try:
    from pynput import keyboard, mouse
except ImportError:  # pragma: no cover - optional in CI
    keyboard = None
    mouse = None


class PynputInputMonitor(QObject):
    activity_detected = Signal(float)

    def __init__(self) -> None:
        super().__init__()
        self._keyboard_listener = None
        self._mouse_listener = None
        self._last_emit = 0.0
        self._running = False

    @property
    def available(self) -> bool:
        return keyboard is not None and mouse is not None

    def start(self) -> None:
        if self._running or not self.available:
            return

        self._keyboard_listener = keyboard.Listener(on_press=self._on_input)
        self._mouse_listener = mouse.Listener(
            on_move=self._on_move,
            on_click=self._on_input,
            on_scroll=self._on_input,
        )
        self._keyboard_listener.start()
        self._mouse_listener.start()
        self._running = True

    def stop(self) -> None:
        if not self._running:
            return
        if self._keyboard_listener is not None:
            self._keyboard_listener.stop()
            self._keyboard_listener = None
        if self._mouse_listener is not None:
            self._mouse_listener.stop()
            self._mouse_listener = None
        self._running = False

    def _on_move(self, _x: int, _y: int) -> None:
        now = time.monotonic()
        if now - self._last_emit < 0.2:
            return
        self._emit(now)

    def _on_input(self, *_args) -> None:
        self._emit(time.monotonic())

    def _emit(self, now: float) -> None:
        self._last_emit = now
        self.activity_detected.emit(now)

