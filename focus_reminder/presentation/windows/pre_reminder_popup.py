from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class PreReminderPopup(QWidget):
    def __init__(self) -> None:
        super().__init__(None, Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setWindowTitle("Focus Reminder")

        self._message = QLabel("", self)
        self._message.setWordWrap(True)
        self._message.setStyleSheet("color: #f5f7ff; font-size: 14px;")

        layout = QVBoxLayout()
        layout.setContentsMargins(16, 12, 16, 12)
        layout.addWidget(self._message)
        self.setLayout(layout)
        self.setStyleSheet(
            """
            QWidget {
                background-color: rgba(21, 26, 56, 230);
                border: 1px solid rgba(116, 146, 255, 200);
                border-radius: 12px;
            }
            """
        )
        self.resize(340, 110)

    def show_message(self, message: str, timeout_ms: int = 4000) -> None:
        self._message.setText(message)
        self._place_bottom_right()
        self.show()
        self.raise_()
        QTimer.singleShot(timeout_ms, self.hide)

    def _place_bottom_right(self) -> None:
        screen = QGuiApplication.primaryScreen()
        if screen is None:
            return
        available = screen.availableGeometry()
        x = available.right() - self.width() - 20
        y = available.bottom() - self.height() - 20
        self.move(x, y)
