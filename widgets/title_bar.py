import os
import sys
from PyQt6.QtCore import Qt, QPoint, QSize, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import (
    QFont, QPixmap, QIcon, QColor, QPainter, QPainterPath,
    QLinearGradient, QBrush, QPen, QRadialGradient
)
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton,
    QGraphicsDropShadowEffect, QGraphicsOpacityEffect, QSizePolicy
)


def resource_path(relative_path):
    base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    return os.path.join(base_path, relative_path)


class WindowButton(QPushButton):
    def __init__(self, icon_type="close", parent=None):
        super().__init__(parent)
        self.setFixedSize(32, 32)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._icon_type = icon_type
        self._hovered = False
        self._pressed = False

        self._colors = {
            "close": {
                "icon": "#6B6878",
                "icon_hover": "#FFFFFF",
                "bg_hover": "#EF4444",
                "bg_pressed": "#DC2626",
            },
            "minimize": {
                "icon": "#6B6878",
                "icon_hover": "#FFFFFF",
                "bg_hover": "#2A2540",
                "bg_pressed": "#1E1B2E",
            },
            "maximize": {
                "icon": "#6B6878",
                "icon_hover": "#FFFFFF",
                "bg_hover": "#2A2540",
                "bg_pressed": "#1E1B2E",
            },
        }

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

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        colors = self._colors.get(self._icon_type, self._colors["minimize"])

        bg = QPainterPath()
        bg.addRoundedRect(0, 0, self.width(), self.height(), 8, 8)

        if self._pressed:
            p.setBrush(QBrush(QColor(colors["bg_pressed"])))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawPath(bg)
        elif self._hovered:
            p.setBrush(QBrush(QColor(colors["bg_hover"])))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawPath(bg)

        icon_color = QColor(colors["icon_hover"] if self._hovered else colors["icon"])
        p.setPen(QPen(icon_color, 1.6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.setBrush(Qt.BrushStyle.NoBrush)

        cx, cy = self.width() / 2, self.height() / 2

        if self._icon_type == "close":
            s = 4.5
            p.drawLine(int(cx - s), int(cy - s), int(cx + s), int(cy + s))
            p.drawLine(int(cx + s), int(cy - s), int(cx - s), int(cy + s))

        elif self._icon_type == "minimize":
            p.drawLine(int(cx - 5), int(cy), int(cx + 5), int(cy))

        elif self._icon_type == "maximize":
            p.drawRoundedRect(int(cx - 5), int(cy - 5), 10, 10, 2, 2)

        p.end()


class AppLogo(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(36, 36)
        self._pixmap = None

        logo_path = resource_path("icons/missionchief_icon.png")
        if os.path.exists(logo_path):
            self._pixmap = QPixmap(logo_path).scaled(
                24, 24,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        bg = QLinearGradient(0, 0, self.width(), self.height())
        bg.setColorAt(0.0, QColor("#6C5CE7"))
        bg.setColorAt(1.0, QColor("#A855F7"))
        p.setBrush(QBrush(bg))
        p.setPen(Qt.PenStyle.NoPen)
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 10, 10)
        p.drawPath(path)

        if self._pixmap:
            x = (self.width() - self._pixmap.width()) // 2
            y = (self.height() - self._pixmap.height()) // 2
            p.drawPixmap(x, y, self._pixmap)

        p.end()


class BreadcrumbDot(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(4, 4)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setBrush(QBrush(QColor("#2A2540")))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(0, 0, 4, 4)
        p.end()


class TitleBar(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.setFixedHeight(52)
        self.setStyleSheet("background: transparent;")

        self.dragging = False
        self.offset = QPoint()
        self._double_click_timer = QTimer()
        self._double_click_timer.setSingleShot(True)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 8, 12, 8)
        layout.setSpacing(0)

        logo_section = QHBoxLayout()
        logo_section.setSpacing(12)
        logo_section.setContentsMargins(0, 0, 0, 0)

        self.logo = AppLogo()
        logo_section.addWidget(self.logo)

        title_block = QWidget()
        title_block.setStyleSheet("background: transparent;")
        title_layout = QHBoxLayout(title_block)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(8)

        self.title = QLabel("Mission Helper")
        self.title.setStyleSheet("""
            QLabel {
                color: #F1F0F5;
                font-size: 14px;
                font-weight: 700;
                background: transparent;
                letter-spacing: 0.3px;
            }
        """)
        title_layout.addWidget(self.title)

        dot = BreadcrumbDot()
        title_layout.addWidget(dot, alignment=Qt.AlignmentFlag.AlignVCenter)

        self.page_label = QLabel("Dashboard")
        self.page_label.setStyleSheet("""
            QLabel {
                color: #4A4458;
                font-size: 12px;
                font-weight: 500;
                background: transparent;
            }
        """)
        title_layout.addWidget(self.page_label)

        logo_section.addWidget(title_block)
        layout.addLayout(logo_section)

        layout.addStretch()

        controls = QHBoxLayout()
        controls.setSpacing(6)
        controls.setContentsMargins(0, 0, 0, 0)

        self.minimize_btn = WindowButton("minimize")
        self.minimize_btn.setToolTip("Minimize")
        self.minimize_btn.clicked.connect(self.parent.showMinimized)

        self.maximize_btn = WindowButton("maximize")
        self.maximize_btn.setToolTip("Maximize")
        self.maximize_btn.clicked.connect(self._toggle_maximize)

        self.close_btn = WindowButton("close")
        self.close_btn.setToolTip("Close")
        self.close_btn.clicked.connect(self.parent.close)

        controls.addWidget(self.minimize_btn)
        controls.addWidget(self.maximize_btn)
        controls.addWidget(self.close_btn)

        layout.addLayout(controls)

    def set_page(self, name):
        self.page_label.setText(name)

    def _toggle_maximize(self):
        if self.parent.isMaximized():
            self.parent.showNormal()
        else:
            self.parent.showMaximized()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        gradient = QLinearGradient(0, self.height(), 0, 0)
        gradient.setColorAt(0.0, QColor(14, 12, 21, 0))
        gradient.setColorAt(1.0, QColor(14, 12, 21, 40))
        p.setBrush(QBrush(gradient))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRect(0, 0, self.width(), self.height())

        p.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.offset = event.globalPosition().toPoint() - self.parent.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if self.dragging and event.buttons() & Qt.MouseButton.LeftButton:
            if self.parent.isMaximized():
                self.parent.showNormal()
                new_offset = QPoint(self.parent.width() // 2, self.offset.y())
                self.offset = new_offset
            self.parent.move(event.globalPosition().toPoint() - self.offset)

    def mouseReleaseEvent(self, event):
        self.dragging = False

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._toggle_maximize()