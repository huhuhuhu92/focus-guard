"""Neumorphic settings window — 1:1 port of frontend/src/components/Settings.tsx.

Signals preserved (bootstrap.py requires them):
    config_saved(FocusConfig)
    clear_history_requested()
    open_stats_requested()
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from focus_reminder.domain.enums.dismiss_mode import DismissMode
from focus_reminder.domain.models.config import FocusConfig

from ._neumorphic import (
    FS_STATUS,
    MUTED,
    TEXT,
    BrandBlock,
    LabeledToggle,
    LineCircleButton,
    LinePillButton,
    NeumorphicCard,
    PillLineEdit,
    PillSelect,
    SectionTitle,
    StepperField,
    TabPill,
    root_stylesheet,
)


class SettingsWindow(QWidget):
    config_saved = Signal(FocusConfig)
    clear_history_requested = Signal()
    open_stats_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("focusRoot")
        self.setWindowTitle("Focus Reminder 设置")
        self.setFixedSize(760, 760)
        self.setStyleSheet(root_stylesheet())
        self._build_ui()

    # ------------------------------------------------------------------ UI
    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        content = QWidget(self)
        content.setObjectName("focusContent")
        root.addWidget(content)

        outer = QVBoxLayout(content)
        outer.setContentsMargins(24, 24, 24, 24)
        outer.setSpacing(14)

        # ---- Header: brand + tabs --------------------------------------
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.addWidget(BrandBlock(self))
        header.addStretch(1)
        tabs = TabPill("settings", self)
        tabs.activeTabChanged.connect(self._on_tab_changed)
        header.addWidget(tabs)
        outer.addLayout(header)
        self._tabs = tabs

        # ---- Grid: 6-column mimicking Tailwind md:grid-cols-6 ----------
        grid = QGridLayout()
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(16)
        for col in range(6):
            grid.setColumnStretch(col, 1)

        # Row 0: base(4) + run(2)
        base_card = self._build_base_card()
        run_card = self._build_run_card()
        self._lock_card_height(base_card, 290)
        self._lock_card_height(run_card, 290)
        grid.addWidget(base_card, 0, 0, 1, 4)
        grid.addWidget(run_card, 0, 4, 1, 2)

        # Row 1: behavior(3) + copy(3)
        behavior_card = self._build_behavior_card()
        copy_card = self._build_copy_card()
        self._lock_card_height(behavior_card, 246)
        self._lock_card_height(copy_card, 246)
        grid.addWidget(behavior_card, 1, 0, 1, 3)
        grid.addWidget(copy_card, 1, 3, 1, 3)

        outer.addLayout(grid)
        outer.addLayout(self._build_footer())
        outer.addStretch(1)

    # ---------------------- Cards ---------------------------------------
    def _build_base_card(self) -> NeumorphicCard:
        card = NeumorphicCard(radius=22)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(24, 22, 24, 22)
        lay.setSpacing(14)
        lay.addWidget(SectionTitle("基础设置", "THRESHOLD", card))

        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(12)

        self._idle_minutes = StepperField("强提醒阈值", "分钟", 1, 180, 1, card)
        self._pre_seconds = StepperField("轻提醒提前", "秒", 0, 600, 5, card)
        self._cooldown_seconds = StepperField("冷却时间", "秒", 0, 3600, 5, card)
        self._poll_interval = StepperField("检查周期", "ms", 250, 5000, 100, card)

        grid.addWidget(self._idle_minutes, 0, 0)
        grid.addWidget(self._pre_seconds, 0, 1)
        grid.addWidget(self._cooldown_seconds, 1, 0)
        grid.addWidget(self._poll_interval, 1, 1)
        lay.addLayout(grid)

        spacer = QFrame(card)
        spacer.setFixedHeight(1)
        spacer.setStyleSheet("background: rgba(0,0,0,0.04);")
        lay.addSpacing(4)
        lay.addWidget(spacer)

        self._enable_pre = LabeledToggle("启用轻提醒", card)
        lay.addWidget(self._enable_pre)
        lay.addStretch(1)
        return card

    def _build_run_card(self) -> NeumorphicCard:
        card = NeumorphicCard(radius=22)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(24, 22, 24, 22)
        lay.setSpacing(14)
        lay.addWidget(SectionTitle("数据与运行", "RUN", card))
        self._monitor_enabled = LabeledToggle("启动监控", card)
        self._start_minimized = LabeledToggle("最小化到托盘", card)
        self._enable_history = LabeledToggle("记录提醒历史", card)
        lay.addWidget(self._monitor_enabled)
        lay.addWidget(self._start_minimized)
        lay.addWidget(self._enable_history)
        lay.addStretch(1)
        return card

    def _build_behavior_card(self) -> NeumorphicCard:
        card = NeumorphicCard(radius=22)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(24, 22, 24, 22)
        lay.setSpacing(14)
        lay.addWidget(SectionTitle("提醒行为", "ALERT", card))

        dismiss_wrap = QVBoxLayout()
        dismiss_wrap.setContentsMargins(0, 0, 0, 0)
        dismiss_wrap.setSpacing(6)
        from ._neumorphic import CapsLabel
        dismiss_wrap.addWidget(CapsLabel("强提醒关闭方式", card))
        self._dismiss_mode = PillSelect(
            [
                ("检测到输入即关闭", DismissMode.ACTIVITY.value),
                ("手动关闭", DismissMode.MANUAL.value),
            ],
            card,
        )
        dismiss_wrap.addWidget(self._dismiss_mode)
        lay.addLayout(dismiss_wrap)

        self._fullscreen_topmost = LabeledToggle("强提醒置顶", card)
        self._fullscreen_overlay = LabeledToggle("强提醒全屏遮罩", card)
        lay.addWidget(self._fullscreen_topmost)
        lay.addWidget(self._fullscreen_overlay)
        lay.addStretch(1)
        return card

    def _build_copy_card(self) -> NeumorphicCard:
        card = NeumorphicCard(radius=22)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(24, 22, 24, 22)
        lay.setSpacing(14)
        lay.addWidget(SectionTitle("提醒文案", "COPY", card))

        from ._neumorphic import CapsLabel
        for label_text, attr in (
            ("轻提醒文案", "_pre_message"),
            ("强提醒文案", "_fullscreen_message"),
        ):
            box = QVBoxLayout()
            box.setContentsMargins(0, 0, 0, 0)
            box.setSpacing(6)
            box.addWidget(CapsLabel(label_text, card))
            field = PillLineEdit(card)
            setattr(self, attr, field)
            box.addWidget(field)
            lay.addLayout(box)
        lay.addStretch(1)
        return card

    def _build_footer(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setContentsMargins(6, 0, 6, 0)
        row.setSpacing(10)

        self._status_dot = QLabel("●", self)
        self._status_dot.setStyleSheet(f"color:{TEXT}; font-size:{FS_STATUS + 1}px;")
        self._status_label = QLabel("加载中...", self)
        self._status_label.setStyleSheet(
            f"color:{MUTED}; font-size:{FS_STATUS + 1}px; font-weight:400; letter-spacing:2px;"
        )
        row.addWidget(self._status_dot)
        row.addWidget(self._status_label)
        row.addStretch(1)

        save_btn = LinePillButton("保存配置", "save", self)
        save_btn.clicked.connect(self._on_save)
        row.addWidget(save_btn)

        stats_btn = LineCircleButton("stats", "查看统计", self)
        stats_btn.clicked.connect(self.open_stats_requested.emit)
        row.addWidget(stats_btn)

        clear_btn = LineCircleButton("trash", "清空历史", self)
        clear_btn.clicked.connect(self.clear_history_requested.emit)
        row.addWidget(clear_btn)
        return row

    def _lock_card_height(self, card: NeumorphicCard, height: int) -> None:
        card.setMinimumHeight(height)
        card.setMaximumHeight(height)

    # ------------------------------------------------------- Logic -----
    def _on_tab_changed(self, key: str) -> None:
        if key == "statistics":
            self.open_stats_requested.emit()
            self._tabs._active = "settings"
            self._tabs._refresh()

    def load_config(self, config: FocusConfig) -> None:
        self._idle_minutes.setValue(max(1, config.idle_threshold_seconds // 60))
        self._enable_pre.setChecked(config.enable_pre_reminder)
        self._pre_seconds.setValue(config.pre_reminder_seconds)
        self._cooldown_seconds.setValue(config.cooldown_seconds)
        self._dismiss_mode.setCurrentIndex(
            0 if config.dismiss_mode == DismissMode.ACTIVITY else 1
        )
        self._fullscreen_topmost.setChecked(config.fullscreen_topmost)
        self._fullscreen_overlay.setChecked(config.fullscreen_overlay)
        self._enable_history.setChecked(config.enable_history)
        self._monitor_enabled.setChecked(config.monitor_enabled)
        self._poll_interval.setValue(config.poll_interval_ms)
        self._start_minimized.setChecked(config.start_minimized_to_tray)
        self._pre_message.setText(config.pre_reminder_message)
        self._fullscreen_message.setText(config.fullscreen_message)
        self._set_status("配置已加载")

    def _on_save(self) -> None:
        mode = DismissMode(self._dismiss_mode.currentData())
        cfg = FocusConfig(
            idle_threshold_seconds=self._idle_minutes.value() * 60,
            pre_reminder_seconds=self._pre_seconds.value(),
            enable_pre_reminder=self._enable_pre.isChecked(),
            cooldown_seconds=self._cooldown_seconds.value(),
            dismiss_mode=mode,
            enable_history=self._enable_history.isChecked(),
            monitor_enabled=self._monitor_enabled.isChecked(),
            poll_interval_ms=self._poll_interval.value(),
            pre_reminder_message=self._pre_message.text().strip(),
            fullscreen_message=self._fullscreen_message.text().strip(),
            fullscreen_topmost=self._fullscreen_topmost.isChecked(),
            fullscreen_overlay=self._fullscreen_overlay.isChecked(),
            start_minimized_to_tray=self._start_minimized.isChecked(),
        ).sanitized()
        self._set_status("配置已保存")
        self.config_saved.emit(cfg)

    def _set_status(self, text: str) -> None:
        self._status_label.setText(text)
