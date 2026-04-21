from __future__ import annotations

from datetime import datetime

from PySide6.QtCharts import (
    QBarCategoryAxis,
    QBarSeries,
    QBarSet,
    QChart,
    QChartView,
    QLineSeries,
    QPieSeries,
    QValueAxis,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from focus_reminder.infrastructure.storage.event_repository import ReminderEventRepository


class StatsWindow(QWidget):
    def __init__(self, repository: ReminderEventRepository) -> None:
        super().__init__()
        self._repo = repository
        self.setWindowTitle("Focus Reminder 统计")
        self.resize(1180, 760)
        self._build_ui()

    def _build_ui(self) -> None:
        self._today_count = QLabel("今日提醒: 0", self)
        self._today_count.setStyleSheet("font-size: 22px; font-weight: 600;")
        self._week_count = QLabel("近7天提醒: 0", self)
        self._week_count.setStyleSheet("font-size: 16px; color: #2b579a;")

        self._trend_chart = QChartView(self)
        self._trend_chart.setRenderHint(QPainter.Antialiasing)
        self._hour_chart = QChartView(self)
        self._hour_chart.setRenderHint(QPainter.Antialiasing)
        self._level_chart = QChartView(self)
        self._level_chart.setRenderHint(QPainter.Antialiasing)
        self._reason_chart = QChartView(self)
        self._reason_chart.setRenderHint(QPainter.Antialiasing)

        charts_grid = QGridLayout()
        charts_grid.addWidget(self._trend_chart, 0, 0)
        charts_grid.addWidget(self._hour_chart, 0, 1)
        charts_grid.addWidget(self._level_chart, 1, 0)
        charts_grid.addWidget(self._reason_chart, 1, 1)
        charts_grid.setColumnStretch(0, 1)
        charts_grid.setColumnStretch(1, 1)

        self._events_table = QTableWidget(self)
        self._events_table.setColumnCount(7)
        self._events_table.setHorizontalHeaderLabels(
            ["时间", "等级", "触发原因", "空闲(s)", "媒体", "关闭原因", "前台进程"]
        )
        self._events_table.horizontalHeader().setStretchLastSection(True)
        self._events_table.verticalHeader().setVisible(False)

        refresh_btn = QPushButton("刷新", self)
        refresh_btn.clicked.connect(self.refresh)

        header = QHBoxLayout()
        header.addWidget(self._today_count)
        header.addWidget(self._week_count)
        header.addStretch(1)
        header.addWidget(refresh_btn)

        layout = QVBoxLayout()
        layout.addLayout(header)
        layout.addLayout(charts_grid)
        layout.addWidget(QLabel("最近提醒事件"))
        layout.addWidget(self._events_table)
        self.setLayout(layout)

    def refresh(self) -> None:
        now = datetime.now()
        self._today_count.setText(f"今日提醒: {self._repo.get_today_count(now)}")

        trend_data = self._repo.get_last_n_days_counts(7, now)
        self._week_count.setText(f"近7天提醒: {sum(count for _, count in trend_data)}")
        self._trend_chart.setChart(self._build_trend_chart(trend_data))

        hour_data = self._repo.get_hourly_distribution(now)
        self._hour_chart.setChart(self._build_hour_chart(hour_data))

        level_data = self._repo.get_level_distribution(7, now)
        self._level_chart.setChart(
            self._build_pie_chart(
                "近7天提醒等级占比",
                level_data,
                {
                    "pre_reminder": "轻提醒",
                    "fullscreen_reminder": "强提醒",
                },
            )
        )

        reason_data = self._repo.get_trigger_reason_distribution(7, now)
        self._reason_chart.setChart(
            self._build_pie_chart(
                "近7天触发原因占比",
                reason_data,
                {
                    "idle_reached_pre_threshold": "达到轻提醒阈值",
                    "idle_reached_fullscreen_threshold": "达到强提醒阈值",
                    "cooldown_pre_reminder": "冷却期轻提醒",
                    "unknown": "未知",
                },
            )
        )

        rows = self._repo.get_recent_events(limit=100)
        self._events_table.setRowCount(len(rows))
        for idx, row in enumerate(rows):
            self._events_table.setItem(idx, 0, QTableWidgetItem(str(row.get("triggered_at", ""))))
            self._events_table.setItem(idx, 1, QTableWidgetItem(str(row.get("level", ""))))
            self._events_table.setItem(idx, 2, QTableWidgetItem(str(row.get("trigger_reason", ""))))
            self._events_table.setItem(idx, 3, QTableWidgetItem(str(row.get("idle_seconds", ""))))
            self._events_table.setItem(idx, 4, QTableWidgetItem(str(row.get("media_state", ""))))
            self._events_table.setItem(idx, 5, QTableWidgetItem(str(row.get("dismiss_reason", ""))))
            self._events_table.setItem(idx, 6, QTableWidgetItem(str(row.get("foreground_app", ""))))
        self._events_table.resizeColumnsToContents()

    def _build_trend_chart(self, points: list[tuple[str, int]]) -> QChart:
        series = QLineSeries()
        labels: list[str] = []
        max_count = 0
        for index, (label, count) in enumerate(points):
            labels.append(label)
            series.append(index, count)
            max_count = max(max_count, count)

        chart = QChart()
        chart.setTitle("最近 7 天提醒趋势")
        chart.addSeries(series)
        chart.legend().hide()

        axis_x = QBarCategoryAxis()
        axis_x.append(labels)
        axis_y = QValueAxis()
        axis_y.setRange(0, max(1, max_count + 1))
        axis_y.setLabelFormat("%d")
        axis_y.setTitleText("次数")
        axis_y.applyNiceNumbers()

        chart.addAxis(axis_x, Qt.AlignBottom)
        chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_x)
        series.attachAxis(axis_y)
        return chart

    def _build_hour_chart(self, points: list[tuple[str, int]]) -> QChart:
        bar_set = QBarSet("提醒次数")
        labels: list[str] = []
        max_count = 0
        for label, count in points:
            labels.append(label)
            bar_set.append(count)
            max_count = max(max_count, count)

        series = QBarSeries()
        series.append(bar_set)

        chart = QChart()
        chart.setTitle("今日 24 小时提醒分布")
        chart.addSeries(series)
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignBottom)

        axis_x = QBarCategoryAxis()
        axis_x.append(labels)
        axis_y = QValueAxis()
        axis_y.setRange(0, max(1, max_count + 1))
        axis_y.setLabelFormat("%d")
        axis_y.setTitleText("次数")
        axis_y.applyNiceNumbers()

        chart.addAxis(axis_x, Qt.AlignBottom)
        chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_x)
        series.attachAxis(axis_y)
        return chart

    def _build_pie_chart(
        self,
        title: str,
        points: list[tuple[str, int]],
        name_mapping: dict[str, str],
    ) -> QChart:
        series = QPieSeries()
        valid_points = [(key, value) for key, value in points if value > 0]
        if not valid_points:
            series.append("暂无数据", 1)
        else:
            for key, value in valid_points:
                label = name_mapping.get(key, key)
                series.append(f"{label} ({value})", value)
        series.setLabelsVisible(True)

        chart = QChart()
        chart.setTitle(title)
        chart.addSeries(series)
        chart.legend().setVisible(False)
        return chart
