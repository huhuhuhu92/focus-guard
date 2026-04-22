"""Neumorphic statistics window — port of frontend/src/components/Statistics.tsx.

Signals preserved:
    open_settings_requested()

Data source: ReminderEventRepository (same as before; no backend changes).
"""
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
from PySide6.QtCore import QMargins, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from focus_reminder.infrastructure.storage.event_repository import (
    ReminderEventRepository,
)

from ._neumorphic import (
    ACCENT,
    BG,
    MUTED,
    SOFT,
    SUB,
    TEXT,
    BrandBlock,
    CapsLabel,
    NeumorphicCard,
    NeumorphicInset,
    SectionTitle,
    SmallPillButton,
    TabPill,
    root_stylesheet,
)

REASON_LABELS = {
    "idle_reached_pre_threshold": "达到轻提醒阈值",
    "idle_reached_fullscreen_threshold": "达到强提醒阈值",
    "cooldown_pre_reminder": "冷却期轻提醒",
    "auto": "自动关闭",
    "activity": "输入关闭",
    "manual": "手动关闭",
    "pending": "待关闭",
    "unknown": "未知",
}


def _reason_label(key: str) -> str:
    return REASON_LABELS.get(key, key)


class StatsWindow(QWidget):
    open_settings_requested = Signal()

    def __init__(self, repository: ReminderEventRepository) -> None:
        super().__init__()
        self._repo = repository
        self.setObjectName("focusRoot")
        self.setWindowTitle("Focus Reminder 统计")
        self.setFixedSize(760, 760)
        self.setStyleSheet(root_stylesheet())
        self._build_ui()

    # ------------------------------------------------------------- UI
    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        root.addWidget(scroll)

        content = QWidget(self)
        content.setObjectName("focusContent")
        scroll.setWidget(content)

        outer = QVBoxLayout(content)
        outer.setContentsMargins(24, 24, 24, 24)
        outer.setSpacing(16)

        header = QHBoxLayout()
        header.addWidget(BrandBlock(self))
        header.addStretch(1)
        tabs = TabPill("statistics", self)
        tabs.activeTabChanged.connect(self._on_tab_changed)
        header.addWidget(tabs)
        outer.addLayout(header)
        self._tabs = tabs

        grid = QGridLayout()
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(16)
        for c in range(6):
            grid.setColumnStretch(c, 1)

        hero_card = self._build_hero()
        trend_card = self._build_trend_card()
        level_card = self._build_level_card()
        hour_card = self._build_hour_card()
        reason_card = self._build_reason_card()
        events_card = self._build_events_card()

        self._lock_card_height(hero_card, 166)
        self._lock_card_height(trend_card, 236)
        self._lock_card_height(level_card, 236)
        self._lock_card_height(hour_card, 236)
        self._lock_card_height(reason_card, 236)
        self._lock_card_height(events_card, 304)

        grid.addWidget(hero_card, 0, 0, 1, 6)
        grid.addWidget(trend_card, 1, 0, 1, 4)
        grid.addWidget(level_card, 1, 4, 1, 2)
        grid.addWidget(hour_card, 2, 0, 1, 4)
        grid.addWidget(reason_card, 2, 4, 1, 2)
        grid.addWidget(events_card, 3, 0, 1, 6)
        outer.addLayout(grid)
        outer.addStretch(1)

    # ------------------------------------------------------ Sections --
    def _build_hero(self) -> NeumorphicCard:
        card = NeumorphicCard(radius=22)
        lay = QHBoxLayout(card)
        lay.setContentsMargins(28, 22, 28, 22)
        lay.setSpacing(28)

        today_box = QVBoxLayout()
        today_box.setSpacing(4)
        today_box.addWidget(CapsLabel("今日提醒", card))
        row = QHBoxLayout()
        row.setSpacing(4)
        self._today_count = QLabel("0", card)
        self._today_count.setStyleSheet(
            f"color:{TEXT}; font-size:40px; font-weight:300;"
        )
        unit = QLabel("次", card)
        unit.setStyleSheet(f"color:{MUTED}; font-size:11px;")
        row.addWidget(self._today_count)
        row.addWidget(unit, 0, Qt.AlignmentFlag.AlignBottom)
        row.addStretch(1)
        today_box.addLayout(row)

        week_box = QVBoxLayout()
        week_box.setSpacing(4)
        week_box.addWidget(CapsLabel("近 7 天提醒", card))
        self._week_count = QLabel("0", card)
        self._week_count.setStyleSheet(
            f"color:{TEXT}; font-size:20px; font-weight:400;"
        )
        week_box.addWidget(self._week_count)
        week_box.addStretch(1)

        lay.addLayout(today_box)
        lay.addLayout(week_box)
        lay.addStretch(1)

        refresh = SmallPillButton("刷新", parent=card)
        refresh.clicked.connect(self.refresh)
        lay.addWidget(refresh, 0, Qt.AlignmentFlag.AlignBottom)
        return card

    def _build_trend_card(self) -> NeumorphicCard:
        card = NeumorphicCard(radius=22)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(22, 20, 22, 20)
        lay.setSpacing(8)
        lay.addWidget(SectionTitle("最近 7 天提醒趋势", "7 DAYS", card))
        self._trend_chart = QChartView(card)
        self._trend_chart.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._trend_chart.setMinimumHeight(110)
        self._trend_chart.setStyleSheet("background: transparent; border: none;")
        lay.addWidget(self._trend_chart)
        return card

    def _build_level_card(self) -> NeumorphicCard:
        return self._build_pie_card("提醒等级占比", "LEVEL", "_level_chart",
                                    "_level_legend")

    def _build_reason_card(self) -> NeumorphicCard:
        return self._build_pie_card("触发原因占比", "REASON", "_reason_chart",
                                    "_reason_legend")

    def _build_pie_card(self, title: str, hint: str,
                        chart_attr: str, legend_attr: str) -> NeumorphicCard:
        card = NeumorphicCard(radius=22)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(22, 20, 22, 20)
        lay.setSpacing(10)
        lay.addWidget(SectionTitle(title, hint, card))
        row = QHBoxLayout()
        row.setSpacing(12)
        chart = QChartView(card)
        chart.setRenderHint(QPainter.RenderHint.Antialiasing)
        chart.setFixedSize(72, 72)
        chart.setStyleSheet("background: transparent; border: none;")
        setattr(self, chart_attr, chart)
        row.addWidget(chart)
        legend = QVBoxLayout()
        legend.setSpacing(4)
        legend_wrap = QWidget(card)
        legend_wrap.setLayout(legend)
        setattr(self, legend_attr, legend)
        row.addWidget(legend_wrap, 1)
        lay.addLayout(row)
        lay.addStretch(1)
        return card

    def _build_hour_card(self) -> NeumorphicCard:
        card = NeumorphicCard(radius=22)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(22, 20, 22, 20)
        lay.setSpacing(8)
        lay.addWidget(SectionTitle("今日 24 小时提醒分布", "TODAY", card))
        self._hour_chart = QChartView(card)
        self._hour_chart.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._hour_chart.setMinimumHeight(110)
        self._hour_chart.setStyleSheet("background: transparent; border: none;")
        lay.addWidget(self._hour_chart)
        return card

    def _build_events_card(self) -> NeumorphicCard:
        card = NeumorphicCard(radius=22)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(22, 20, 22, 20)
        lay.setSpacing(10)
        lay.addWidget(SectionTitle("最近提醒事件", "RECENT", card))

        inset = NeumorphicInset(radius=14, parent=card)
        inset.setMinimumHeight(200)
        inset_lay = QVBoxLayout(inset)
        inset_lay.setContentsMargins(8, 8, 8, 8)
        inset_lay.setSpacing(0)

        self._events_table = QTableWidget(inset)
        self._events_table.setColumnCount(7)
        self._events_table.setHorizontalHeaderLabels(
            ["时间", "等级", "触发", "空闲", "媒体", "关闭", "前台进程"]
        )
        h = self._events_table.horizontalHeader()
        h.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        h.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self._events_table.verticalHeader().setVisible(False)
        self._events_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self._events_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self._events_table.setShowGrid(False)
        self._events_table.setAlternatingRowColors(False)
        self._events_table.setStyleSheet(
            f"QTableWidget{{background:transparent;border:none;color:{TEXT};"
            f"font-size:11px;gridline-color:transparent;}}"
            f"QHeaderView::section{{background:transparent;border:none;"
            f"color:{MUTED};font-size:9px;letter-spacing:2px;padding:6px 4px;}}"
            f"QTableWidget::item{{border:none;padding:6px 4px;}}"
            f"QTableWidget::item:selected{{background:rgba(0,0,0,0.04);"
            f"color:{TEXT};}}"
        )
        inset_lay.addWidget(self._events_table)
        lay.addWidget(inset)
        return card

    # ----------------------------------------------------- Refresh ----
    def _on_tab_changed(self, key: str) -> None:
        if key == "settings":
            self.open_settings_requested.emit()
            self._tabs._active = "statistics"
            self._tabs._refresh()

    def refresh(self) -> None:
        now = datetime.now()
        self._today_count.setText(str(self._repo.get_today_count(now)))

        trend = self._repo.get_last_n_days_counts(7, now)
        self._week_count.setText(str(sum(c for _, c in trend)))
        self._trend_chart.setChart(self._build_trend_chart(trend))

        self._hour_chart.setChart(
            self._build_hour_chart(self._repo.get_hourly_distribution(now))
        )

        level = self._repo.get_level_distribution(7, now)
        strong = next((v for k, v in level if k == "fullscreen_reminder"), 0)
        light = next((v for k, v in level if k == "pre_reminder"), 0)
        self._set_pie(self._level_chart, self._level_legend, [
            ("强提醒", strong, ACCENT),
            ("轻提醒", light, SOFT),
        ])

        # Use repository-level aggregation directly for consistency with API.
        reason_items = [
            (_reason_label(key), count)
            for key, count in self._repo.get_trigger_reason_distribution(7, now)
        ]
        palette = [ACCENT, SOFT]
        self._set_pie(self._reason_chart, self._reason_legend, [
            (name, count, palette[i % 2])
            for i, (name, count) in enumerate(reason_items)
        ])

        rows = self._repo.get_recent_events(limit=100)
        self._fill_events_table(rows)

    def _fill_events_table(self, rows: list[dict]) -> None:
        self._events_table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            self._events_table.setItem(i, 0, QTableWidgetItem(
                self._fmt_time(str(row.get("triggered_at", "")))))
            level_key = str(row.get("level", ""))
            lvl_item = QTableWidgetItem(
                "强" if level_key == "fullscreen_reminder" else "轻"
            )
            self._events_table.setItem(i, 1, lvl_item)
            self._events_table.setItem(i, 2, QTableWidgetItem(
                _reason_label(str(row.get("trigger_reason") or "unknown"))))
            idle = row.get("idle_seconds")
            self._events_table.setItem(i, 3, QTableWidgetItem(
                f"{idle}s" if idle not in (None, "") else "-"))
            self._events_table.setItem(i, 4, QTableWidgetItem(
                str(row.get("media_state") or "-")))
            self._events_table.setItem(i, 5, QTableWidgetItem(
                _reason_label(str(row.get("dismiss_reason") or "pending"))))
            self._events_table.setItem(i, 6, QTableWidgetItem(
                str(row.get("foreground_app") or "-")))
        self._events_table.resizeRowsToContents()

    # ------------------------------------------------------ Charts ----
    def _build_trend_chart(self, points: list[tuple[str, int]]) -> QChart:
        series = QLineSeries()
        pen = QPen(QColor(ACCENT))
        pen.setWidthF(1.8)
        series.setPen(pen)
        series.setPointsVisible(True)
        series.setMarkerSize(6)

        labels: list[str] = []
        max_count = 0
        for i, (label, count) in enumerate(points):
            labels.append(label)
            series.append(i, count)
            max_count = max(max_count, count)

        chart = _transparent_chart()
        chart.addSeries(series)

        ax = QBarCategoryAxis()
        ax.append(labels)
        ax.setLabelsColor(QColor(MUTED))
        ax.setGridLineVisible(False)
        ax.setLineVisible(False)
        ay = QValueAxis()
        ay.setRange(0, max(1, max_count + 1))
        ay.setVisible(False)
        chart.addAxis(ax, Qt.AlignmentFlag.AlignBottom)
        chart.addAxis(ay, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(ax)
        series.attachAxis(ay)
        return chart

    def _build_hour_chart(self, points: list[tuple[str, int]]) -> QChart:
        bar = QBarSet("count")
        bar.setColor(QColor(ACCENT))
        labels: list[str] = []
        max_count = 0
        for i, (_, count) in enumerate(points):
            labels.append(f"{i:02d}h" if i % 3 == 0 else "")
            bar.append(count)
            max_count = max(max_count, count)
        series = QBarSeries()
        series.append(bar)
        series.setBarWidth(0.6)

        chart = _transparent_chart()
        chart.addSeries(series)
        ax = QBarCategoryAxis()
        ax.append(labels)
        ax.setLabelsColor(QColor(MUTED))
        ax.setGridLineVisible(False)
        ax.setLineVisible(False)
        ay = QValueAxis()
        ay.setRange(0, max(1, max_count + 1))
        ay.setVisible(False)
        chart.addAxis(ax, Qt.AlignmentFlag.AlignBottom)
        chart.addAxis(ay, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(ax)
        series.attachAxis(ay)
        return chart

    def _set_pie(self, chart_view: QChartView, legend_layout: QVBoxLayout,
                 items: list[tuple[str, int, str]]) -> None:
        # Clear legend
        while legend_layout.count():
            it = legend_layout.takeAt(0)
            w = it.widget()
            if w is not None:
                w.deleteLater()

        series = QPieSeries()
        series.setHoleSize(0.55)
        series.setPieSize(0.82)
        series.setLabelsVisible(False)
        total = sum(v for _, v, _ in items)
        if total <= 0:
            ph = series.append("empty", 1)
            ph.setColor(QColor("#D4D9E0"))
            empty = QLabel("暂无数据")
            empty.setStyleSheet(f"color:{MUTED}; font-size:11px;")
            legend_layout.addWidget(empty)
        else:
            for name, count, color in items:
                if count <= 0:
                    continue
                s = series.append(name, count)
                s.setColor(QColor(color))
                legend_layout.addWidget(self._legend_row(name, count, color))
        legend_layout.addStretch(1)

        chart = _transparent_chart()
        chart.addSeries(series)
        chart_view.setChart(chart)

    def _legend_row(self, name: str, count: int, color: str) -> QWidget:
        w = QWidget()
        lay = QHBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(6)
        dot = QLabel("●", w)
        dot.setStyleSheet(f"color:{color}; font-size:10px;")
        lbl = QLabel(name, w)
        lbl.setStyleSheet(f"color:{SUB}; font-size:11px;")
        cnt = QLabel(str(count), w)
        cnt.setStyleSheet(f"color:{MUTED}; font-size:11px;")
        lay.addWidget(dot)
        lay.addWidget(lbl, 1)
        lay.addWidget(cnt)
        return w

    def _lock_card_height(self, card: NeumorphicCard, height: int) -> None:
        card.setMinimumHeight(height)
        card.setMaximumHeight(height)

    # ------------------------------------------------------ Utils -----
    def _fmt_time(self, raw: str) -> str:
        try:
            return datetime.fromisoformat(raw).strftime("%H:%M:%S")
        except ValueError:
            return raw


def _transparent_chart() -> QChart:
    chart = QChart()
    chart.setBackgroundVisible(False)
    chart.setMargins(QMargins(0, 0, 0, 0))
    chart.layout().setContentsMargins(0, 0, 0, 0)
    chart.legend().hide()
    return chart
