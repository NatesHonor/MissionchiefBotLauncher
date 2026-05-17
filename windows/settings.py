import os
import sys
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import (
    QColor, QPainter, QPainterPath, QLinearGradient, QBrush,
    QPen, QFont, QRadialGradient, QSyntaxHighlighter, QTextCharFormat
)
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QFrame, QGraphicsDropShadowEffect, QLabel
)

from widgets.action_button import ActionButton
from utils.integrity import run_integrity_check


class IniHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._section_fmt = QTextCharFormat()
        self._section_fmt.setForeground(QColor("#A855F7"))
        self._section_fmt.setFontWeight(QFont.Weight.Bold)

        self._key_fmt = QTextCharFormat()
        self._key_fmt.setForeground(QColor("#EC4899"))

        self._value_fmt = QTextCharFormat()
        self._value_fmt.setForeground(QColor("#C9C8D0"))

        self._equals_fmt = QTextCharFormat()
        self._equals_fmt.setForeground(QColor("#4A4458"))

        self._comment_fmt = QTextCharFormat()
        self._comment_fmt.setForeground(QColor("#3D3756"))
        self._comment_fmt.setFontItalic(True)

    def highlightBlock(self, text):
        stripped = text.strip()

        if stripped.startswith("[") and "]" in stripped:
            self.setFormat(0, len(text), self._section_fmt)

        elif stripped.startswith("#") or stripped.startswith(";"):
            self.setFormat(0, len(text), self._comment_fmt)

        elif "=" in text:
            idx = text.index("=")
            self.setFormat(0, idx, self._key_fmt)
            self.setFormat(idx, 1, self._equals_fmt)
            self.setFormat(idx + 1, len(text) - idx - 1, self._value_fmt)


class SettingsSectionHeader(QWidget):
    def __init__(self, title, description="", icon_type="settings", accent="#A855F7", parent=None):
        super().__init__(parent)
        self.setFixedHeight(64)
        self._title = title
        self._description = description
        self._icon_type = icon_type
        self._accent = QColor(accent)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        icon_x, icon_y = 0, 8
        icon_size = 48

        bg_gradient = QLinearGradient(icon_x, icon_y, icon_x + icon_size, icon_y + icon_size)
        bg_gradient.setColorAt(0.0, QColor(self._accent.red(), self._accent.green(), self._accent.blue(), 25))
        bg_gradient.setColorAt(1.0, QColor(self._accent.red(), self._accent.green(), self._accent.blue(), 10))
        p.setBrush(QBrush(bg_gradient))
        p.setPen(QPen(QColor(self._accent.red(), self._accent.green(), self._accent.blue(), 40), 1))
        icon_path = QPainterPath()
        icon_path.addRoundedRect(icon_x, icon_y, icon_size, icon_size, 14, 14)
        p.drawPath(icon_path)

        cx = icon_x + icon_size / 2
        cy = icon_y + icon_size / 2
        p.setPen(QPen(self._accent, 1.8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        p.setBrush(Qt.BrushStyle.NoBrush)

        if self._icon_type == "settings":
            import math
            p.drawEllipse(int(cx - 4), int(cy - 4), 8, 8)
            for a in range(0, 360, 45):
                rad = math.radians(a)
                x1 = cx + 6 * math.cos(rad)
                y1 = cy + 6 * math.sin(rad)
                x2 = cx + 9 * math.cos(rad)
                y2 = cy + 9 * math.sin(rad)
                p.drawLine(int(x1), int(y1), int(x2), int(y2))

        elif self._icon_type == "file":
            p.drawRoundedRect(int(cx - 7), int(cy - 9), 14, 18, 2, 2)
            p.drawLine(int(cx - 4), int(cy - 3), int(cx + 4), int(cy - 3))
            p.drawLine(int(cx - 4), int(cy + 1), int(cx + 4), int(cy + 1))
            p.drawLine(int(cx - 4), int(cy + 5), int(cx + 2), int(cy + 5))

        elif self._icon_type == "repair":
            p.drawLine(int(cx - 6), int(cy + 6), int(cx + 2), int(cy - 2))
            p.drawEllipse(int(cx + 0), int(cy - 6), 8, 8)

        text_x = icon_x + icon_size + 16

        title_font = QFont("Segoe UI", 15)
        title_font.setWeight(QFont.Weight.Bold)
        p.setFont(title_font)
        p.setPen(QColor("#F1F0F5"))
        p.drawText(text_x, 8, self.width() - text_x, 26, Qt.AlignmentFlag.AlignVCenter, self._title)

        if self._description:
            desc_font = QFont("Segoe UI", 11)
            desc_font.setWeight(QFont.Weight.Normal)
            p.setFont(desc_font)
            p.setPen(QColor("#4A4458"))
            p.drawText(text_x, 34, self.width() - text_x, 22, Qt.AlignmentFlag.AlignVCenter, self._description)

        p.end()


class SaveNotification(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(40)
        self.setVisible(False)
        self._opacity = 0.0
        self._message = ""
        self._level = "success"
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._fade_out)
        self._fade_timer = QTimer(self)
        self._fade_timer.timeout.connect(self._animate_fade)
        self._fading_in = False
        self._fading_out = False

    def show_message(self, text, level="success", duration=3000):
        self._message = text
        self._level = level
        self._opacity = 0.0
        self._fading_in = True
        self._fading_out = False
        self.setVisible(True)
        self._fade_timer.start(16)
        self._timer.start(duration)

    def _fade_out(self):
        self._fading_in = False
        self._fading_out = True
        self._fade_timer.start(16)

    def _animate_fade(self):
        if self._fading_in:
            self._opacity = min(1.0, self._opacity + 0.08)
            if self._opacity >= 1.0:
                self._fading_in = False
                self._fade_timer.stop()
        elif self._fading_out:
            self._opacity = max(0.0, self._opacity - 0.06)
            if self._opacity <= 0.0:
                self._fading_out = False
                self._fade_timer.stop()
                self.setVisible(False)
        self.update()

    def paintEvent(self, event):
        if self._opacity <= 0:
            return

        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setOpacity(self._opacity)

        colors = {
            "success": ("#22C55E", "✓"),
            "error": ("#EF4444", "✗"),
            "warning": ("#F59E0B", "⚠"),
            "info": ("#6C5CE7", "◆"),
        }
        color_hex, icon = colors.get(self._level, colors["info"])
        color = QColor(color_hex)

        bg = QPainterPath()
        bg.addRoundedRect(0, 0, self.width(), self.height(), 10, 10)
        p.setBrush(QBrush(QColor(color.red(), color.green(), color.blue(), 15)))
        p.setPen(QPen(QColor(color.red(), color.green(), color.blue(), 50), 1))
        p.drawPath(bg)

        p.setBrush(QBrush(color))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(14, 12, 6, 6)

        font = QFont("Segoe UI", 12)
        font.setWeight(QFont.Weight.DemiBold)
        p.setFont(font)
        p.setPen(color)
        p.drawText(28, 0, self.width() - 40, self.height(), Qt.AlignmentFlag.AlignVCenter, f"{icon}  {self._message}")

        p.end()


class ConfigEditor(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QTextEdit {
                background-color: #08070D;
                color: #C9C8D0;
                border: 1px solid #1A1726;
                border-radius: 10px;
                padding: 14px 16px;
                font-family: 'Cascadia Code', 'Fira Code', 'Consolas', monospace;
                font-size: 13px;
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
        self._highlighter = IniHighlighter(self.document())


class LineCountLabel(QWidget):
    def __init__(self, editor, parent=None):
        super().__init__(parent)
        self.setFixedHeight(24)
        self._editor = editor
        self._editor.textChanged.connect(self.update)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        line_count = self._editor.document().blockCount()
        char_count = len(self._editor.toPlainText())

        font = QFont("Segoe UI", 10)
        font.setWeight(QFont.Weight.Medium)
        p.setFont(font)
        p.setPen(QColor("#3D3756"))

        text = f"{line_count} lines  •  {char_count} chars"
        p.drawText(0, 0, self.width(), self.height(), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight, text)

        p.end()


class ProfileHandler(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setStyleSheet("background: transparent; border: none;")
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = SettingsSectionHeader(
            "Configuration",
            "Edit config.ini for bot settings",
            "file",
            "#A855F7"
        )
        layout.addWidget(header)
        layout.addSpacing(16)

        editor_card = QFrame()
        editor_card.setStyleSheet("""
            QFrame {
                background-color: #0E0C15;
                border: 1px solid #1A1726;
                border-radius: 12px;
            }
        """)
        shadow = QGraphicsDropShadowEffect(editor_card)
        shadow.setBlurRadius(24)
        shadow.setColor(QColor(0, 0, 0, 50))
        shadow.setOffset(0, 4)
        editor_card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(editor_card)
        card_layout.setContentsMargins(2, 2, 2, 8)
        card_layout.setSpacing(4)

        self.text_edit = ConfigEditor()

        base_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.abspath(".")
        self.config_path = os.path.join(base_dir, "bot", "config.ini")

        if os.path.exists(self.config_path):
            with open(self.config_path, "r") as f:
                self.text_edit.setText(f.read())
        else:
            self.text_edit.setReadOnly(True)
            self.text_edit.setText("# Config.ini not available until setup is complete.")

        card_layout.addWidget(self.text_edit, 1)

        self.line_counter = LineCountLabel(self.text_edit)
        counter_layout = QHBoxLayout()
        counter_layout.setContentsMargins(8, 0, 12, 0)
        counter_layout.addStretch()
        counter_layout.addWidget(self.line_counter)
        card_layout.addLayout(counter_layout)

        layout.addWidget(editor_card, 1)
        layout.addSpacing(12)

        self.notification = SaveNotification()
        layout.addWidget(self.notification)
        layout.addSpacing(8)

        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(10)

        self.save_btn = ActionButton("Save Config", style="primary", icon_type="save")
        self.save_btn.clicked.connect(self.save_config)
        btn_layout.addWidget(self.save_btn, 1)

        self.repair_btn = ActionButton("Repair", style="danger", icon_type="refresh")
        self.repair_btn.clicked.connect(self._run_repair)
        btn_layout.addWidget(self.repair_btn, 1)

        layout.addLayout(btn_layout)

    def save_config(self):
        if not os.path.exists(self.config_path):
            self.notification.show_message("Config.ini is missing — run repair first", "error")
            return
        try:
            with open(self.config_path, "w") as f:
                f.write(self.text_edit.toPlainText())
            self.notification.show_message("Configuration saved successfully", "success")
            if self.parent and hasattr(self.parent, "status_bar"):
                self.parent.status_bar.showMessage("Settings saved")
        except Exception as e:
            self.notification.show_message(f"Save failed: {e}", "error")

    def _run_repair(self):
        self.notification.show_message("Running integrity check...", "info")
        try:
            run_integrity_check()
            self.notification.show_message("Repair completed successfully", "success")
            if os.path.exists(self.config_path):
                with open(self.config_path, "r") as f:
                    self.text_edit.setText(f.read())
                self.text_edit.setReadOnly(False)
        except Exception as e:
            self.notification.show_message(f"Repair failed: {e}", "error")