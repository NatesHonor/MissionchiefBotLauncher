import configparser
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import (
    QColor, QPainter, QPainterPath, QLinearGradient,
    QBrush, QPen, QFont, QRadialGradient
)
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QWidget, QFrame, QScrollArea, QGraphicsDropShadowEffect
)

from utils.regions import get_selected_region, list_regions, select_region
from utils.paths import LAUNCHER_CONFIG


class RegionButton(QWidget):
    def __init__(self, region_name, callback, parent=None):
        super().__init__(parent)
        self.setFixedHeight(52)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._name = region_name
        self._callback = callback
        self._hovered = False
        self._pressed = False

    def enterEvent(self, event):
        self._hovered = True
        self.update()

    def leaveEvent(self, event):
        self._hovered = False
        self._pressed = False
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._pressed = True
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._pressed:
            self._pressed = False
            self.update()
            if self._callback:
                self._callback(self._name)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        bg = QPainterPath()
        bg.addRoundedRect(0, 0, self.width(), self.height(), 12, 12)

        if self._pressed:
            p.setBrush(QBrush(QColor("#0B1B2D")))
            p.setPen(QPen(QColor("#2583E8"), 1))
        elif self._hovered:
            hover_bg = QLinearGradient(0, 0, self.width(), 0)
            hover_bg.setColorAt(0.0, QColor(29, 101, 216, 12))
            hover_bg.setColorAt(1.0, QColor(37, 131, 232, 6))
            p.setBrush(QBrush(hover_bg))
            p.setPen(QPen(QColor(29, 101, 216, 40), 1))
        else:
            p.setBrush(QBrush(QColor("#07111F")))
            p.setPen(QPen(QColor("#1D3B5B"), 1))

        p.drawPath(bg)

        dot_x, dot_y = 18, self.height() // 2 - 4
        if self._hovered or self._pressed:
            glow = QRadialGradient(dot_x + 4, dot_y + 4, 10)
            glow.setColorAt(0.0, QColor(29, 101, 216, 30))
            glow.setColorAt(1.0, QColor(29, 101, 216, 0))
            p.setBrush(QBrush(glow))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(dot_x - 6, dot_y - 6, 20, 20)

        p.setBrush(QBrush(QColor("#2583E8") if self._hovered else QColor("#1D3B5B")))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(dot_x, dot_y, 8, 8)

        cx = dot_x + 4
        cy = dot_y + 4
        p.setPen(QPen(QColor("#7F9DB8") if not self._hovered else QColor("#4BA3FF"), 1.4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(cx - 4, cy - 4, 8, 8)
        p.drawLine(cx - 4, cy, cx + 4, cy)

        font = QFont("Segoe UI", 13)
        font.setWeight(QFont.Weight.DemiBold if self._hovered else QFont.Weight.Medium)
        p.setFont(font)
        p.setPen(QColor("#F1F0F5") if self._hovered else QColor("#9CA3AF"))
        p.drawText(40, 0, self.width() - 52, self.height(), Qt.AlignmentFlag.AlignVCenter, self._name)

        if self._hovered:
            arrow_x = self.width() - 28
            arrow_cy = self.height() // 2
            p.setPen(QPen(QColor("#2583E8"), 1.6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            p.drawLine(arrow_x, arrow_cy - 4, arrow_x + 5, arrow_cy)
            p.drawLine(arrow_x, arrow_cy + 4, arrow_x + 5, arrow_cy)

        p.end()


class WelcomeIcon(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(72, 72)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        glow = QRadialGradient(36, 36, 36)
        glow.setColorAt(0.0, QColor(29, 101, 216, 20))
        glow.setColorAt(1.0, QColor(29, 101, 216, 0))
        p.setBrush(QBrush(glow))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(0, 0, 72, 72)

        bg = QLinearGradient(10, 10, 62, 62)
        bg.setColorAt(0.0, QColor("#1D65D8"))
        bg.setColorAt(1.0, QColor("#2583E8"))
        p.setBrush(QBrush(bg))
        icon_path = QPainterPath()
        icon_path.addRoundedRect(10, 10, 52, 52, 16, 16)
        p.drawPath(icon_path)

        cx, cy = 36, 36
        p.setPen(QPen(QColor("#FFFFFF"), 2.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(cx - 10, cy - 10, 20, 20)
        p.drawLine(cx - 10, cy, cx + 10, cy)
        p.drawArc(cx - 5, cy - 10, 10, 20, 0, 5760)

        p.end()


def ensure_region_selected(parent):
    region = get_selected_region()
    if region:
        return True

    # Reuse the sidebar's themed dialog so first-run setup and in-app region
    # changes share the same layout and localization.
    from windows.sidebar import RegionDialog

    dialog_parent = getattr(parent, "sidebar", parent)
    dialog = RegionDialog(dialog_parent)
    if dialog.exec() != QDialog.DialogCode.Accepted or not dialog.selected_region:
        return False
    select_region(dialog.selected_region)
    return True
