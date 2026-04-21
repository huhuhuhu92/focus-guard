from __future__ import annotations

from PySide6.QtCore import QObject, Signal

from focus_reminder.domain.enums.dismiss_mode import DismissMode
from focus_reminder.presentation.windows.fullscreen_popup import FullscreenPopup


class FullscreenPresenter(QObject):
    dismissed = Signal(str, int)

    def __init__(self, popup: FullscreenPopup) -> None:
        super().__init__()
        self._popup = popup
        self._popup.dismissed.connect(self.dismissed.emit)

    def show_fullscreen(
        self,
        message: str,
        dismiss_mode: DismissMode,
        topmost: bool,
        overlay: bool,
    ) -> None:
        self._popup.show_popup(
            message=message,
            dismiss_mode=dismiss_mode,
            topmost=topmost,
            overlay=overlay,
        )

    def dismiss_by_activity(self) -> None:
        self._popup.dismiss_by_activity()

