"""Neumorphic building blocks for Focus Reminder PySide6 UI.

Palette aligned with the React prototype:
- BG:       #ECECEC
- TEXT:     #3A3A3A
- SUB:      #7A7A7A
- MUTED:    #A8A8A8
- ACCENT:   #3A3A3A
- DARK SHADOW:  #C9CFD6
- LIGHT SHADOW: #FFFFFF
"""
from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QPointF, QRectF, QSize, Qt, Signal
from PySide6.QtGui import (
    QColor,
    QFont,
    QIcon,
    QPainter,
    QPainterPath,
    QPen,
)
from PySide6.QtWidgets import (
    QAbstractSpinBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

BG = "#ECECEC"
TEXT = "#3A3A3A"
SUB = "#7A7A7A"
MUTED = "#A8A8A8"
ACCENT = "#3A3A3A"
SOFT = "#B4BCC4"
SHADOW_DARK = QColor(201, 207, 214)   # #C9CFD6
SHADOW_LIGHT = QColor(255, 255, 255)

# Global tuning knobs for real-device visual adjustment.
# If you need to tweak depth, start from these two numbers.
NEU_OUTSET_OFFSET = 10
NEU_OUTSET_BLUR_LAYERS = 6

# Secondary controls for smaller controls/buttons.
NEU_BUTTON_OFFSET = 5
NEU_BUTTON_BLUR_LAYERS = 5
NEU_ICON_OFFSET = 4
NEU_ICON_BLUR_LAYERS = 4
NEU_TINY_OFFSET = 3
NEU_TINY_BLUR_LAYERS = 3

FS_CAPS = 10
FS_TITLE = 13
FS_TEXT = 13
FS_VALUE = 14
FS_UNIT = 11
FS_STATUS = 11
FS_BRAND_TAG = 12
FS_BRAND_TITLE = 19


def _draw_neumorphic(
    painter: QPainter,
    rect: QRectF,
    radius: float,
    inset: bool = False,
    offset: int = NEU_OUTSET_OFFSET,
    blur_layers: int = NEU_OUTSET_BLUR_LAYERS,
) -> None:
    """Software-approximated neumorphism.

    Out-set: draws soft dark bottom-right + soft light top-left shadow halos
             around the rect, then the BG fill on top.
    In-set:  draws the BG fill, then paints translucent dark/light arcs
             along the top-left / bottom-right edges inside the rect.
    """
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

    bg = QColor(BG)
    path = QPainterPath()
    path.addRoundedRect(rect, radius, radius)

    if not inset:
        # Outer shadows — draw multiple offset copies with decreasing alpha.
        for i in range(blur_layers, 0, -1):
            alpha = int(18 + 10 * (i / blur_layers))
            # Dark (bottom-right)
            dark = QColor(SHADOW_DARK)
            dark.setAlpha(alpha)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(dark)
            painter.drawRoundedRect(
                rect.translated(offset * i / blur_layers, offset * i / blur_layers),
                radius, radius,
            )
            # Light (top-left)
            light = QColor(SHADOW_LIGHT)
            light.setAlpha(alpha)
            painter.setBrush(light)
            painter.drawRoundedRect(
                rect.translated(-offset * i / blur_layers, -offset * i / blur_layers),
                radius, radius,
            )
        # Fill body
        painter.setBrush(bg)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(rect, radius, radius)
    else:
        painter.setBrush(bg)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(rect, radius, radius)

        painter.save()
        painter.setClipPath(path)

        inner_radius = max(1.0, radius - 1.0)
        light = QColor(SHADOW_LIGHT)
        light.setAlpha(185)
        dark = QColor(SHADOW_DARK)
        dark.setAlpha(155)

        painter.setBrush(Qt.BrushStyle.NoBrush)
        pen_light = QPen(light)
        pen_light.setWidthF(1.4)
        painter.setPen(pen_light)
        painter.drawRoundedRect(
            QRectF(rect).adjusted(0.9, 0.9, -2.0, -2.0),
            inner_radius,
            inner_radius,
        )

        pen_dark = QPen(dark)
        pen_dark.setWidthF(1.4)
        painter.setPen(pen_dark)
        painter.drawRoundedRect(
            QRectF(rect).adjusted(2.0, 2.0, -0.9, -0.9),
            inner_radius,
            inner_radius,
        )
        painter.restore()


class NeumorphicCard(QWidget):
    def __init__(self, radius: int = 22, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._radius = radius
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)

    def paintEvent(self, event) -> None:  # noqa: D401
        del event
        painter = QPainter(self)
        margin = 10
        rect = QRectF(self.rect()).adjusted(margin, margin, -margin, -margin)
        _draw_neumorphic(painter, rect, self._radius, inset=False,
                         offset=NEU_OUTSET_OFFSET,
                         blur_layers=NEU_OUTSET_BLUR_LAYERS)


class NeumorphicInset(QWidget):
    def __init__(self, radius: int = 999, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._radius = radius

    def paintEvent(self, event) -> None:
        del event
        painter = QPainter(self)
        rect = QRectF(self.rect()).adjusted(0.7, 0.7, -0.7, -0.7)
        r = self._radius if self._radius < rect.height() / 2 else rect.height() / 2
        _draw_neumorphic(painter, rect, r, inset=True)


class CapsLabel(QLabel):
    def __init__(self, text: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(text.upper(), parent)
        self.setStyleSheet(
            f"color:{MUTED}; letter-spacing:3px; font-size:{FS_CAPS + 1}px; font-weight:400;"
        )


class SectionTitle(QWidget):
    def __init__(self, title: str, hint: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 8)
        lay.setSpacing(8)
        t = QLabel(title, self)
        t.setStyleSheet(f"color:{TEXT}; font-size:{FS_TITLE + 1}px; font-weight:700;")
        lay.addWidget(t)
        lay.addStretch(1)
        lay.addWidget(CapsLabel(hint, self))


class SmallPillButton(QPushButton):
    """Rounded outset neumorphic button (no QSS shadow — painted)."""

    def __init__(self, text: str = "", icon: Optional[QIcon] = None,
                 parent: Optional[QWidget] = None) -> None:
        super().__init__(text, parent)
        if icon is not None:
            self.setIcon(icon)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFlat(True)
        self.setStyleSheet(
            f"QPushButton{{border:none;background:transparent;color:{TEXT};"
            f"font-size:{FS_TEXT + 1}px;font-weight:400;padding:8px 18px;}}"
        )

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        rect = QRectF(self.rect()).adjusted(6, 6, -6, -6)
        r = rect.height() / 2
        _draw_neumorphic(
            painter,
            rect,
            r,
            inset=False,
            offset=NEU_BUTTON_OFFSET,
            blur_layers=NEU_BUTTON_BLUR_LAYERS,
        )
        painter.end()
        super().paintEvent(event)


class CircleIconButton(QToolButton):
    def __init__(self, icon: QIcon, tooltip: str = "",
                 parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setIcon(icon)
        self.setToolTip(tooltip)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(46, 46)
        self.setStyleSheet(
            f"QToolButton{{border:none;background:transparent;color:{SUB};}}"
        )

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        rect = QRectF(self.rect()).adjusted(4, 4, -4, -4)
        _draw_neumorphic(
            painter,
            rect,
            rect.height() / 2,
            inset=False,
            offset=NEU_ICON_OFFSET,
            blur_layers=NEU_ICON_BLUR_LAYERS,
        )
        painter.end()
        super().paintEvent(event)


def _draw_line_glyph(p: QPainter, rect: QRectF, kind: str, color: QColor) -> None:
    p.save()
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    pen = QPen(color)
    pen.setWidthF(1.6)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)

    if kind == "save":
        body = rect.adjusted(1.0, 1.0, -1.0, -1.0)
        p.drawRoundedRect(body, 2.0, 2.0)
        p.drawLine(body.left() + 2.0, body.top() + 5.0, body.right() - 2.0, body.top() + 5.0)
        p.drawRect(QRectF(body.left() + 3.2, body.top() + 2.0, 4.5, 2.2))
        p.drawLine(body.left() + 3.0, body.bottom() - 3.0, body.right() - 3.0, body.bottom() - 3.0)
    elif kind == "stats":
        x0, y0 = rect.left() + 1.0, rect.bottom() - 1.0
        p.drawLine(x0, rect.top() + 1.0, x0, y0)
        p.drawLine(x0, y0, rect.right() - 1.0, y0)
        p.drawLine(rect.left() + 4.0, y0, rect.left() + 4.0, rect.top() + 8.0)
        p.drawLine(rect.left() + 7.0, y0, rect.left() + 7.0, rect.top() + 5.0)
        p.drawLine(rect.left() + 10.0, y0, rect.left() + 10.0, rect.top() + 3.0)
    elif kind == "trash":
        body = QRectF(rect.left() + 2.0, rect.top() + 4.0, rect.width() - 4.0, rect.height() - 6.0)
        p.drawRoundedRect(body, 1.8, 1.8)
        p.drawLine(body.left() - 0.6, body.top() - 1.8, body.right() + 0.6, body.top() - 1.8)
        p.drawLine(body.center().x() - 3.0, body.top() - 3.2, body.center().x() + 3.0, body.top() - 3.2)
        p.drawLine(body.left() + 3.0, body.top() + 2.0, body.left() + 3.0, body.bottom() - 2.0)
        p.drawLine(body.center().x(), body.top() + 2.0, body.center().x(), body.bottom() - 2.0)
        p.drawLine(body.right() - 3.0, body.top() + 2.0, body.right() - 3.0, body.bottom() - 2.0)

    p.restore()


class LinePillButton(QPushButton):
    def __init__(
        self,
        text: str,
        glyph: str,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(text, parent)
        self._glyph = glyph
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(44)
        self.setMinimumWidth(148)
        self.setStyleSheet("QPushButton{border:none;background:transparent;}")

    def paintEvent(self, event) -> None:
        del event
        p = QPainter(self)
        rect = QRectF(self.rect()).adjusted(6, 6, -6, -6)
        _draw_neumorphic(
            p,
            rect,
            rect.height() / 2,
            inset=False,
            offset=NEU_BUTTON_OFFSET,
            blur_layers=NEU_BUTTON_BLUR_LAYERS,
        )

        glyph_rect = QRectF(rect.left() + 12, rect.center().y() - 7, 14, 14)
        _draw_line_glyph(p, glyph_rect, self._glyph, QColor(TEXT))

        p.setPen(QColor(TEXT))
        font = QFont(p.font())
        font.setPixelSize(FS_TEXT + 2)
        font.setWeight(QFont.Weight.Normal)
        p.setFont(font)
        text_rect = QRectF(glyph_rect.right() + 8, rect.top(), rect.width() - 30, rect.height())
        p.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, self.text())


class LineCircleButton(QToolButton):
    def __init__(self, glyph: str, tooltip: str = "", parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._glyph = glyph
        self.setToolTip(tooltip)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(46, 46)
        self.setStyleSheet("QToolButton{border:none;background:transparent;}")

    def paintEvent(self, event) -> None:
        del event
        p = QPainter(self)
        rect = QRectF(self.rect()).adjusted(4, 4, -4, -4)
        _draw_neumorphic(
            p,
            rect,
            rect.height() / 2,
            inset=False,
            offset=NEU_ICON_OFFSET,
            blur_layers=NEU_ICON_BLUR_LAYERS,
        )
        glyph_rect = QRectF(rect.center().x() - 7, rect.center().y() - 7, 14, 14)
        _draw_line_glyph(p, glyph_rect, self._glyph, QColor(SUB))


class ToggleSwitch(QWidget):
    toggled = Signal(bool)

    def __init__(self, checked: bool = False, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._checked = checked
        self.setFixedSize(44, 22)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def isChecked(self) -> bool:
        return self._checked

    def setChecked(self, value: bool) -> None:
        if value != self._checked:
            self._checked = bool(value)
            self.update()
            self.toggled.emit(self._checked)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.setChecked(not self._checked)

    def paintEvent(self, event) -> None:
        del event
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        # Track — inset
        _draw_neumorphic(p, rect, rect.height() / 2, inset=True)
        # Knob
        knob_size = rect.height() - 4
        x = rect.right() - knob_size - 2 if self._checked else rect.left() + 2
        y = rect.top() + 2
        knob = QRectF(x, y, knob_size, knob_size)
        _draw_neumorphic(p, knob, knob_size / 2, inset=False,
                         offset=NEU_TINY_OFFSET,
                         blur_layers=NEU_ICON_BLUR_LAYERS)
        if self._checked:
            p.setBrush(QColor(TEXT))
            p.setPen(Qt.PenStyle.NoPen)
            cx, cy = knob.center().x(), knob.center().y()
            p.drawEllipse(QPointF(cx, cy), 2, 2)


class _StepperSpin(QSpinBox):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.setFrame(False)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet(
            f"QSpinBox{{background:transparent;border:none;color:{TEXT};"
            f"font-size:{FS_VALUE + 1}px;font-weight:400;}}"
        )


class StepperField(QWidget):
    def __init__(self, label: str, unit: str, minimum: int, maximum: int,
                 step: int = 1, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(6)
        outer.addWidget(CapsLabel(label, self))

        track = NeumorphicInset(radius=999, parent=self)
        track.setFixedHeight(36)
        row = QHBoxLayout(track)
        row.setContentsMargins(6, 4, 6, 4)
        row.setSpacing(4)

        self._minus = self._circle_btn("−")
        self._plus = self._circle_btn("+")
        self._spin = _StepperSpin(track)
        self._spin.setRange(minimum, maximum)
        self._spin.setSingleStep(step)

        unit_lbl = QLabel(unit, track)
        unit_lbl.setStyleSheet(f"color:{MUTED}; font-size:{FS_UNIT + 1}px; font-weight:400;")

        center = QHBoxLayout()
        center.setContentsMargins(0, 0, 0, 0)
        center.setSpacing(4)
        center.addStretch(1)
        center.addWidget(self._spin)
        center.addWidget(unit_lbl)
        center.addStretch(1)

        row.addWidget(self._minus)
        row.addLayout(center, 1)
        row.addWidget(self._plus)
        outer.addWidget(track)

        self._minus.clicked.connect(lambda: self._spin.setValue(
            max(self._spin.minimum(), self._spin.value() - step)))
        self._plus.clicked.connect(lambda: self._spin.setValue(
            min(self._spin.maximum(), self._spin.value() + step)))

    def _circle_btn(self, text: str) -> QToolButton:
        btn = QToolButton(self)
        btn.setText(text)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFixedSize(24, 24)
        btn.setStyleSheet(
            f"QToolButton{{border:none;background:transparent;color:{SUB};"
            f"font-size:{FS_TEXT + 1}px;font-weight:400;}}"
        )

        def _paint(event, b=btn):
            p = QPainter(b)
            rect = QRectF(b.rect()).adjusted(1, 1, -1, -1)
            _draw_neumorphic(p, rect, rect.height() / 2,
                             inset=False,
                             offset=NEU_TINY_OFFSET,
                             blur_layers=NEU_TINY_BLUR_LAYERS)
            p.end()
            QToolButton.paintEvent(b, event)

        btn.paintEvent = _paint  # type: ignore[assignment]
        return btn

    def value(self) -> int:
        return self._spin.value()

    def setValue(self, value: int) -> None:
        self._spin.setValue(int(value))


class PillSelect(QWidget):
    currentIndexChanged = Signal(int)

    def __init__(self, items: list[tuple[str, object]],
                 parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        self._inset = NeumorphicInset(radius=999, parent=self)
        self._inset.setFixedHeight(36)
        inner = QHBoxLayout(self._inset)
        inner.setContentsMargins(14, 4, 14, 4)
        inner.setSpacing(6)

        self._combo = QComboBox(self._inset)
        self._combo.setStyleSheet(
            f"QComboBox{{background:transparent;border:none;color:{TEXT};"
            f"font-size:{FS_TEXT + 1}px;font-weight:400;}}"
            f"QComboBox::drop-down{{border:none;width:0;}}"
            f"QComboBox QAbstractItemView{{background:{BG};border:1px solid #D8DCE2;"
            f"selection-background-color:#DFE4EA;color:{TEXT};}}"
        )
        for label, data in items:
            self._combo.addItem(label, data)
        arrow = QLabel("▾", self._inset)
        arrow.setStyleSheet(f"color:{MUTED}; font-size:{FS_UNIT + 1}px; font-weight:400;")
        inner.addWidget(self._combo, 1)
        inner.addWidget(arrow)
        lay.addWidget(self._inset)
        self._combo.currentIndexChanged.connect(self.currentIndexChanged.emit)

    def currentData(self):
        return self._combo.currentData()

    def setCurrentIndex(self, idx: int) -> None:
        self._combo.setCurrentIndex(idx)


class PillLineEdit(QWidget):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        self._inset = NeumorphicInset(radius=999, parent=self)
        self._inset.setFixedHeight(36)
        inner = QHBoxLayout(self._inset)
        inner.setContentsMargins(14, 4, 14, 4)
        self._line = QLineEdit(self._inset)
        self._line.setStyleSheet(
            f"QLineEdit{{background:transparent;border:none;color:{SUB};"
            f"font-size:{FS_TEXT + 1}px;font-weight:400;}}"
        )
        inner.addWidget(self._line)
        lay.addWidget(self._inset)

    def text(self) -> str:
        return self._line.text()

    def setText(self, t: str) -> None:
        self._line.setText(t)


class LabeledToggle(QWidget):
    toggled = Signal(bool)

    def __init__(self, label: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 4, 0, 4)
        lay.setSpacing(10)
        self._label = QLabel(label, self)
        self._label.setStyleSheet(f"color:{TEXT}; font-size:{FS_TEXT + 1}px; font-weight:400;")
        self._switch = ToggleSwitch(parent=self)
        self._switch.toggled.connect(self.toggled.emit)
        lay.addWidget(self._label)
        lay.addStretch(1)
        lay.addWidget(self._switch)

    def isChecked(self) -> bool:
        return self._switch.isChecked()

    def setChecked(self, v: bool) -> None:
        self._switch.setChecked(v)


class TabPill(QWidget):
    """Two-button pill tab: 设置 / 统计."""

    activeTabChanged = Signal(str)  # 'settings' | 'statistics'

    def __init__(self, active: str = "settings",
                 parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._active = active
        self.setFixedSize(172, 38)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        self._inset = NeumorphicInset(radius=999, parent=self)
        inner = QHBoxLayout(self._inset)
        inner.setContentsMargins(4, 4, 4, 4)
        inner.setSpacing(4)
        self._settings = self._make_btn("设置", "settings")
        self._stats = self._make_btn("统计", "statistics")
        inner.addWidget(self._settings)
        inner.addWidget(self._stats)
        lay.addWidget(self._inset)
        self._refresh()

    def _make_btn(self, text: str, key: str) -> QPushButton:
        btn = QPushButton(text, self)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFlat(True)
        btn.setFixedHeight(30)
        btn.setMinimumWidth(72)
        btn.clicked.connect(lambda _=False, k=key: self._on_click(k))
        btn._key = key  # type: ignore[attr-defined]
        return btn

    def _on_click(self, key: str) -> None:
        if key != self._active:
            self._active = key
            self._refresh()
            self.activeTabChanged.emit(key)

    def _refresh(self) -> None:
        for btn in (self._settings, self._stats):
            key = btn._key  # type: ignore[attr-defined]
            if key == self._active:
                btn.setStyleSheet(
                    f"QPushButton{{border:none;border-radius:14px;background:{BG};"
                    f"color:{TEXT};font-size:{FS_TEXT + 1}px;font-weight:400;padding:0 14px;}}"
                )
                # add outset shadow via paintEvent
                def _paint(event, b=btn):
                    p = QPainter(b)
                    rect = QRectF(b.rect()).adjusted(2, 2, -2, -2)
                    _draw_neumorphic(p, rect, rect.height() / 2,
                                     inset=False,
                                     offset=NEU_TINY_OFFSET,
                                     blur_layers=NEU_TINY_BLUR_LAYERS)
                    p.end()
                    QPushButton.paintEvent(b, event)
                btn.paintEvent = _paint  # type: ignore[assignment]
            else:
                btn.setStyleSheet(
                    f"QPushButton{{border:none;background:transparent;"
                    f"color:{MUTED};font-size:{FS_TEXT + 1}px;font-weight:400;padding:0 14px;}}"
                    f"QPushButton:hover{{color:{SUB};}}"
                )
                btn.paintEvent = lambda e, b=btn: QPushButton.paintEvent(b, e)  # type: ignore[assignment]
            btn.update()


class BrandBlock(QWidget):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(2)
        tag = QLabel("FOCUS", self)
        tag.setStyleSheet(
            f"color:{MUTED}; font-size:{FS_BRAND_TAG + 1}px; letter-spacing:4px; font-weight:400;"
        )
        title = QLabel("Reminder", self)
        title.setStyleSheet(
            f"color:{TEXT}; font-size:{FS_BRAND_TITLE + 1}px; font-weight:400; letter-spacing:1px;"
        )
        lay.addWidget(tag)
        lay.addWidget(title)


def clamp_window_to_half_screen(widget: QWidget, max_w: int = 720,
                                max_h: int = 860,
                                lock_size: bool = True) -> None:
    from PySide6.QtGui import QGuiApplication
    screen = QGuiApplication.primaryScreen()
    if screen is None:
        w = min(max_w, 720)
        h = min(max_h, 800)
        if lock_size:
            widget.setFixedSize(w, h)
        else:
            widget.resize(w, h)
        return
    geo = screen.availableGeometry()
    w = min(max_w, geo.width() // 2)
    h = min(max_h, geo.height() // 2)
    if lock_size:
        widget.setFixedSize(w, h)
    else:
        widget.resize(w, h)


def root_stylesheet() -> str:
    return f"""
        QWidget#focusRoot, QWidget#focusContent {{
            background: {BG};
            color: {TEXT};
            font-size: {FS_TEXT + 1}px;
            font-weight: 400;
            font-family: "Source Han Sans SC", "Noto Sans CJK SC", "PingFang SC", "Microsoft YaHei UI", sans-serif;
        }}
        QScrollArea, QScrollArea > QWidget > QWidget {{
            background: {BG};
            border: none;
        }}
        QScrollBar:vertical {{
            background: transparent; width: 8px; margin: 0;
        }}
        QScrollBar::handle:vertical {{
            background: #D4D9E0; border-radius: 4px; min-height: 30px;
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0; background: transparent;
        }}
    """
