from __future__ import annotations

from PySide6.QtWidgets import QSystemTrayIcon

from focus_reminder.presentation.windows.pre_reminder_popup import PreReminderPopup


class NotificationPresenter:
    def __init__(
        self,
        popup: PreReminderPopup,
        tray_icon: QSystemTrayIcon | None = None,
    ) -> None:
        self._popup = popup
        self._tray_icon = tray_icon

    def attach_tray_icon(self, tray_icon: QSystemTrayIcon) -> None:
        self._tray_icon = tray_icon

    def show_pre_reminder(self, message: str) -> None:
        self._popup.show_message(message)
        if self._tray_icon is not None and self._tray_icon.isVisible():
            self._tray_icon.showMessage("Focus Reminder", message, QSystemTrayIcon.Information, 3500)

