from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QApplication, QMenu, QStyle, QSystemTrayIcon


class TrayController(QObject):
    open_settings_requested = Signal()
    open_stats_requested = Signal()
    pause_requested = Signal(object)  # int seconds or None
    resume_requested = Signal()
    quit_requested = Signal()

    def __init__(self, app: QApplication, icon: Optional[QIcon] = None) -> None:
        super().__init__()
        self._app = app
        self._tray = QSystemTrayIcon(icon or self._default_icon(), self._app)
        self._tray.setToolTip("Focus Reminder")
        self._menu = QMenu()
        self._build_menu()
        self._tray.setContextMenu(self._menu)
        self._tray.activated.connect(self._on_activated)

    @property
    def tray_icon(self) -> QSystemTrayIcon:
        return self._tray

    def show(self) -> None:
        self._tray.show()

    def hide(self) -> None:
        self._tray.hide()

    def show_message(self, title: str, message: str) -> None:
        if self._tray.isVisible():
            self._tray.showMessage(title, message, QSystemTrayIcon.Information, 3000)

    def _default_icon(self) -> QIcon:
        return self._app.style().standardIcon(QStyle.SP_ComputerIcon)

    def _build_menu(self) -> None:
        open_settings = QAction("打开配置", self)
        open_settings.triggered.connect(self.open_settings_requested.emit)

        open_stats = QAction("查看统计", self)
        open_stats.triggered.connect(self.open_stats_requested.emit)

        pause_10 = QAction("暂停 10 分钟", self)
        pause_10.triggered.connect(lambda: self.pause_requested.emit(10 * 60))

        pause_30 = QAction("暂停 30 分钟", self)
        pause_30.triggered.connect(lambda: self.pause_requested.emit(30 * 60))

        pause_manual = QAction("暂停直到手动恢复", self)
        pause_manual.triggered.connect(lambda: self.pause_requested.emit(None))

        resume = QAction("恢复提醒", self)
        resume.triggered.connect(self.resume_requested.emit)

        quit_action = QAction("退出程序", self)
        quit_action.triggered.connect(self.quit_requested.emit)

        for action in (
            open_settings,
            open_stats,
            pause_10,
            pause_30,
            pause_manual,
            resume,
            quit_action,
        ):
            self._menu.addAction(action)

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.DoubleClick:
            self.open_settings_requested.emit()

