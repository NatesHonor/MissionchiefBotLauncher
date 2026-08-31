from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPainter, QPainterPath, QLinearGradient, QBrush, QPen, QRadialGradient
from PyQt6.QtWidgets import QFrame


class GlassFrame(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setStyleSheet("background: transparent; border: none;")

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        main_bg = QPainterPath()
        main_bg.addRoundedRect(0, 0, self.width(), self.height(), 16, 16)
        p.setBrush(QBrush(QColor("#07111F")))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawPath(main_bg)

        border_gradient = QLinearGradient(0, 0, self.width(), self.height())
        border_gradient.setColorAt(0.0, QColor(29, 101, 216, 40))
        border_gradient.setColorAt(0.25, QColor(29, 59, 91, 60))
        border_gradient.setColorAt(0.5, QColor(37, 131, 232, 30))
        border_gradient.setColorAt(0.75, QColor(29, 59, 91, 60))
        border_gradient.setColorAt(1.0, QColor(33, 184, 212, 35))

        border_path = QPainterPath()
        border_path.addRoundedRect(0, 0, self.width(), self.height(), 16, 16)
        inner_path = QPainterPath()
        inner_path.addRoundedRect(1, 1, self.width() - 2, self.height() - 2, 15.5, 15.5)
        border_only = border_path - inner_path

        p.setBrush(QBrush(border_gradient))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawPath(border_only)

        glow_tl = QRadialGradient(self.width() * 0.1, self.height() * 0.05, self.width() * 0.4)
        glow_tl.setColorAt(0.0, QColor(29, 101, 216, 6))
        glow_tl.setColorAt(0.5, QColor(29, 101, 216, 2))
        glow_tl.setColorAt(1.0, QColor(29, 101, 216, 0))
        p.setBrush(QBrush(glow_tl))
        p.setPen(Qt.PenStyle.NoPen)
        p.setClipPath(main_bg)
        p.drawEllipse(
            int(self.width() * 0.1 - self.width() * 0.4),
            int(self.height() * 0.05 - self.width() * 0.4),
            int(self.width() * 0.8),
            int(self.width() * 0.8)
        )

        glow_br = QRadialGradient(self.width() * 0.9, self.height() * 0.9, self.width() * 0.35)
        glow_br.setColorAt(0.0, QColor(33, 184, 212, 4))
        glow_br.setColorAt(0.5, QColor(33, 184, 212, 1))
        glow_br.setColorAt(1.0, QColor(33, 184, 212, 0))
        p.setBrush(QBrush(glow_br))
        p.drawEllipse(
            int(self.width() * 0.9 - self.width() * 0.35),
            int(self.height() * 0.9 - self.width() * 0.35),
            int(self.width() * 0.7),
            int(self.width() * 0.7)
        )

        p.setClipping(False)

        noise_gradient = QLinearGradient(0, 0, 0, self.height())
        noise_gradient.setColorAt(0.0, QColor(255, 255, 255, 2))
        noise_gradient.setColorAt(0.5, QColor(255, 255, 255, 0))
        noise_gradient.setColorAt(1.0, QColor(0, 0, 0, 3))
        p.setBrush(QBrush(noise_gradient))
        p.setClipPath(main_bg)
        p.drawRect(0, 0, self.width(), self.height())
        p.setClipping(False)

        p.end()

    def mousePressEvent(self, event):
        if self.parent():
            self.parent().mousePressEvent(event)
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.parent():
            self.parent().mouseMoveEvent(event)
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.parent():
            self.parent().mouseReleaseEvent(event)
        else:
            super().mouseReleaseEvent(event)
