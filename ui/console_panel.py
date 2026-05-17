from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import (
    QFont, QColor, QPainter, QPainterPath, QLinearGradient,
    QBrush, QPen, QRadialGradient, QTextCursor
)
from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel,
    QTextEdit, QWidget, QGraphicsDropShadowEffect
)

from handlers.console import set_console_instance
from utils.start import update_start_button_state, run_start_logic
from utils.stop_bot import stop_bot


class ConsoleHeader(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(42)
        self._pulse = 0
        self._direction = 1
        self._active = False
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)
        self._timer.start(40)

    def set_active(self, active):
        self._active = active
        self.update()

    def _animate(self):
        if self._active:
            self._pulse += self._direction * 2
            if self._pulse >= 100:
                self._direction = -1
            elif self._pulse <= 0:
                self._direction = 1
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        dot_x, dot_y = 0, 15
        if self._active:
            pulse_factor = self._pulse / 100.0
            glow = QRadialGradient(dot_x + 5, dot_y + 5, 12)
            glow.setColorAt(0.0, QColor(34, 197, 94, int(20 + pulse_factor * 30)))
            glow.setColorAt(1.0, QColor(34, 197, 94, 0))
            p.setBrush(QBrush(glow))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(dot_x - 7, dot_y - 7, 24, 24)

            p.setBrush(QBrush(QColor("#22C55E")))
        else:
            p.setBrush(QBrush(QColor("#6C5CE7")))

        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(dot_x + 1, dot_y + 1, 8, 8)

        font = QFont("Segoe UI", 13)
        font.setWeight(QFont.Weight.Bold)
        p.setFont(font)
        p.setPen(QColor("#F1F0F5"))
        p.drawText(18, 0, self.width() - 18, self.height(), Qt.AlignmentFlag.AlignVCenter, "Console")

        tag_font = QFont("Segoe UI", 9)
        tag_font.setWeight(QFont.Weight.DemiBold)
        tag_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1.0)
        p.setFont(tag_font)

        tag_text = "LIVE" if self._active else "IDLE"
        tag_color = QColor("#22C55E") if self._active else QColor("#4A4458")
        tag_bg = QColor(34, 197, 94, 20) if self._active else QColor(74, 68, 88, 15)
        tag_border = QColor(34, 197, 94, 50) if self._active else QColor(74, 68, 88, 40)

        metrics = p.fontMetrics()
        tag_w = metrics.horizontalAdvance(tag_text) + 20
        tag_h = 22
        tag_x = self.width() - tag_w - 4
        tag_y = (self.height() - tag_h) // 2

        tag_path = QPainterPath()
        tag_path.addRoundedRect(tag_x, tag_y, tag_w, tag_h, 11, 11)
        p.setBrush(QBrush(tag_bg))
        p.setPen(QPen(tag_border, 1))
        p.drawPath(tag_path)

        p.setPen(tag_color)
        p.drawText(tag_x, tag_y, tag_w, tag_h, Qt.AlignmentFlag.AlignCenter, tag_text)

        p.end()


class ConsoleOutput(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setStyleSheet("""
            QTextEdit {
                background-color: #08070D;
                color: #C9C8D0;
                border: 1px solid #1A1726;
                border-radius: 10px;
                padding: 12px 14px;
                font-family: 'Cascadia Code', 'Fira Code', 'Consolas', monospace;
                font-size: 12px;
                line-height: 1.6;
                selection-background-color: #6C5CE7;
                selection-color: #FFFFFF;
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
        """)

    def append_message(self, message, level="info"):
        colors = {
            "info": "#C9C8D0",
            "success": "#22C55E",
            "warning": "#F59E0B",
            "error": "#EF4444",
            "system": "#6C5CE7",
            "debug": "#4A4458",
        }
        color = colors.get(level, colors["info"])

        prefixes = {
            "info": "›",
            "success": "✓",
            "warning": "⚠",
            "error": "✗",
            "system": "◆",
            "debug": "·",
        }
        prefix = prefixes.get(level, "›")

        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")

        html = f"""
            <div style="margin: 2px 0; line-height: 1.5;">
                <span style="color: #3D3756; font-size: 11px;">{timestamp}</span>
                <span style="color: {color}; font-weight: 600;"> {prefix} </span>
                <span style="color: {color};">{message}</span>
            </div>
        """
        self.moveCursor(QTextCursor.MoveOperation.End)
        self.insertHtml(html)
        self.ensureCursorVisible()


class ActionBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(48)
        self._running = False

    def set_running(self, running):
        self._running = running
        self.update()


class ControlButton(QWidget):
    clicked = None

    def __init__(self, text="Start Bot", parent=None):
        super().__init__(parent)
        from PyQt6.QtCore import pyqtSignal
        self.__class__.clicked = pyqtSignal()
        self.setFixedHeight(42)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._text = text
        self._running = False
        self._hovered = False
        self._pressed = False

    def set_running(self, running):
        self._running = running
        self._text = "Stop Bot" if running else "Start Bot"
        self.update()

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
            if hasattr(self, '_click_callback') and self._click_callback:
                self._click_callback()

    def set_click_callback(self, callback):
        self._click_callback = callback

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        bg = QPainterPath()
        bg.addRoundedRect(0, 0, self.width(), self.height(), 10, 10)

        if self._running:
            if self._pressed:
                g = QLinearGradient(0, 0, self.width(), 0)
                g.setColorAt(0.0, QColor("#B91C1C"))
                g.setColorAt(1.0, QColor("#991B1B"))
            elif self._hovered:
                g = QLinearGradient(0, 0, self.width(), 0)
                g.setColorAt(0.0, QColor("#F87171"))
                g.setColorAt(1.0, QColor("#EF4444"))
            else:
                g = QLinearGradient(0, 0, self.width(), 0)
                g.setColorAt(0.0, QColor("#EF4444"))
                g.setColorAt(1.0, QColor("#DC2626"))
        else:
            if self._pressed:
                g = QLinearGradient(0, 0, self.width(), 0)
                g.setColorAt(0.0, QColor("#4338CA"))
                g.setColorAt(0.5, QColor("#7E22CE"))
                g.setColorAt(1.0, QColor("#BE185D"))
            elif self._hovered:
                g = QLinearGradient(0, 0, self.width(), 0)
                g.setColorAt(0.0, QColor("#7C6CF7"))
                g.setColorAt(0.5, QColor("#B86AF7"))
                g.setColorAt(1.0, QColor("#F472B6"))
            else:
                g = QLinearGradient(0, 0, self.width(), 0)
                g.setColorAt(0.0, QColor("#6C5CE7"))
                g.setColorAt(0.5, QColor("#A855F7"))
                g.setColorAt(1.0, QColor("#EC4899"))

        p.setBrush(QBrush(g))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawPath(bg)

        icon_x = 16
        icon_cy = self.height() / 2
        p.setPen(QPen(QColor("#FFFFFF"), 2.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.setBrush(Qt.BrushStyle.NoBrush)

        if self._running:
            bx, by = icon_x, int(icon_cy - 5)
            p.setBrush(QBrush(QColor("#FFFFFF")))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(bx, by, 10, 10, 2, 2)
        else:
            bx, by = icon_x, int(icon_cy - 6)
            path = QPainterPath()
            path.moveTo(bx, by)
            path.lineTo(bx + 12, by + 6)
            path.lineTo(bx, by + 12)
            path.closeSubpath()
            p.setBrush(QBrush(QColor("#FFFFFF")))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawPath(path)

        font = QFont("Segoe UI", 13)
        font.setWeight(QFont.Weight.Bold)
        p.setFont(font)
        p.setPen(QColor("#FFFFFF"))
        p.drawText(36, 0, self.width() - 48, self.height(), Qt.AlignmentFlag.AlignVCenter, self._text)

        p.end()


class StatusFooter(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(28)
        self._message = "Ready"
        self._level = "idle"

    def set_message(self, text, level="info"):
        self._message = text
        self._level = level
        self.update()

    def showMessage(self, text):
        self.set_message(text)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        colors = {
            "idle": "#3D3756",
            "info": "#6C5CE7",
            "success": "#22C55E",
            "warning": "#F59E0B",
            "error": "#EF4444",
        }
        color = QColor(colors.get(self._level, colors["idle"]))

        p.setBrush(QBrush(color))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(0, 10, 6, 6)

        font = QFont("Segoe UI", 11)
        font.setWeight(QFont.Weight.Medium)
        p.setFont(font)
        p.setPen(QColor("#6B6878"))
        p.drawText(14, 0, self.width() - 14, self.height(), Qt.AlignmentFlag.AlignVCenter, self._message)

        p.end()


class ClearButton(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(32, 32)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._hovered = False
        self._callback = None
        self.setToolTip("Clear Console")

    def set_click_callback(self, callback):
        self._callback = callback

    def enterEvent(self, event):
        self._hovered = True
        self.update()

    def leaveEvent(self, event):
        self._hovered = False
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._callback:
            self._callback()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        if self._hovered:
            bg = QPainterPath()
            bg.addRoundedRect(0, 0, 32, 32, 8, 8)
            p.setBrush(QBrush(QColor("#1A1726")))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawPath(bg)

        color = QColor("#9CA3AF") if self._hovered else QColor("#4A4458")
        p.setPen(QPen(color, 1.6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.setBrush(Qt.BrushStyle.NoBrush)

        cx, cy = 16, 16
        p.drawRoundedRect(cx - 5, cy - 3, 10, 8, 1.5, 1.5)
        p.drawLine(cx - 6, cy - 3, cx + 6, cy - 3)
        p.drawLine(cx - 2, cy - 6, cx + 2, cy - 6)
        p.drawLine(cx - 2, cy, cx - 2, cy + 3)
        p.drawLine(cx + 2, cy, cx + 2, cy + 3)

        p.end()


class ConsolePanel(QFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.setStyleSheet("background: transparent; border: none;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)
        header_row.setSpacing(8)

        self.header = ConsoleHeader()
        header_row.addWidget(self.header, 1)

        self.clear_btn = ClearButton()
        self.clear_btn.set_click_callback(self._clear_console)
        header_row.addWidget(self.clear_btn)

        layout.addLayout(header_row)

        self.console = ConsoleOutput()
        layout.addWidget(self.console, 1)
        set_console_instance(self.console)

        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(0, 0, 0, 0)
        footer_layout.setSpacing(12)

        self.control_btn = ControlButton("Start Bot")
        self.control_btn.set_click_callback(self.toggle_start_stop)
        self.control_btn.setFixedWidth(160)
        footer_layout.addWidget(self.control_btn)

        self.status_bar = StatusFooter()
        footer_layout.addWidget(self.status_bar, 1)

        layout.addLayout(footer_layout)

    def toggle_start_stop(self):
        self.parent.is_running = not self.parent.is_running
        self.control_btn.set_running(self.parent.is_running)
        self.header.set_active(self.parent.is_running)

        if hasattr(self.parent, 'set_running'):
            self.parent.set_running(self.parent.is_running)

        if self.parent.is_running:
            self.status_bar.set_message("Bot started", "success")
            run_start_logic(self.status_bar)
        else:
            stop_bot()
            self.status_bar.set_message("Bot stopped", "idle")

    def _clear_console(self):
        self.console.clear()
        self.console.append_message("Console cleared", "system")