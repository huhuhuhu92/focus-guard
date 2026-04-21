from __future__ import annotations

import time

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from focus_reminder.domain.enums.dismiss_mode import DismissMode


class FullscreenPopup(QDialog):
    dismissed = Signal(str, int)

    def __init__(self) -> None:
        super().__init__(None, Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self._shown_at = 0.0
        self._dismissed = False
        self._dismiss_mode = DismissMode.ACTIVITY
        self._init_ui()

    def _init_ui(self) -> None:
        self.setModal(True)
        self.setWindowTitle("Focus Reminder")
        self.setStyleSheet(
            """
            QDialog {
                background-color: rgba(7, 10, 24, 220);
            }
            QLabel#message {
                color: #ffffff;
                font-size: 30px;
                font-weight: bold;
            }
            QLabel#hint {
                color: #9cc4ff;
                font-size: 16px;
            }
            QPushButton {
                padding: 10px 28px;
                border-radius: 8px;
                color: #f5f8ff;
                background: #1f4fff;
                font-size: 16px;
            }
            QPushButton:hover {
                background: #3d67ff;
            }
            """
        )

        self._message_label = QLabel("", self)
        self._message_label.setObjectName("message")
        self._message_label.setAlignment(Qt.AlignCenter)

        self._hint_label = QLabel("", self)
        self._hint_label.setObjectName("hint")
        self._hint_label.setAlignment(Qt.AlignCenter)

        self._close_btn = QPushButton("我已回到任务", self)
        self._close_btn.clicked.connect(self._on_manual_close)

        button_row = QHBoxLayout()
        button_row.addStretch(1)
        button_row.addWidget(self._close_btn)
        button_row.addStretch(1)

        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.addStretch(1)
        layout.addWidget(self._message_label)
        layout.addSpacing(12)
        layout.addWidget(self._hint_label)
        layout.addSpacing(28)
        layout.addLayout(button_row)
        layout.addStretch(1)
        self.setLayout(layout)

    def show_popup(
        self,
        message: str,
        dismiss_mode: DismissMode,
        topmost: bool = True,
        overlay: bool = True,
    ) -> None:
        self._dismiss_mode = dismiss_mode
        self._dismissed = False
        self._shown_at = time.monotonic()

        flags = Qt.Window | Qt.FramelessWindowHint
        if topmost:
            flags |= Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)

        self._message_label.setText(message)
        if dismiss_mode == DismissMode.ACTIVITY:
            self._hint_label.setText("检测到键盘或鼠标活动后将自动关闭提醒")
            self._close_btn.hide()
        else:
            self._hint_label.setText("请点击按钮确认已回到任务")
            self._close_btn.show()

        if overlay:
            self.showFullScreen()
        else:
            self.resize(880, 460)
            self.show()
            self.raise_()
            self.activateWindow()

    def dismiss_by_activity(self) -> None:
        if self.isVisible() and self._dismiss_mode == DismissMode.ACTIVITY:
            self._finish("activity")

    def _on_manual_close(self) -> None:
        self._finish("manual")

    def _finish(self, reason: str) -> None:
        if self._dismissed:
            return
        self._dismissed = True
        duration_ms = int((time.monotonic() - self._shown_at) * 1000)
        self.dismissed.emit(reason, max(0, duration_ms))
        self.hide()
