from __future__ import annotations

import time

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QDialog, QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

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
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(30, 6, 10, 245),
                    stop:1 rgba(14, 4, 6, 245)
                );
            }
            QFrame#panel {
                background-color: rgba(55, 11, 16, 232);
                border: 2px solid rgba(182, 66, 77, 232);
                border-radius: 20px;
                min-width: 760px;
                max-width: 900px;
            }
            QLabel#title {
                color: #ffb6bc;
                font-size: 20px;
                font-weight: 700;
                letter-spacing: 2px;
            }
            QLabel#message {
                color: #fff3f4;
                font-size: 34px;
                font-weight: 700;
            }
            QLabel#hint {
                color: #f1b3b9;
                font-size: 18px;
            }
            QPushButton {
                padding: 12px 34px;
                border-radius: 12px;
                border: 1px solid #f4adb5;
                color: #fff2f3;
                background: #8f1f2a;
                font-size: 18px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #ab2c39;
                border-color: #ffd0d4;
            }
            """
        )

        panel = QFrame(self)
        panel.setObjectName("panel")

        self._title_label = QLabel("低专注提醒", panel)
        self._title_label.setObjectName("title")
        self._title_label.setAlignment(Qt.AlignCenter)

        self._message_label = QLabel("", panel)
        self._message_label.setObjectName("message")
        self._message_label.setAlignment(Qt.AlignCenter)
        self._message_label.setWordWrap(True)

        self._hint_label = QLabel("", panel)
        self._hint_label.setObjectName("hint")
        self._hint_label.setAlignment(Qt.AlignCenter)
        self._hint_label.setWordWrap(True)

        self._close_btn = QPushButton("我已回到任务", panel)
        self._close_btn.clicked.connect(self._on_manual_close)

        button_row = QHBoxLayout()
        button_row.addStretch(1)
        button_row.addWidget(self._close_btn)
        button_row.addStretch(1)

        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(48, 40, 48, 36)
        panel_layout.setSpacing(14)
        panel_layout.addWidget(self._title_label)
        panel_layout.addSpacing(8)
        panel_layout.addWidget(self._message_label)
        panel_layout.addWidget(self._hint_label)
        panel_layout.addSpacing(18)
        panel_layout.addLayout(button_row)

        root_layout = QVBoxLayout()
        root_layout.setContentsMargins(56, 40, 56, 40)
        root_layout.addStretch(1)
        root_layout.addWidget(panel, 0, Qt.AlignCenter)
        root_layout.addStretch(1)
        self.setLayout(root_layout)

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
