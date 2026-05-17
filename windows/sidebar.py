import os
import sys
import configparser
from PyQt6.QtCore import Qt, QSize, QTimer, QPropertyAnimation, QEasingCurve, QRect
from PyQt6.QtGui import (
    QFont, QIcon, QPixmap, QColor, QPainter, QPainterPath,
    QLinearGradient, QBrush, QPen, QRadialGradient
)
from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QDialog, QWidget, QGraphicsDropShadowEffect,
    QGraphicsOpacityEffect, QScrollArea, QSizePolicy
)

from utils.regions import list_regions, select_region


def resource_path(relative_path):
    base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    return os.path.join(base_path, relative_path)


class SidebarButton(QPushButton):
    def __init__(self, text, icon_type=None, accent=None, parent=None):
        super().__init__(parent)
        self.setText(text)
        self.setFixedHeight(42)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._icon_type = icon_type
        self._accent = QColor(accent) if accent else QColor("#6C5CE7")
        self._active = False
        self._hovered = False
        self._pressed = False

    def set_active(self, active):
        self._active = active
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

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        bg = QPainterPath()
        bg.addRoundedRect(0, 0, self.width(), self.height(), 10, 10)

        if self._active:
            active_bg = QLinearGradient(0, 0, self.width(), 0)
            active_bg.setColorAt(0.0, QColor(self._accent.red(), self._accent.green(), self._accent.blue(), 20))
            active_bg.setColorAt(1.0, QColor(self._accent.red(), self._accent.green(), self._accent.blue(), 8))
            p.setBrush(QBrush(active_bg))
            p.setPen(QPen(QColor(self._accent.red(), self._accent.green(), self._accent.blue(), 40), 1))
            p.drawPath(bg)

            p.setBrush(QBrush(self._accent))
            p.setPen(Qt.PenStyle.NoPen)
            indicator = QPainterPath()
            indicator.addRoundedRect(0, 8, 3, self.height() - 16, 1.5, 1.5)
            p.drawPath(indicator)

        elif self._pressed:
            p.setBrush(QBrush(QColor("#1A1726")))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawPath(bg)

        elif self._hovered:
            p.setBrush(QBrush(QColor("#13111C")))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawPath(bg)

        icon_x = 14
        icon_cy = self.height() / 2
        icon_color = self._accent if self._active else (QColor("#C9C8D0") if self._hovered else QColor("#6B6878"))
        p.setPen(QPen(icon_color, 1.6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        p.setBrush(Qt.BrushStyle.NoBrush)

        if self._icon_type == "dashboard":
            bx, by = icon_x, int(icon_cy - 7)
            p.drawRoundedRect(bx, by, 6, 6, 1.5, 1.5)
            p.drawRoundedRect(bx + 8, by, 6, 6, 1.5, 1.5)
            p.drawRoundedRect(bx, by + 8, 6, 6, 1.5, 1.5)
            p.drawRoundedRect(bx + 8, by + 8, 6, 6, 1.5, 1.5)

        elif self._icon_type == "globe":
            cx, cy = icon_x + 7, int(icon_cy)
            p.drawEllipse(cx - 7, cy - 7, 14, 14)
            p.drawLine(cx - 7, cy, cx + 7, cy)
            p.drawArc(cx - 4, cy - 7, 8, 14, 0, 5760)

        elif self._icon_type == "settings":
            cx, cy = icon_x + 7, int(icon_cy)
            p.drawEllipse(cx - 3, cy - 3, 6, 6)
            for angle in range(0, 360, 45):
                import math
                rad = math.radians(angle)
                x1 = cx + int(5 * math.cos(rad))
                y1 = cy + int(5 * math.sin(rad))
                x2 = cx + int(7 * math.cos(rad))
                y2 = cy + int(7 * math.sin(rad))
                p.drawLine(x1, y1, x2, y2)

        elif self._icon_type == "user":
            cx, cy = icon_x + 7, int(icon_cy)
            p.drawEllipse(cx - 3, cy - 6, 6, 6)
            path = QPainterPath()
            path.moveTo(cx - 6, cy + 7)
            path.quadTo(cx - 6, cy + 1, cx, cy + 1)
            path.quadTo(cx + 6, cy + 1, cx + 6, cy + 7)
            p.drawPath(path)

        elif self._icon_type == "exit":
            bx, by = icon_x, int(icon_cy - 6)
            p.drawLine(bx + 4, by, bx + 4, by + 12)
            p.drawArc(bx, by + 2, 14, 10, 30 * 16, 120 * 16)
            p.drawArc(bx, by + 2, 14, 10, 210 * 16, 120 * 16)

        elif self._icon_type == "play":
            bx, by = icon_x + 1, int(icon_cy - 6)
            path = QPainterPath()
            path.moveTo(bx, by)
            path.lineTo(bx + 12, by + 6)
            path.lineTo(bx, by + 12)
            path.closeSubpath()
            p.setBrush(QBrush(icon_color))
            p.drawPath(path)

        elif self._icon_type == "stop":
            bx, by = icon_x + 1, int(icon_cy - 5)
            p.setBrush(QBrush(icon_color))
            p.drawRoundedRect(bx, by, 10, 10, 2, 2)

        text_x = 40
        font = QFont("Segoe UI", 12)
        font.setWeight(QFont.Weight.DemiBold if self._active else QFont.Weight.Medium)
        p.setFont(font)

        text_color = self._accent if self._active else (QColor("#E1E1E6") if self._hovered else QColor("#7C7A85"))
        p.setPen(text_color)
        p.drawText(text_x, 0, self.width() - text_x - 12, self.height(), Qt.AlignmentFlag.AlignVCenter, self.text())

        p.end()


class UserCard(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(64)
        self._pixmap = None

        avatar_path = resource_path("icons/user_icon.png")
        if os.path.exists(avatar_path):
            self._pixmap = QPixmap(avatar_path).scaled(
                28, 28,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        bg = QPainterPath()
        bg.addRoundedRect(4, 4, self.width() - 8, self.height() - 8, 12, 12)
        p.setBrush(QBrush(QColor("#13111C")))
        p.setPen(QPen(QColor("#1E1B2E"), 1))
        p.drawPath(bg)

        avatar_x, avatar_y = 16, 12
        avatar_size = 40

        ring_gradient = QLinearGradient(avatar_x, avatar_y, avatar_x + avatar_size, avatar_y + avatar_size)
        ring_gradient.setColorAt(0.0, QColor("#6C5CE7"))
        ring_gradient.setColorAt(1.0, QColor("#A855F7"))
        p.setPen(QPen(QBrush(ring_gradient), 2))
        p.setBrush(QBrush(QColor("#1E1B2E")))
        p.drawEllipse(avatar_x, avatar_y, avatar_size, avatar_size)

        if self._pixmap:
            mask_path = QPainterPath()
            mask_path.addEllipse(avatar_x + 4, avatar_y + 4, avatar_size - 8, avatar_size - 8)
            p.setClipPath(mask_path)
            px = avatar_x + (avatar_size - self._pixmap.width()) // 2
            py = avatar_y + (avatar_size - self._pixmap.height()) // 2
            p.drawPixmap(px, py, self._pixmap)
            p.setClipping(False)
        else:
            cx = avatar_x + avatar_size // 2
            cy = avatar_y + avatar_size // 2
            p.setPen(QPen(QColor("#6C5CE7"), 1.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(cx - 4, cy - 7, 8, 8)
            path = QPainterPath()
            path.moveTo(cx - 8, cy + 9)
            path.quadTo(cx - 8, cy + 2, cx, cy + 2)
            path.quadTo(cx + 8, cy + 2, cx + 8, cy + 9)
            p.drawPath(path)

        text_x = avatar_x + avatar_size + 12

        name_font = QFont("Segoe UI", 12)
        name_font.setWeight(QFont.Weight.DemiBold)
        p.setFont(name_font)
        p.setPen(QColor("#F1F0F5"))
        p.drawText(text_x, 10, self.width() - text_x - 12, 24, Qt.AlignmentFlag.AlignVCenter, "User")

        role_font = QFont("Segoe UI", 10)
        role_font.setWeight(QFont.Weight.Normal)
        p.setFont(role_font)
        p.setPen(QColor("#4A4458"))
        p.drawText(text_x, 30, self.width() - text_x - 12, 20, Qt.AlignmentFlag.AlignVCenter, "Operator")

        online_x = self.width() - 24
        online_y = 26
        p.setBrush(QBrush(QColor("#22C55E")))
        p.setPen(QPen(QColor("#13111C"), 2))
        p.drawEllipse(online_x, online_y, 8, 8)

        p.end()


class SectionLabel(QWidget):
    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.setFixedHeight(28)
        self._text = text.upper()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        font = QFont("Segoe UI", 9)
        font.setWeight(QFont.Weight.Bold)
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 2.0)
        p.setFont(font)
        p.setPen(QColor("#3D3756"))
        p.drawText(16, 0, self.width() - 16, self.height(), Qt.AlignmentFlag.AlignVCenter, self._text)

        p.end()


class RegionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_region = None
        self.setWindowTitle("Select Region")
        self.setFixedSize(320, 420)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        self._drag_pos = None

        container = QWidget(self)
        container.setGeometry(0, 0, 320, 420)
        container.setStyleSheet("""
            QWidget {
                background-color: #13111C;
                border-radius: 14px;
                border: 1px solid #2A2540;
            }
        """)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(40)
        shadow.setColor(QColor(0, 0, 0, 150))
        shadow.setOffset(0, 8)
        container.setGraphicsEffect(shadow)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        accent = QWidget()
        accent.setFixedHeight(3)
        accent.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6C5CE7, stop:0.5 #A855F7, stop:1 #EC4899);
                border: none;
                border-radius: 0;
            }
        """)
        layout.addWidget(accent)

        header = QWidget()
        header.setFixedHeight(56)
        header.setStyleSheet("background: transparent; border: none;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 0, 12, 0)

        title = QLabel("Select Region")
        title.setStyleSheet("""
            QLabel {
                color: #F1F0F5;
                font-size: 16px;
                font-weight: 700;
                background: transparent;
                border: none;
            }
        """)
        header_layout.addWidget(title)
        header_layout.addStretch()

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(28, 28)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #4A4458;
                font-size: 14px;
                font-weight: 600;
                border: none;
                border-radius: 14px;
            }
            QPushButton:hover {
                background: #1E1B2E;
                color: #9CA3AF;
            }
        """)
        close_btn.clicked.connect(self.reject)
        header_layout.addWidget(close_btn)

        layout.addWidget(header)

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
                margin: 4px 0;
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
        scroll_layout.setContentsMargins(12, 8, 12, 12)
        scroll_layout.setSpacing(4)

        for region in list_regions():
            btn = QPushButton(region)
            btn.setFixedHeight(44)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    color: #C9C8D0;
                    font-size: 13px;
                    font-weight: 500;
                    border: none;
                    border-radius: 10px;
                    text-align: left;
                    padding-left: 16px;
                }
                QPushButton:hover {
                    background: #1A1726;
                    color: #F1F0F5;
                }
                QPushButton:pressed {
                    background: #13111C;
                }
            """)
            btn.clicked.connect(lambda _, r=region: self._pick(r))
            scroll_layout.addWidget(btn)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

    def _pick(self, region):
        self.selected_region = region
        self.accept()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None


class Sidebar(QFrame):
    def __init__(self, parent, stack):
        super().__init__()
        self.parent = parent
        self.stack = stack
        self.setFixedWidth(230)
        self.setStyleSheet("background: transparent; border: none;")
        self._active_btn = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 12, 8, 16)
        layout.setSpacing(0)

        self.user_card = UserCard()
        layout.addWidget(self.user_card)

        layout.addSpacing(16)

        layout.addWidget(SectionLabel("Navigation"))
        layout.addSpacing(4)

        self.dashboard_btn = SidebarButton("Dashboard", "dashboard", "#6C5CE7")
        self.dashboard_btn.clicked.connect(lambda: self._navigate("dashboard"))
        layout.addWidget(self.dashboard_btn)

        layout.addSpacing(2)

        self.region_btn = SidebarButton(self._get_region(), "globe", "#A855F7")
        self.region_btn.clicked.connect(self.change_region)
        layout.addWidget(self.region_btn)

        layout.addSpacing(2)

        self.settings_btn = SidebarButton("Settings", "settings", "#EC4899")
        self.settings_btn.clicked.connect(lambda: self._navigate("settings"))
        layout.addWidget(self.settings_btn)

        layout.addSpacing(16)

        layout.addWidget(SectionLabel("Controls"))
        layout.addSpacing(4)

        self.run_btn = SidebarButton("Start Bot", "play", "#22C55E")
        self.run_btn.clicked.connect(self._toggle_bot)
        layout.addWidget(self.run_btn)

        layout.addSpacing(2)

        self.signin_btn = SidebarButton("Sign In", "user", "#53D8FB")
        layout.addWidget(self.signin_btn)

        layout.addStretch()

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 transparent, stop:0.15 #1E1B2E,
                    stop:0.5 #2A2540, stop:0.85 #1E1B2E, stop:1 transparent);
                border: none;
            }
        """)
        layout.addWidget(sep)
        layout.addSpacing(8)

        self.exit_btn = SidebarButton("Exit", "exit", "#EF4444")
        self.exit_btn.clicked.connect(parent.close)
        layout.addWidget(self.exit_btn)

        self._set_active(self.dashboard_btn)

    def _get_region(self):
        config = configparser.ConfigParser()
        config.read("launcher_settings.ini")
        return config.get("Launcher", "region", fallback="Select Region")

    def _navigate(self, page):
        if page == "dashboard":
            self._set_active(self.dashboard_btn)
            if hasattr(self.parent, 'title_bar'):
                self.parent.title_bar.set_page("Dashboard")
            if self.stack:
                self.stack.setCurrentIndex(0)

        elif page == "settings":
            self._set_active(self.settings_btn)
            if hasattr(self.parent, 'title_bar'):
                self.parent.title_bar.set_page("Settings")
            if self.stack:
                self.stack.setCurrentIndex(1)

    def _set_active(self, btn):
        if self._active_btn:
            self._active_btn.set_active(False)
        btn.set_active(True)
        self._active_btn = btn

    def change_region(self):
        dialog = RegionDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.selected_region:
            select_region(dialog.selected_region)
            self.region_btn.setText(dialog.selected_region)

    def _toggle_bot(self):
        if hasattr(self.parent, 'console_panel'):
            self.parent.console_panel.toggle_start_stop()
            self.sync_run_button()

    def sync_run_button(self):
        running = self.parent.is_running
        if running:
            self.run_btn.setText("Stop Bot")
            self.run_btn._icon_type = "stop"
            self.run_btn._accent = QColor("#EF4444")
        else:
            self.run_btn.setText("Start Bot")
            self.run_btn._icon_type = "play"
            self.run_btn._accent = QColor("#22C55E")
        self.run_btn.update()

    def show_settings(self):
        self._navigate("settings")

    def show_home(self):
        self._navigate("dashboard")