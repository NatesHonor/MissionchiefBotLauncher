import configparser
import html
import os
import sys
import requests
import subprocess
from pathlib import Path
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect, QPoint, QSize, QObject, QThread, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QFont, QColor, QPainter, QPainterPath, QLinearGradient, QBrush, QPen, QRadialGradient
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextBrowser, QProgressBar, QApplication, QGraphicsDropShadowEffect,
    QWidget, QFrame, QGraphicsOpacityEffect, QSizePolicy
)
from handlers.console import send_error, send_success, send_system, send_warning
from handlers.logging import log_error, log_exception, log_info
from utils.paths import LAUNCHER_CONFIG
from utils.localization import tr
from utils.settings_store import get as get_setting, parse_version

API_URL = os.environ.get("MISSION_HELPER_LAUNCHER_UPDATE_URL", "https://api.natemarcellus.com/updates/missionlauncher")
BOT_UPDATE_API_URL = os.environ.get("MISSION_HELPER_BOT_UPDATE_URL", "https://api.natemarcellus.com/updates/missionchief")
INI_FILE = str(LAUNCHER_CONFIG)


def format_changelog_html(notes):
    def safe(value):
        return html.escape(str(value))

    if isinstance(notes, dict):
        html = ""
        category_colors = {
            "Design": "#2583E8",
            "Functionality": "#1D65D8",
            "Bug Fixes": "#21B8D4",
            "Performance": "#32B9E8",
            "Security": "#EF4444",
            "Other": "#27C4E8",
        }
        for category, items in notes.items():
            color = category_colors.get(category, "#2583E8")
            html += f"""
                <div style="margin-bottom: 14px;">
                    <div style="
                        display: inline-block;
                        color: {color};
                        font-size: 11px;
                        font-weight: 700;
                        letter-spacing: 1.5px;
                        text-transform: uppercase;
                        margin-bottom: 6px;
                        padding: 3px 0;
                        border-bottom: 1px solid {color}40;
                    ">
                        ◆&nbsp; {safe(category).upper()}
                    </div>
                    <div style="margin-left: 4px;">
            """
            if isinstance(items, list):
                for item in items:
                    html += f"""
                        <div style="
                            color: #C7D8EA;
                            font-size: 13px;
                            padding: 3px 0 3px 12px;
                            line-height: 1.5;
                        ">
                            <span style="color: {color}80;">●</span>&nbsp;&nbsp;{safe(item)}
                        </div>
                    """
            elif isinstance(items, str):
                html += f"""
                    <div style="
                        color: #C7D8EA;
                        font-size: 13px;
                        padding: 3px 0 3px 12px;
                        line-height: 1.5;
                    ">
                        <span style="color: {color}80;">●</span>&nbsp;&nbsp;{safe(items)}
                    </div>
                """
            html += "</div></div>"
        return html

    elif isinstance(notes, list):
        html = ""
        for item in notes:
            html += f"""
                <div style="
                    color: #C7D8EA;
                    font-size: 13px;
                    padding: 3px 0 3px 12px;
                    line-height: 1.5;
                ">
                    <span style="color: #2583E880;">●</span>&nbsp;&nbsp;{safe(item)}
                </div>
            """
        return html

    elif isinstance(notes, str):
        return f'<div style="color: #C7D8EA; font-size: 13px; padding: 8px 0;">{safe(notes)}</div>'

    return f'<div style="color: #6688A6; font-size: 13px;">{html.escape(tr("no_details"))}</div>'


class AccentBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(3)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        gradient = QLinearGradient(0, 0, self.width(), 0)
        gradient.setColorAt(0.0, QColor("#1D65D8"))
        gradient.setColorAt(0.3, QColor("#2583E8"))
        gradient.setColorAt(0.6, QColor("#21B8D4"))
        gradient.setColorAt(1.0, QColor("#32B9E8"))
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 1.5, 1.5)
        painter.drawPath(path)


class UpdateIcon(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(56, 56)
        self._pulse = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)
        self._timer.start(40)
        self._direction = 1

    def _animate(self):
        self._pulse += self._direction * 2
        if self._pulse >= 100:
            self._direction = -1
        elif self._pulse <= 0:
            self._direction = 1
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pulse_factor = self._pulse / 100.0
        glow_opacity = int(20 + pulse_factor * 30)
        glow_gradient = QRadialGradient(28, 28, 28)
        glow_gradient.setColorAt(0.0, QColor(37, 131, 232, glow_opacity))
        glow_gradient.setColorAt(1.0, QColor(37, 131, 232, 0))
        painter.setBrush(QBrush(glow_gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(0, 0, 56, 56)
        bg_gradient = QLinearGradient(8, 8, 48, 48)
        bg_gradient.setColorAt(0.0, QColor("#1D65D8"))
        bg_gradient.setColorAt(1.0, QColor("#2583E8"))
        painter.setBrush(QBrush(bg_gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        path = QPainterPath()
        path.addRoundedRect(8, 8, 40, 40, 12, 12)
        painter.drawPath(path)
        painter.setPen(QPen(QColor("#FFFFFF"), 2.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawLine(28, 18, 28, 34)
        painter.drawLine(28, 34, 22, 28)
        painter.drawLine(28, 34, 34, 28)
        painter.drawLine(18, 38, 38, 38)


class MandatoryIcon(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(56, 56)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        glow_gradient = QRadialGradient(28, 28, 28)
        glow_gradient.setColorAt(0.0, QColor(239, 68, 68, 40))
        glow_gradient.setColorAt(1.0, QColor(239, 68, 68, 0))
        painter.setBrush(QBrush(glow_gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(0, 0, 56, 56)
        bg_gradient = QLinearGradient(8, 8, 48, 48)
        bg_gradient.setColorAt(0.0, QColor("#EF4444"))
        bg_gradient.setColorAt(1.0, QColor("#DC2626"))
        painter.setBrush(QBrush(bg_gradient))
        path = QPainterPath()
        path.addRoundedRect(8, 8, 40, 40, 12, 12)
        painter.drawPath(path)
        painter.setPen(QPen(QColor("#FFFFFF"), 2.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawLine(28, 19, 28, 31)
        painter.setBrush(QBrush(QColor("#FFFFFF")))
        painter.drawEllipse(26, 35, 4, 4)


class GradientProgressBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(6)
        self._value = 0
        self._animated_value = 0.0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._step)
        self._indeterminate = True
        self._sweep = 0

    def setValue(self, val):
        self._value = val
        self._indeterminate = False
        if not self._timer.isActive():
            self._timer.start(16)

    def startIndeterminate(self):
        self._indeterminate = True
        self._sweep = 0
        if not self._timer.isActive():
            self._timer.start(16)

    def _step(self):
        if self._indeterminate:
            self._sweep = (self._sweep + 3) % 360
        else:
            diff = self._value - self._animated_value
            if abs(diff) < 0.5:
                self._animated_value = self._value
            else:
                self._animated_value += diff * 0.12
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        bg_path = QPainterPath()
        bg_path.addRoundedRect(0, 0, self.width(), self.height(), 3, 3)
        painter.setBrush(QBrush(QColor("#102640")))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPath(bg_path)
        if self._indeterminate:
            center = (self._sweep / 360.0) * (self.width() + 120) - 60
            bar_width = 120
            x_start = max(0, center - bar_width / 2)
            x_end = min(self.width(), center + bar_width / 2)
            if x_end > x_start:
                gradient = QLinearGradient(x_start, 0, x_end, 0)
                gradient.setColorAt(0.0, QColor(29, 101, 216, 0))
                gradient.setColorAt(0.5, QColor(37, 131, 232, 255))
                gradient.setColorAt(1.0, QColor(33, 184, 212, 0))
                fill_path = QPainterPath()
                fill_path.addRoundedRect(x_start, 0, x_end - x_start, self.height(), 3, 3)
                painter.setBrush(QBrush(gradient))
                painter.drawPath(fill_path)
        else:
            fill_width = (self._animated_value / 100.0) * self.width()
            if fill_width > 0:
                gradient = QLinearGradient(0, 0, self.width(), 0)
                gradient.setColorAt(0.0, QColor("#1D65D8"))
                gradient.setColorAt(0.5, QColor("#2583E8"))
                gradient.setColorAt(1.0, QColor("#21B8D4"))
                fill_path = QPainterPath()
                fill_path.addRoundedRect(0, 0, fill_width, self.height(), 3, 3)
                painter.setBrush(QBrush(gradient))
                painter.drawPath(fill_path)


class UpdateDialog(QDialog):
    def __init__(self, parent, remote_version, local_version, notes, mandatory, download_url):
        super().__init__(parent)
        self.download_url = download_url
        self.mandatory = mandatory
        self.remote_version = remote_version
        self._drag_pos = None
        self.setWindowTitle(tr("update_available"))
        self.setFixedSize(520, 580)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        self.container = QWidget(self)
        self.container.setGeometry(0, 0, 520, 580)
        self.container.setStyleSheet("""
            QWidget {
                background-color: #0B1B2D;
                border-radius: 16px;
                border: 1px solid #1D3B5B;
            }
        """)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(50)
        shadow.setColor(QColor(0, 0, 0, 180))
        shadow.setOffset(0, 10)
        self.container.setGraphicsEffect(shadow)

        main_layout = QVBoxLayout(self.container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        accent_bar = AccentBar()
        main_layout.addWidget(accent_bar)

        close_bar = QHBoxLayout()
        close_bar.setContentsMargins(0, 8, 12, 0)
        close_bar.addStretch()
        if not mandatory:
            close_btn = QPushButton("✕")
            close_btn.setFixedSize(28, 28)
            close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            close_btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    color: #6688A6;
                    font-size: 14px;
                    font-weight: 600;
                    border: none;
                    border-radius: 14px;
                }
                QPushButton:hover {
                    background: #102640;
                    color: #A8BCD1;
                }
            """)
            close_btn.clicked.connect(self.reject)
            close_bar.addWidget(close_btn)
        main_layout.addLayout(close_bar)

        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(32, 4, 32, 28)
        content_layout.setSpacing(0)

        header_row = QHBoxLayout()
        header_row.setSpacing(16)

        if mandatory:
            icon = MandatoryIcon()
        else:
            icon = UpdateIcon()
        header_row.addWidget(icon)

        title_block = QVBoxLayout()
        title_block.setSpacing(4)

        title_text = tr("required_update") if mandatory else tr("update_available")
        title_label = QLabel(title_text)
        title_label.setStyleSheet("""
            QLabel {
                color: #EAF4FF;
                font-size: 20px;
                font-weight: 700;
                background: transparent;
                border: none;
            }
        """)
        title_block.addWidget(title_label)

        version_label = QLabel(f"v{local_version}  →  v{remote_version}")
        version_label.setStyleSheet("""
            QLabel {
                color: #7F9DB8;
                font-size: 13px;
                font-weight: 500;
                background: transparent;
                border: none;
            }
        """)
        title_block.addWidget(version_label)

        header_row.addLayout(title_block)
        header_row.addStretch()

        if mandatory:
            req_badge = QLabel("REQUIRED")
            req_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            req_badge.setFixedSize(80, 26)
            req_badge.setStyleSheet("""
                QLabel {
                    background-color: rgba(239, 68, 68, 0.15);
                    color: #EF4444;
                    font-size: 10px;
                    font-weight: 700;
                    letter-spacing: 1.5px;
                    border-radius: 13px;
                    border: 1px solid rgba(239, 68, 68, 0.3);
                }
            """)
            header_row.addWidget(req_badge, alignment=Qt.AlignmentFlag.AlignTop)

        content_layout.addLayout(header_row)
        content_layout.addSpacing(20)

        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setFixedHeight(1)
        divider.setStyleSheet("QFrame { background-color: #102640; border: none; }")
        content_layout.addWidget(divider)

        content_layout.addSpacing(20)

        section_header = QHBoxLayout()
        section_header.setSpacing(8)

        dot = QLabel("●")
        dot.setStyleSheet("""
            QLabel {
                color: #2583E8;
                font-size: 8px;
                background: transparent;
                border: none;
            }
        """)
        section_header.addWidget(dot, alignment=Qt.AlignmentFlag.AlignVCenter)

        changelog_title = QLabel(tr("changelog"))
        changelog_title.setStyleSheet("""
            QLabel {
                color: #A8BCD1;
                font-size: 11px;
                font-weight: 700;
                letter-spacing: 2px;
                background: transparent;
                border: none;
            }
        """)
        section_header.addWidget(changelog_title)
        section_header.addStretch()
        content_layout.addLayout(section_header)

        content_layout.addSpacing(10)

        self.changelog_box = QTextBrowser()
        self.changelog_box.setOpenExternalLinks(False)
        self.changelog_box.setMinimumHeight(200)
        self.changelog_box.setStyleSheet("""
            QTextBrowser {
                background-color: #07111F;
                color: #C7D8EA;
                border: 1px solid #1D3B5B;
                border-radius: 10px;
                padding: 16px 18px;
                font-size: 13px;
                font-family: 'Segoe UI', sans-serif;
                selection-background-color: #2583E8;
                selection-color: #FFFFFF;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 6px;
                margin: 4px 0;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical {
                background: #1D3B5B;
                border-radius: 3px;
                min-height: 40px;
            }
            QScrollBar::handle:vertical:hover {
                background: #2583E8;
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

        changelog_html = format_changelog_html(notes)
        self.changelog_box.setHtml(f"""
            <div style="font-family: 'Segoe UI', sans-serif;">
                {changelog_html}
            </div>
        """)
        content_layout.addWidget(self.changelog_box)

        content_layout.addSpacing(12)

        self.progress_container = QWidget()
        self.progress_container.setStyleSheet("QWidget { background: transparent; border: none; }")
        progress_inner = QVBoxLayout(self.progress_container)
        progress_inner.setContentsMargins(0, 0, 0, 0)
        progress_inner.setSpacing(8)

        self.progress_bar = GradientProgressBar()
        progress_inner.addWidget(self.progress_bar)

        self.status_label = QLabel(tr("preparing_update"))
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                color: #7F9DB8;
                font-size: 12px;
                font-weight: 500;
                background: transparent;
                border: none;
            }
        """)
        progress_inner.addWidget(self.status_label)

        self.progress_container.setVisible(False)
        content_layout.addWidget(self.progress_container)

        content_layout.addSpacing(8)

        self.btn_container = QWidget()
        self.btn_container.setStyleSheet("QWidget { background: transparent; border: none; }")
        btn_layout = QHBoxLayout(self.btn_container)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(12)

        if not mandatory:
            self.skip_btn = QPushButton(tr("skip"))
            self.skip_btn.setFixedHeight(44)
            self.skip_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.skip_btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    color: #7890AD;
                    font-size: 13px;
                    font-weight: 600;
                    border: 1px solid #1D3B5B;
                    border-radius: 10px;
                    padding: 0 28px;
                }
                QPushButton:hover {
                    color: #A8BCD1;
                    border-color: #2D537A;
                    background: rgba(16, 38, 64, 0.5);
                }
                QPushButton:pressed {
                    background: #102640;
                    color: #C7D8EA;
                }
            """)
            self.skip_btn.clicked.connect(self.reject)
            btn_layout.addWidget(self.skip_btn)

        self.update_btn = QPushButton(tr("install_update"))
        self.update_btn.setFixedHeight(44)
        self.update_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.update_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1D65D8, stop:0.5 #2583E8, stop:1 #21B8D4);
                color: #FFFFFF;
                font-size: 14px;
                font-weight: 700;
                border: none;
                border-radius: 10px;
                padding: 0 36px;
                letter-spacing: 0.3px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3B82F6, stop:0.5 #4BA3FF, stop:1 #32B9E8);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #164EA8, stop:0.5 #1D65D8, stop:1 #168BA7);
            }
        """)
        self.update_btn.clicked.connect(self._on_install)
        btn_layout.addWidget(self.update_btn)

        content_layout.addWidget(self.btn_container)
        main_layout.addLayout(content_layout)

    def _on_install(self):
        self.update_btn.setEnabled(False)
        self.update_btn.setText(tr("installing"))
        self.update_btn.setStyleSheet("""
            QPushButton {
                background: #102640;
                color: #6688A6;
                font-size: 14px;
                font-weight: 700;
                border: 1px solid #1D3B5B;
                border-radius: 10px;
                padding: 0 36px;
            }
        """)
        if hasattr(self, "skip_btn"):
            self.skip_btn.setEnabled(False)
            self.skip_btn.setVisible(False)

        self.changelog_box.setVisible(False)
        self.progress_container.setVisible(True)
        self.progress_bar.startIndeterminate()
        self.status_label.setText(tr("launching_updater"))

        self.setFixedSize(520, 320)
        self.container.setGeometry(0, 0, 520, 320)

        QTimer.singleShot(800, self._start_updater)

    def _start_updater(self):
        if run_updater(self.download_url):
            return
        self.status_label.setText(tr("self_update_source"))
        self.progress_bar.setValue(0)
        self.update_btn.setEnabled(True)
        self.update_btn.setText(tr("install_update"))
        if hasattr(self, "skip_btn"):
            self.skip_btn.setVisible(True)
            self.skip_btn.setEnabled(True)
        self.changelog_box.setVisible(True)
        self.progress_container.setVisible(False)
        self.setFixedSize(520, 580)
        self.container.setGeometry(0, 0, 520, 580)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None

    def closeEvent(self, event):
        if self.mandatory:
            event.ignore()
        else:
            super().closeEvent(event)


class _UpdateCheckWorker(QObject):
    result = pyqtSignal(object)

    def __init__(self, current_version=""):
        super().__init__()
        self.current_version = current_version

    @pyqtSlot()
    def run(self):
        try:
            params = {"current_version": self.current_version} if self.current_version else {}
            response = requests.get(API_URL, params=params, timeout=(5, 15), headers={"User-Agent": "MissionHelper-Launcher"})
            response.raise_for_status()
            data = response.json()
            self.result.emit(data if isinstance(data, dict) else None)
        except Exception as exc:
            log_info(f"Launcher update check unavailable: {exc}")
            self.result.emit(None)


class _UpdateResultReceiver(QObject):
    def __init__(self, parent, callback):
        super().__init__(parent)
        self._callback = callback

    @pyqtSlot(object)
    def handle(self, data):
        self._callback(data)


def _show_update_data(parent, data):
    if not data:
        return
    try:
        config = configparser.ConfigParser()
        config.read(INI_FILE, encoding="utf-8")
        local_version = config.get("Launcher", "version", fallback="0.0.0").strip()
        remote_version = str(data.get("version", "")).strip()
        download_url = str(data.get("url", "")).strip()
        if not remote_version or not download_url or parse_version(remote_version) <= parse_version(local_version):
            if hasattr(parent, "sidebar"):
                parent.sidebar.apply_update_info(remote_version or local_version)
            return
        if hasattr(parent, "sidebar"):
            parent.sidebar.apply_update_info(remote_version, bool(data.get("mandatory", False)))
        dialog = UpdateDialog(
            parent,
            remote_version,
            local_version,
            data.get("notes", {}),
            bool(data.get("mandatory", False)),
            download_url,
        )
        result = dialog.exec()
        if result == QDialog.DialogCode.Rejected and not bool(data.get("mandatory", False)):
            parent.update_declined_this_session = True
    except Exception:
        log_exception("Could not display launcher update information")


def check_updates(parent):
    """Check for launcher updates in the background so startup stays responsive."""
    if getattr(parent, "update_declined_this_session", False):
        return False
    if get_setting("check_updates_on_start", "true").lower() not in {"1", "true", "yes", "on"}:
        return False
    existing = getattr(parent, "_update_thread", None)
    if existing is not None and existing.isRunning():
        return False

    thread = QThread(parent)
    config = configparser.ConfigParser()
    config.read(INI_FILE, encoding="utf-8")
    local_version = config.get("Launcher", "version", fallback="0.0.0").strip()
    worker = _UpdateCheckWorker(local_version)
    receiver = _UpdateResultReceiver(parent, lambda data: _show_update_data(parent, data))
    worker.moveToThread(thread)
    thread.started.connect(worker.run)
    worker.result.connect(receiver.handle)
    worker.result.connect(thread.quit)
    worker.result.connect(worker.deleteLater)
    thread.finished.connect(thread.deleteLater)
    thread.finished.connect(lambda: setattr(parent, "_update_thread", None))
    parent._update_thread = thread
    parent._update_worker = worker
    parent._update_receiver = receiver
    thread.start()
    return False


def run_updater(download_url):
    """Hand a packaged launcher update to the next-process updater mode."""
    if not getattr(sys, "frozen", False):
        send_warning("Launcher self-update is available only in packaged builds")
        log_info("Skipped self-update because launcher is running from source")
        return False
    target = Path(sys.executable).resolve()
    try:
        subprocess.Popen(
            [str(target), "--apply-update", str(download_url), str(target), str(os.getpid())],
            cwd=str(target.parent),
            close_fds=True,
        )
        QApplication.quit()
        return True
    except OSError as exc:
        send_error(f"Could not start launcher updater: {exc}")
        log_exception("Could not start packaged launcher updater")
        return False


def run_update_check(version, config_file=None, status_bar=None):
    """Update the nested bot safely, keeping the operator's configuration."""
    if not version:
        return False

    def status(message):
        if status_bar is not None:
            try:
                status_bar.showMessage(message)
            except Exception:
                log_exception("Could not update launcher status bar")

    try:
        response = requests.get(
            BOT_UPDATE_API_URL,
            params={"current_version": version},
            timeout=(5, 20),
            headers={"User-Agent": "MissionHelper-Launcher"},
        )
        response.raise_for_status()
        data = response.json()
        latest_version = str(data.get("version", "")).strip()
        update_url = str(data.get("url", "")).strip()
        if not latest_version or parse_version(latest_version) <= parse_version(version):
            return False
        if not update_url.lower().startswith(("http://", "https://")):
            raise RuntimeError("Bot update response did not contain a valid download URL")

        send_system(f"Bot update available: {latest_version}")
        status(f"Updating bot to {latest_version}...")
        from utils.install import _cleanup_temp, _deploy_files, _extract_release

        with requests.get(update_url, stream=True, timeout=(10, 90), headers={"User-Agent": "MissionHelper-Launcher"}) as update_response:
            update_response.raise_for_status()
            data_bytes = update_response.content
        source_dir = _extract_release(data_bytes, status_bar)
        _deploy_files(source_dir, status_bar)
        _cleanup_temp()
        send_success(f"Bot updated to {latest_version}")
        log_info(f"Bot update applied: {version} -> {latest_version}")
        status(f"Bot updated to {latest_version}")
        return True
    except Exception as exc:
        send_warning(f"Bot update check failed: {exc}")
        log_exception("Bot update check failed")
        if status_bar is not None:
            status("Bot update skipped")
        return False
