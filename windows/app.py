import configparser
from PyQt6.QtCore import Qt, QTimer, QUrl, QSize, QPropertyAnimation, QEasingCurve, QPoint
from PyQt6.QtGui import (
    QColor, QPainter, QPainterPath, QLinearGradient, QBrush,
    QPen, QRadialGradient, QFont, QIcon
)
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGraphicsDropShadowEffect, QFrame, QLabel,
    QStackedWidget, QSizePolicy, QSpacerItem
)
from PyQt6.QtWebEngineWidgets import QWebEngineView

from widgets.glass_frame import GlassFrame
from widgets.title_bar import TitleBar
from windows.sidebar import Sidebar
from windows.settings import ProfileHandler
from handlers.logging import generate_log_file
from handlers.updates import check_updates

from ui.console_panel import ConsolePanel
from ui.version_bar import VersionBar
from logic.region import ensure_region_selected
from logic.window_drag import WindowDragMixin


GLOBAL_STYLE = """
QMainWindow {
    background-color: #08070D;
}

QToolTip {
    background-color: #1E1B2E;
    color: #C9C8D0;
    border: 1px solid #2A2540;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 12px;
    font-family: 'Segoe UI', sans-serif;
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
    min-height: 40px;
}
QScrollBar::handle:vertical:hover {
    background: #6C5CE7;
}
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {
    background: transparent;
    height: 0;
    border: none;
}
QScrollBar:horizontal {
    background: transparent;
    height: 6px;
    margin: 0 4px;
    border-radius: 3px;
}
QScrollBar::handle:horizontal {
    background: #2A2540;
    border-radius: 3px;
    min-width: 40px;
}
QScrollBar::handle:horizontal:hover {
    background: #6C5CE7;
}
QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal,
QScrollBar::add-page:horizontal,
QScrollBar::sub-page:horizontal {
    background: transparent;
    width: 0;
    border: none;
}
"""


class AccentStrip(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(3)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        g = QLinearGradient(0, 0, self.width(), 0)
        g.setColorAt(0.0, QColor("#6C5CE7"))
        g.setColorAt(0.35, QColor("#A855F7"))
        g.setColorAt(0.65, QColor("#EC4899"))
        g.setColorAt(1.0, QColor("#F97316"))
        p.setBrush(QBrush(g))
        p.setPen(Qt.PenStyle.NoPen)
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 1.5, 1.5)
        p.drawPath(path)
        p.end()


class AmbientGlow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)

        g1 = QRadialGradient(self.width() * 0.15, 0, self.width() * 0.35)
        g1.setColorAt(0.0, QColor(108, 92, 231, 10))
        g1.setColorAt(1.0, QColor(108, 92, 231, 0))
        p.setBrush(QBrush(g1))
        p.drawEllipse(
            int(self.width() * 0.15 - self.width() * 0.35), -80,
            int(self.width() * 0.7), self.height() + 80
        )

        g2 = QRadialGradient(self.width() * 0.85, 0, self.width() * 0.3)
        g2.setColorAt(0.0, QColor(236, 72, 153, 7))
        g2.setColorAt(1.0, QColor(236, 72, 153, 0))
        p.setBrush(QBrush(g2))
        p.drawEllipse(
            int(self.width() * 0.85 - self.width() * 0.3), -60,
            int(self.width() * 0.6), self.height() + 60
        )

        p.end()


class SectionHeader(QWidget):
    def __init__(self, title, accent_color="#A855F7", parent=None):
        super().__init__(parent)
        self.setFixedHeight(32)
        self._title = title.upper()
        self._accent = QColor(accent_color)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(self._accent))
        p.drawEllipse(0, 11, 8, 8)

        font = QFont("Segoe UI", 10)
        font.setWeight(QFont.Weight.Bold)
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1.8)
        p.setFont(font)
        p.setPen(QColor("#7C7A85"))
        p.drawText(16, 0, self.width() - 16, self.height(), Qt.AlignmentFlag.AlignVCenter, self._title)

        p.end()


class GradientDivider(QFrame):
    def __init__(self, orientation="horizontal", parent=None):
        super().__init__(parent)
        if orientation == "horizontal":
            self.setFixedHeight(1)
            self.setStyleSheet("""
                QFrame {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 transparent,
                        stop:0.1 #1E1B2E,
                        stop:0.5 #2A2540,
                        stop:0.9 #1E1B2E,
                        stop:1 transparent);
                    border: none;
                }
            """)
        else:
            self.setFixedWidth(1)
            self.setStyleSheet("""
                QFrame {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 transparent,
                        stop:0.1 #1E1B2E,
                        stop:0.5 #2A2540,
                        stop:0.9 #1E1B2E,
                        stop:1 transparent);
                    border: none;
                }
            """)


class ContentCard(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background-color: #0E0C15;
                border: 1px solid #1A1726;
                border-radius: 12px;
            }
        """)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(24)
        shadow.setColor(QColor(0, 0, 0, 50))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)


class StatusIndicator(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(120, 28)
        self._running = False
        self._pulse = 0
        self._direction = 1
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)
        self._timer.start(40)

    def set_running(self, running):
        self._running = running
        self.update()

    def _animate(self):
        if self._running:
            self._pulse += self._direction * 3
            if self._pulse >= 100:
                self._direction = -1
            elif self._pulse <= 0:
                self._direction = 1
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        bg = QPainterPath()
        bg.addRoundedRect(0, 0, self.width(), self.height(), 14, 14)

        if self._running:
            p.setBrush(QBrush(QColor(34, 197, 94, 15)))
            p.setPen(QPen(QColor(34, 197, 94, 50), 1))
            dot_color = QColor(34, 197, 94)
            label = "Running"
        else:
            p.setBrush(QBrush(QColor(124, 122, 133, 10)))
            p.setPen(QPen(QColor(124, 122, 133, 40), 1))
            dot_color = QColor("#4A4458")
            label = "Idle"

        p.drawPath(bg)

        dot_x, dot_y = 12, 10
        if self._running:
            pulse_factor = self._pulse / 100.0
            glow = QRadialGradient(dot_x + 4, dot_y + 4, 10)
            glow.setColorAt(0.0, QColor(34, 197, 94, int(30 + pulse_factor * 40)))
            glow.setColorAt(1.0, QColor(34, 197, 94, 0))
            p.setBrush(QBrush(glow))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(dot_x - 6, dot_y - 6, 20, 20)

        p.setBrush(QBrush(dot_color))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(dot_x, dot_y, 8, 8)

        font = QFont("Segoe UI", 10)
        font.setWeight(QFont.Weight.DemiBold)
        p.setFont(font)
        p.setPen(QColor("#C9C8D0") if self._running else QColor("#6B6878"))
        p.drawText(28, 0, self.width() - 32, self.height(), Qt.AlignmentFlag.AlignVCenter, label)

        p.end()


class MissionChiefBotApp(QMainWindow, WindowDragMixin):
    def __init__(self):
        super().__init__()
        generate_log_file()

        self.is_running = False
        self.update_declined_this_session = False

        self.setWindowTitle("Mission Helper")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setStyleSheet(GLOBAL_STYLE)
        self.setMinimumSize(900, 600)

        self._set_geometry()
        self._build_ui()

        QTimer.singleShot(0, self.startup_sequence)

    def startup_sequence(self):
        updater_started = check_updates(self)
        if updater_started:
            return
        ensure_region_selected(self)
        self._setup_updates()

    def _set_geometry(self):
        screen = self.screen().availableGeometry()
        w = max(int(screen.width() * 0.6), 1000)
        h = max(int(screen.height() * 0.65), 650)
        x = (screen.width() - w) // 2
        y = (screen.height() - h) // 2
        self.setGeometry(x, y, w, h)

    def _build_ui(self):
        outer_shell = QWidget()
        outer_shell.setStyleSheet("background: #08070D;")
        outer_layout = QVBoxLayout(outer_shell)
        outer_layout.setContentsMargins(6, 6, 6, 6)
        outer_layout.setSpacing(0)

        container = GlassFrame(self)
        container.setObjectName("AppContainer")
        container.setStyleSheet("""
            QWidget#AppContainer {
                background-color: #0E0C15;
                border: 1px solid #1E1B2E;
                border-radius: 14px;
            }
        """)

        container_shadow = QGraphicsDropShadowEffect(self)
        container_shadow.setBlurRadius(50)
        container_shadow.setColor(QColor(0, 0, 0, 120))
        container_shadow.setOffset(0, 8)
        container.setGraphicsEffect(container_shadow)

        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        accent = AccentStrip()
        container_layout.addWidget(accent)

        self.title_bar = TitleBar(self)
        container_layout.addWidget(self.title_bar)

        header_bar = QWidget()
        header_bar.setFixedHeight(44)
        header_bar.setStyleSheet("background: transparent;")
        header_layout = QHBoxLayout(header_bar)
        header_layout.setContentsMargins(24, 0, 24, 0)
        header_layout.setSpacing(12)

        self.status_indicator = StatusIndicator()
        header_layout.addWidget(self.status_indicator)

        header_layout.addStretch()

        self.connection_label = QLabel("● Connected")
        self.connection_label.setStyleSheet("""
            QLabel {
                color: #22C55E;
                font-size: 11px;
                font-weight: 600;
                background: transparent;
                letter-spacing: 0.5px;
            }
        """)
        header_layout.addWidget(self.connection_label)

        container_layout.addWidget(header_bar)
        container_layout.addWidget(GradientDivider("horizontal"))

        body = QWidget()
        body.setStyleSheet("background: transparent;")
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setStyleSheet("background: transparent;")

        main_area = QWidget()
        main_area.setStyleSheet("background: transparent;")
        main_layout = QVBoxLayout(main_area)
        main_layout.setContentsMargins(20, 16, 20, 16)
        main_layout.setSpacing(0)

        ambient = AmbientGlow()
        ambient.setFixedHeight(80)
        main_layout.addWidget(ambient)

        console_header = SectionHeader("Console Output", "#6C5CE7")
        main_layout.addWidget(console_header)
        main_layout.addSpacing(8)

        console_card = ContentCard()
        console_inner = QVBoxLayout(console_card)
        console_inner.setContentsMargins(2, 2, 2, 2)
        console_inner.setSpacing(0)

        self.console_panel = ConsolePanel(self)
        console_inner.addWidget(self.console_panel)

        main_layout.addWidget(console_card, 3)
        main_layout.addSpacing(16)

        browser_header = SectionHeader("Mission Control", "#EC4899")
        main_layout.addWidget(browser_header)
        main_layout.addSpacing(8)

        browser_card = ContentCard()
        browser_inner = QVBoxLayout(browser_card)
        browser_inner.setContentsMargins(2, 2, 2, 2)
        browser_inner.setSpacing(0)

        self.web_view = QWebEngineView()
        self.web_view.setUrl(QUrl("https://www.missionchief.com"))
        self.web_view.setStyleSheet("""
            QWebEngineView {
                background-color: #0E0C15;
                border-radius: 10px;
            }
        """)
        browser_inner.addWidget(self.web_view)

        main_layout.addWidget(browser_card, 5)

        self.profile_handler = ProfileHandler(self)

        self.stacked_widget.addWidget(main_area)
        self.stacked_widget.addWidget(self.profile_handler)

        self.sidebar = Sidebar(self, self.stacked_widget)
        body_layout.addWidget(self.sidebar)
        body_layout.addWidget(GradientDivider("vertical"))
        body_layout.addWidget(self.stacked_widget, 1)

        container_layout.addWidget(body, 1)

        footer = QWidget()
        footer.setFixedHeight(32)
        footer.setStyleSheet("background: transparent;")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(24, 0, 24, 8)
        footer_layout.setSpacing(0)

        config = configparser.ConfigParser()
        config.read("launcher_settings.ini")
        version = config.get("Launcher", "version", fallback="0.0.0")

        version_label = QLabel(f"v{version}")
        version_label.setStyleSheet("""
            QLabel {
                color: #2A2540;
                font-size: 11px;
                font-weight: 600;
                background: transparent;
                letter-spacing: 1px;
            }
        """)
        footer_layout.addWidget(version_label)

        footer_layout.addStretch()

        credit_label = QLabel("Mission Helper")
        credit_label.setStyleSheet("""
            QLabel {
                color: #2A2540;
                font-size: 11px;
                font-weight: 500;
                background: transparent;
            }
        """)
        footer_layout.addWidget(credit_label)

        container_layout.addWidget(GradientDivider("horizontal"))
        container_layout.addWidget(footer)

        outer_layout.addWidget(container)

        self.setCentralWidget(outer_shell)

    def set_running(self, running):
        self.is_running = running
        self.status_indicator.set_running(running)

    def _setup_updates(self):
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(lambda: check_updates(self))
        self.update_timer.start(15 * 60 * 1000)