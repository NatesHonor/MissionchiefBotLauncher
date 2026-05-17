from PyQt6.QtCore import Qt
from PyQt6.QtGui import (
    QColor, QPainter, QPainterPath, QLinearGradient,
    QBrush, QPen, QFont, QRadialGradient
)
from PyQt6.QtWidgets import QPushButton


class ActionButton(QPushButton):

    STYLES = {
        "primary": {
            "gradient": [("#6C5CE7", 0.0), ("#A855F7", 0.5), ("#EC4899", 1.0)],
            "hover":    [("#7C6CF7", 0.0), ("#B86AF7", 0.5), ("#F472B6", 1.0)],
            "pressed":  [("#4338CA", 0.0), ("#7E22CE", 0.5), ("#BE185D", 1.0)],
            "glow": "#A855F7",
        },
        "success": {
            "gradient": [("#059669", 0.0), ("#10B981", 0.5), ("#34D399", 1.0)],
            "hover":    [("#10B981", 0.0), ("#34D399", 0.5), ("#6EE7B7", 1.0)],
            "pressed":  [("#047857", 0.0), ("#059669", 0.5), ("#10B981", 1.0)],
            "glow": "#10B981",
        },
        "danger": {
            "gradient": [("#DC2626", 0.0), ("#EF4444", 0.5), ("#F87171", 1.0)],
            "hover":    [("#EF4444", 0.0), ("#F87171", 0.5), ("#FCA5A5", 1.0)],
            "pressed":  [("#B91C1C", 0.0), ("#DC2626", 0.5), ("#EF4444", 1.0)],
            "glow": "#EF4444",
        },
        "secondary": {
            "gradient": [("#1E1B2E", 0.0), ("#1E1B2E", 1.0)],
            "hover":    [("#2A2540", 0.0), ("#2A2540", 1.0)],
            "pressed":  [("#13111C", 0.0), ("#13111C", 1.0)],
            "glow": "#6C5CE7",
            "border": "#2A2540",
            "border_hover": "#3D3756",
            "text": "#C9C8D0",
        },
        "ghost": {
            "gradient": [("#00000000", 0.0), ("#00000000", 1.0)],
            "hover":    [("#1A1726", 0.0), ("#1A1726", 1.0)],
            "pressed":  [("#13111C", 0.0), ("#13111C", 1.0)],
            "glow": None,
            "border": "#2A2540",
            "border_hover": "#3D3756",
            "text": "#7C7A85",
            "text_hover": "#C9C8D0",
        },
    }

    def __init__(self, text, style="primary", icon_type=None, parent=None):
        super().__init__(text, parent)
        self.setFixedHeight(44)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("background: transparent; border: none;")

        self._style_name = style
        self._style = self.STYLES.get(style, self.STYLES["primary"])
        self._icon_type = icon_type
        self._hovered = False
        self._pressed = False

    def set_style(self, style_name):
        self._style_name = style_name
        self._style = self.STYLES.get(style_name, self.STYLES["primary"])
        self.update()

    def enterEvent(self, event):
        self._hovered = True
        self.update()

    def leaveEvent(self, event):
        self._hovered = False
        self._pressed = False
        self.update()

    def mousePressEvent(self, event):
        self._pressed = True
        self.update()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self._pressed = False
        self.update()
        super().mouseReleaseEvent(event)

    def _build_gradient(self, stops):
        g = QLinearGradient(0, 0, self.width(), 0)
        for color, pos in stops:
            g.setColorAt(pos, QColor(color))
        return g

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        style = self._style
        w, h = self.width(), self.height()

        bg_path = QPainterPath()
        bg_path.addRoundedRect(0, 0, w, h, 12, 12)

        if self._pressed:
            gradient = self._build_gradient(style["pressed"])
        elif self._hovered:
            gradient = self._build_gradient(style["hover"])
        else:
            gradient = self._build_gradient(style["gradient"])

        p.setBrush(QBrush(gradient))

        has_border = "border" in style
        if has_border:
            border_color = style.get("border_hover", style["border"]) if self._hovered else style["border"]
            p.setPen(QPen(QColor(border_color), 1))
        else:
            p.setPen(Qt.PenStyle.NoPen)

        p.drawPath(bg_path)

        if self._hovered and not self._pressed and style.get("glow"):
            glow = QRadialGradient(w / 2, h / 2, w * 0.6)
            glow.setColorAt(0.0, QColor(style["glow"] + "18"))
            glow.setColorAt(0.5, QColor(style["glow"] + "08"))
            glow.setColorAt(1.0, QColor(style["glow"] + "00"))
            p.setBrush(QBrush(glow))
            p.setPen(Qt.PenStyle.NoPen)
            p.setClipPath(bg_path)
            p.drawRect(0, 0, w, h)
            p.setClipping(False)

        if not self._pressed and not has_border:
            shine = QLinearGradient(0, 0, 0, h * 0.5)
            shine.setColorAt(0.0, QColor(255, 255, 255, 15))
            shine.setColorAt(1.0, QColor(255, 255, 255, 0))
            p.setBrush(QBrush(shine))
            p.setPen(Qt.PenStyle.NoPen)
            top_path = QPainterPath()
            top_path.addRoundedRect(0, 0, w, h * 0.5, 12, 12)
            clipped = top_path & bg_path
            p.drawPath(clipped)

        text_x = 0
        if self._icon_type:
            icon_x = 16
            icon_cy = h / 2
            icon_color = QColor(style.get("text", "#FFFFFF") if not self._hovered else style.get("text_hover", "#FFFFFF"))
            p.setPen(QPen(icon_color, 1.8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
            p.setBrush(Qt.BrushStyle.NoBrush)

            if self._icon_type == "play":
                bx, by = icon_x, int(icon_cy - 6)
                path = QPainterPath()
                path.moveTo(bx, by)
                path.lineTo(bx + 11, by + 6)
                path.lineTo(bx, by + 12)
                path.closeSubpath()
                p.setBrush(QBrush(icon_color))
                p.setPen(Qt.PenStyle.NoPen)
                p.drawPath(path)

            elif self._icon_type == "stop":
                bx, by = icon_x, int(icon_cy - 5)
                p.setBrush(QBrush(icon_color))
                p.setPen(Qt.PenStyle.NoPen)
                p.drawRoundedRect(bx, by, 10, 10, 2, 2)

            elif self._icon_type == "save":
                bx, by = icon_x, int(icon_cy - 7)
                p.drawRoundedRect(bx, by, 14, 14, 2, 2)
                p.drawLine(bx + 4, by, bx + 4, by + 5)
                p.drawLine(bx + 10, by, bx + 10, by + 5)
                p.drawLine(bx + 3, by + 9, bx + 11, by + 9)

            elif self._icon_type == "refresh":
                import math
                cx, cy_i = icon_x + 7, int(icon_cy)
                p.drawArc(cx - 6, cy_i - 6, 12, 12, 30 * 16, 300 * 16)
                angle = math.radians(30)
                ax = cx + int(6 * math.cos(angle))
                ay = cy_i - int(6 * math.sin(angle))
                p.drawLine(ax, ay, ax + 3, ay - 3)
                p.drawLine(ax, ay, ax + 3, ay + 2)

            elif self._icon_type == "download":
                cx_i = icon_x + 7
                cy_i = int(icon_cy)
                p.drawLine(cx_i, cy_i - 7, cx_i, cy_i + 3)
                p.drawLine(cx_i, cy_i + 3, cx_i - 4, cy_i - 1)
                p.drawLine(cx_i, cy_i + 3, cx_i + 4, cy_i - 1)
                p.drawLine(cx_i - 6, cy_i + 6, cx_i + 6, cy_i + 6)

            elif self._icon_type == "settings":
                cx_i, cy_i = icon_x + 7, int(icon_cy)
                p.drawEllipse(cx_i - 3, cy_i - 3, 6, 6)
                import math
                for a in range(0, 360, 45):
                    rad = math.radians(a)
                    x1 = cx_i + int(5 * math.cos(rad))
                    y1 = cy_i + int(5 * math.sin(rad))
                    x2 = cx_i + int(7 * math.cos(rad))
                    y2 = cy_i + int(7 * math.sin(rad))
                    p.drawLine(x1, y1, x2, y2)

            text_x = 36

        font = QFont("Segoe UI", 13)
        font.setWeight(QFont.Weight.Bold)
        p.setFont(font)

        if self._pressed:
            text_color = QColor(style.get("text", "#FFFFFF"))
            text_color.setAlpha(200)
        elif self._hovered:
            text_color = QColor(style.get("text_hover", style.get("text", "#FFFFFF")))
        else:
            text_color = QColor(style.get("text", "#FFFFFF"))

        p.setPen(text_color)
        p.drawText(
            text_x, 0, w - text_x - 12, h,
            Qt.AlignmentFlag.AlignCenter if not self._icon_type else Qt.AlignmentFlag.AlignVCenter,
            self.text()
        )

        p.end()