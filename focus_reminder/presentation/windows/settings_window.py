from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from focus_reminder.domain.enums.dismiss_mode import DismissMode
from focus_reminder.domain.models.config import FocusConfig


class SettingsWindow(QWidget):
    config_saved = Signal(FocusConfig)
    clear_history_requested = Signal()
    open_stats_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Focus Reminder 设置")
        self.resize(640, 560)
        self._build_ui()

    def _build_ui(self) -> None:
        self._idle_minutes = QSpinBox(self)
        self._idle_minutes.setRange(1, 180)

        self._enable_pre = QCheckBox("启用轻提醒", self)
        self._pre_seconds = QSpinBox(self)
        self._pre_seconds.setRange(0, 600)

        self._cooldown_seconds = QSpinBox(self)
        self._cooldown_seconds.setRange(0, 3600)

        self._dismiss_mode = QComboBox(self)
        self._dismiss_mode.addItem("检测到输入即关闭", DismissMode.ACTIVITY.value)
        self._dismiss_mode.addItem("必须手动点击关闭", DismissMode.MANUAL.value)

        self._fullscreen_topmost = QCheckBox("强提醒置顶", self)
        self._fullscreen_overlay = QCheckBox("强提醒全屏遮罩", self)

        self._enable_history = QCheckBox("记录提醒历史", self)
        self._monitor_enabled = QCheckBox("启动监控", self)
        self._start_minimized = QCheckBox("启动最小化到托盘", self)

        self._poll_interval = QSpinBox(self)
        self._poll_interval.setRange(250, 5000)
        self._poll_interval.setSingleStep(250)

        self._pre_message = QLineEdit(self)
        self._fullscreen_message = QLineEdit(self)

        base_form = QFormLayout()
        base_form.addRow("强提醒阈值(分钟)", self._idle_minutes)
        base_form.addRow(self._enable_pre)
        base_form.addRow("轻提醒提前(秒)", self._pre_seconds)
        base_form.addRow("冷却时间(秒)", self._cooldown_seconds)
        base_form.addRow("检查周期(ms)", self._poll_interval)
        base_group = QGroupBox("基础设置", self)
        base_group.setLayout(base_form)

        behavior_form = QFormLayout()
        behavior_form.addRow("强提醒关闭方式", self._dismiss_mode)
        behavior_form.addRow(self._fullscreen_topmost)
        behavior_form.addRow(self._fullscreen_overlay)
        behavior_form.addRow("轻提醒文案", self._pre_message)
        behavior_form.addRow("强提醒文案", self._fullscreen_message)
        behavior_group = QGroupBox("提醒行为", self)
        behavior_group.setLayout(behavior_form)

        data_form = QFormLayout()
        data_form.addRow(self._enable_history)
        data_form.addRow(self._monitor_enabled)
        data_form.addRow(self._start_minimized)
        data_group = QGroupBox("数据与运行", self)
        data_group.setLayout(data_form)

        self._status_label = QLabel("", self)
        self._status_label.setStyleSheet("color: #2b579a;")

        save_btn = QPushButton("保存配置", self)
        save_btn.clicked.connect(self._on_save)

        stats_btn = QPushButton("查看统计", self)
        stats_btn.clicked.connect(self.open_stats_requested.emit)

        clear_btn = QPushButton("清空历史", self)
        clear_btn.clicked.connect(self.clear_history_requested.emit)

        btn_row = QHBoxLayout()
        btn_row.addWidget(save_btn)
        btn_row.addWidget(stats_btn)
        btn_row.addWidget(clear_btn)
        btn_row.addStretch(1)

        layout = QVBoxLayout()
        layout.addWidget(base_group)
        layout.addWidget(behavior_group)
        layout.addWidget(data_group)
        layout.addLayout(btn_row)
        layout.addWidget(self._status_label)
        layout.addStretch(1)
        self.setLayout(layout)

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
        self._status_label.setText("配置已加载")

    def _on_save(self) -> None:
        selected_mode = DismissMode(self._dismiss_mode.currentData())
        cfg = FocusConfig(
            idle_threshold_seconds=self._idle_minutes.value() * 60,
            pre_reminder_seconds=self._pre_seconds.value(),
            enable_pre_reminder=self._enable_pre.isChecked(),
            cooldown_seconds=self._cooldown_seconds.value(),
            dismiss_mode=selected_mode,
            enable_history=self._enable_history.isChecked(),
            monitor_enabled=self._monitor_enabled.isChecked(),
            poll_interval_ms=self._poll_interval.value(),
            pre_reminder_message=self._pre_message.text().strip(),
            fullscreen_message=self._fullscreen_message.text().strip(),
            fullscreen_topmost=self._fullscreen_topmost.isChecked(),
            fullscreen_overlay=self._fullscreen_overlay.isChecked(),
            start_minimized_to_tray=self._start_minimized.isChecked(),
        ).sanitized()
        self._status_label.setText("配置已保存")
        self.config_saved.emit(cfg)

