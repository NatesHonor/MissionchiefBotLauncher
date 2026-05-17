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

from utils.regions import list_regions, select_region


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
            p.setBrush(QBrush(QColor("#13111C")))
            p.setPen(QPen(QColor("#6C5CE7"), 1))
        elif self._hovered:
            hover_bg = QLinearGradient(0, 0, self.width(), 0)
            hover_bg.setColorAt(0.0, QColor(108, 92, 231, 12))
            hover_bg.setColorAt(1.0, QColor(168, 85, 247, 6))
            p.setBrush(QBrush(hover_bg))
            p.setPen(QPen(QColor(108, 92, 231, 40), 1))
        else:
            p.setBrush(QBrush(QColor("#0E0C15")))
            p.setPen(QPen(QColor("#1E1B2E"), 1))

        p.drawPath(bg)

        dot_x, dot_y = 18, self.height() // 2 - 4
        if self._hovered or self._pressed:
            glow = QRadialGradient(dot_x + 4, dot_y + 4, 10)
            glow.setColorAt(0.0, QColor(108, 92, 231, 30))
            glow.setColorAt(1.0, QColor(108, 92, 231, 0))
            p.setBrush(QBrush(glow))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(dot_x - 6, dot_y - 6, 20, 20)

        p.setBrush(QBrush(QColor("#6C5CE7") if self._hovered else QColor("#2A2540")))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(dot_x, dot_y, 8, 8)

        cx = dot_x + 4
        cy = dot_y + 4
        p.setPen(QPen(QColor("#7C7A85") if not self._hovered else QColor("#A855F7"), 1.4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
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
            p.setPen(QPen(QColor("#6C5CE7"), 1.6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
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
        glow.setColorAt(0.0, QColor(108, 92, 231, 20))
        glow.setColorAt(1.0, QColor(108, 92, 231, 0))
        p.setBrush(QBrush(glow))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(0, 0, 72, 72)

        bg = QLinearGradient(10, 10, 62, 62)
        bg.setColorAt(0.0, QColor("#6C5CE7"))
        bg.setColorAt(1.0, QColor("#A855F7"))
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
    config = configparser.ConfigParser()
    config.read("launcher_settings.ini")

    region = config.get("Launcher", "region", fallback="").strip()
    if region:
        return

    dialog = QDialog(parent)
    dialog.setWindowTitle("Select Region")
    dialog.setFixedSize(400, 520)
    dialog.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
    dialog.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
    dialog.setModal(True)

    dialog._drag_pos = None

    def mouse_press(event):
        if event.button() == Qt.MouseButton.LeftButton:
            dialog._drag_pos = event.globalPosition().toPoint() - dialog.frameGeometry().topLeft()

    def mouse_move(event):
        if dialog._drag_pos and event.buttons() == Qt.MouseButton.LeftButton:
            dialog.move(event.globalPosition().toPoint() - dialog._drag_pos)

    def mouse_release(event):
        dialog._drag_pos = None

    dialog.mousePressEvent = mouse_press
    dialog.mouseMoveEvent = mouse_move
    dialog.mouseReleaseEvent = mouse_release

    container = QWidget(dialog)
    container.setGeometry(0, 0, 400, 520)
    container.setStyleSheet("""
        QWidget {
            background-color: #13111C;
            border-radius: 16px;
            border: 1px solid #2A2540;
        }
    """)

    shadow = QGraphicsDropShadowEffect(dialog)
    shadow.setBlurRadius(50)
    shadow.setColor(QColor(0, 0, 0, 180))
    shadow.setOffset(0, 10)
    container.setGraphicsEffect(shadow)

    layout = QVBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)

    accent = QWidget()
    accent.setFixedHeight(3)
    accent.setStyleSheet("""
        QWidget {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #6C5CE7, stop:0.35 #A855F7,
                stop:0.65 #EC4899, stop:1 #F97316);
            border: none;
            border-radius: 0;
        }
    """)
    layout.addWidget(accent)

    header = QWidget()
    header.setStyleSheet("background: transparent; border: none;")
    header_layout = QVBoxLayout(header)
    header_layout.setContentsMargins(0, 24, 0, 0)
    header_layout.setSpacing(12)
    header_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

    icon = WelcomeIcon()
    header_layout.addWidget(icon, alignment=Qt.AlignmentFlag.AlignCenter)

    title = QLabel("Welcome")
    title.setAlignment(Qt.AlignmentFlag.AlignCenter)
    title.setStyleSheet("""
        QLabel {
            color: #F1F0F5;
            font-size: 22px;
            font-weight: 700;
            background: transparent;
            border: none;
            letter-spacing: 0.5px;
        }
    """)
    header_layout.addWidget(title)

    subtitle = QLabel("Select your region to get started")
    subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
    subtitle.setStyleSheet("""
        QLabel {
            color: #6B6878;
            font-size: 13px;
            font-weight: 400;
            background: transparent;
            border: none;
        }
    """)
    header_layout.addWidget(subtitle)

    layout.addWidget(header)
    layout.addSpacing(20)

    divider = QFrame()
    divider.setFixedHeight(1)
    divider.setStyleSheet("""
        QFrame {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 transparent, stop:0.1 #1E1B2E,
                stop:0.5 #2A2540, stop:0.9 #1E1B2E, stop:1 transparent);
            border: none;
        }
    """)
    layout.addWidget(divider)
    layout.addSpacing(8)

    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    scroll.setStyleSheet("""
        QScrollArea {
            background: transparent;
            border: none;
        }
        QScrollBar:vertical {
            background: transparent;
            width: 6px;
            margin: 4px 2px;
            border-radius: 3px;
        }
        QScrollBar::handle:vertical {
            background: #2A2540;
            border-radius: 3px;
            min-height: 30px;
        }
        QScrollBar::handle:vertical:hover {
            background: #6C5CE7;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
            background: transparent; height: 0; border: none;
        }
    """)

    scroll_content = QWidget()
    scroll_content.setStyleSheet("background: transparent; border: none;")
    scroll_layout = QVBoxLayout(scroll_content)
    scroll_layout.setContentsMargins(16, 4, 16, 16)
    scroll_layout.setSpacing(6)

    def on_select(region_name):
        select_region(region_name)
        dialog.accept()

    for r in list_regions():
        btn = RegionButton(r, on_select)
        scroll_layout.addWidget(btn)

    scroll_layout.addStretch()
    scroll.setWidget(scroll_content)
    layout.addWidget(scroll)

    dialog.exec()