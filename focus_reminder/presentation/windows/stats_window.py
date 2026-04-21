from __future__ import annotations

from datetime import datetime

from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from focus_reminder.infrastructure.storage.event_repository import ReminderEventRepository


class StatsWindow(QWidget):
    def __init__(self, repository: ReminderEventRepository) -> None:
        super().__init__()
        self._repo = repository
        self.setWindowTitle("Focus Reminder 统计")
        self.resize(860, 620)
        self._build_ui()

    def _build_ui(self) -> None:
        self._today_count = QLabel("今日提醒: 0", self)
        self._today_count.setStyleSheet("font-size: 22px; font-weight: 600;")

        self._trend_text = QTextEdit(self)
        self._trend_text.setReadOnly(True)

        self._hour_text = QTextEdit(self)
        self._hour_text.setReadOnly(True)

        self._events_table = QTableWidget(self)
        self._events_table.setColumnCount(6)
        self._events_table.setHorizontalHeaderLabels(
            ["时间", "等级", "空闲(s)", "媒体", "关闭原因", "前台进程"]
        )
        self._events_table.horizontalHeader().setStretchLastSection(True)

        refresh_btn = QPushButton("刷新", self)
        refresh_btn.clicked.connect(self.refresh)

        header = QHBoxLayout()
        header.addWidget(self._today_count)
        header.addStretch(1)
        header.addWidget(refresh_btn)

        layout = QVBoxLayout()
        layout.addLayout(header)
        layout.addWidget(QLabel("最近 7 天提醒趋势"))
        layout.addWidget(self._trend_text)
        layout.addWidget(QLabel("今日 24 小时提醒分布"))
        layout.addWidget(self._hour_text)
        layout.addWidget(QLabel("最近提醒事件"))
        layout.addWidget(self._events_table)
        self.setLayout(layout)

    def refresh(self) -> None:
        self._today_count.setText(f"今日提醒: {self._repo.get_today_count(datetime.now())}")

        trend_lines = [
            f"{label}: {count}"
            for label, count in self._repo.get_last_n_days_counts(7, datetime.now())
        ]
        self._trend_text.setPlainText("\n".join(trend_lines) or "暂无数据")

        hour_lines = [
            f"{hour}:00 - {count}"
            for hour, count in self._repo.get_hourly_distribution(datetime.now())
        ]
        self._hour_text.setPlainText("\n".join(hour_lines) or "暂无数据")

        rows = self._repo.get_recent_events(limit=100)
        self._events_table.setRowCount(len(rows))
        for idx, row in enumerate(rows):
            self._events_table.setItem(idx, 0, QTableWidgetItem(str(row.get("triggered_at", ""))))
            self._events_table.setItem(idx, 1, QTableWidgetItem(str(row.get("level", ""))))
            self._events_table.setItem(idx, 2, QTableWidgetItem(str(row.get("idle_seconds", ""))))
            self._events_table.setItem(idx, 3, QTableWidgetItem(str(row.get("media_state", ""))))
            self._events_table.setItem(idx, 4, QTableWidgetItem(str(row.get("dismiss_reason", ""))))
            self._events_table.setItem(idx, 5, QTableWidgetItem(str(row.get("foreground_app", ""))))
        self._events_table.resizeColumnsToContents()

