import configparser
from PyQt6.QtCore import Qt, QSize, QTimer
from PyQt6.QtGui import QColor, QPainter, QPainterPath, QLinearGradient, QBrush, QPen, QFont
from PyQt6.QtWidgets import QHBoxLayout, QWidget
from utils.paths import LAUNCHER_CONFIG


class VersionLabel(QWidget):
    def __init__(self, version, parent=None):
        super().__init__(parent)
        self._version = f"v{version}"
        self.setFixedHeight(24)
        self.setFixedWidth(self._calculate_width())

    def _calculate_width(self):
        font = QFont("Segoe UI", 9)
        font.setWeight(QFont.Weight.DemiBold)
        from PyQt6.QtGui import QFontMetrics
        metrics = QFontMetrics(font)
        return metrics.horizontalAdvance(self._version) + 24

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        bg = QPainterPath()
        bg.addRoundedRect(0, 0, self.width(), self.height(), 12, 12)
        p.setBrush(QBrush(QColor(30, 27, 46, 120)))
        p.setPen(QPen(QColor(42, 37, 64, 80), 1))
        p.drawPath(bg)

        font = QFont("Segoe UI", 9)
        font.setWeight(QFont.Weight.DemiBold)
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 0.8)
        p.setFont(font)
        p.setPen(QColor("#2D537A"))
        p.drawText(0, 0, self.width(), self.height(), Qt.AlignmentFlag.AlignCenter, self._version)

        p.end()


class HeartbeatDot(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(20, 24)
        self._pulse = 0
        self._direction = 1
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)
        self._timer.start(50)
        self.setToolTip("Update check active — runs every 15 minutes")

    def _animate(self):
        self._pulse += self._direction * 2
        if self._pulse >= 100:
            self._direction = -1
        elif self._pulse <= 0:
            self._direction = 1
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        cx, cy = 10, 12
        pulse_factor = self._pulse / 100.0

        from PyQt6.QtGui import QRadialGradient
        glow = QRadialGradient(cx, cy, 8)
        glow.setColorAt(0.0, QColor(29, 101, 216, int(15 + pulse_factor * 25)))
        glow.setColorAt(1.0, QColor(29, 101, 216, 0))
        p.setBrush(QBrush(glow))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(cx - 8, cy - 8, 16, 16)

        size = 4 + pulse_factor * 1.5
        p.setBrush(QBrush(QColor(29, 101, 216, int(80 + pulse_factor * 80))))
        p.drawEllipse(int(cx - size / 2), int(cy - size / 2), int(size), int(size))

        p.end()


class BrandLabel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(24)
        self._text = "Mission Helper"
        self.setFixedWidth(self._calculate_width())

    def _calculate_width(self):
        font = QFont("Segoe UI", 9)
        font.setWeight(QFont.Weight.Medium)
        from PyQt6.QtGui import QFontMetrics
        metrics = QFontMetrics(font)
        return metrics.horizontalAdvance(self._text) + 8

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        font = QFont("Segoe UI", 9)
        font.setWeight(QFont.Weight.Medium)
        p.setFont(font)

        gradient = QLinearGradient(0, 0, self.width(), 0)
        gradient.setColorAt(0.0, QColor("#1D3B5B"))
        gradient.setColorAt(1.0, QColor("#102640"))
        p.setPen(QPen(QBrush(gradient), 1))
        p.drawText(0, 0, self.width(), self.height(), Qt.AlignmentFlag.AlignCenter, self._text)

        p.end()


class SeparatorDot(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(8, 24)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setBrush(QBrush(QColor("#102640")))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(2, 10, 3, 3)
        p.end()


class VersionBar(QHBoxLayout):
    def __init__(self, parent):
        super().__init__()
        self.setContentsMargins(12, 2, 12, 6)
        self.setSpacing(6)

        config = configparser.ConfigParser()
        config.read(LAUNCHER_CONFIG, encoding="utf-8")
        version = config.get("Launcher", "version", fallback="0.0.0")

        brand = BrandLabel()
        self.addWidget(brand)

        sep = SeparatorDot()
        self.addWidget(sep)

        version_label = VersionLabel(version)
        self.addWidget(version_label)

        self.addStretch()

        heartbeat = HeartbeatDot()
        self.addWidget(heartbeat)
