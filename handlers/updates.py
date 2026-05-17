import os
import sys
import shutil
import zipfile
import requests
import subprocess
import configparser
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect, QPoint, QSize
from PyQt6.QtGui import QFont, QColor, QPainter, QPainterPath, QLinearGradient, QBrush, QPen, QRadialGradient
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextBrowser, QProgressBar, QApplication, QGraphicsDropShadowEffect,
    QWidget, QFrame, QGraphicsOpacityEffect, QSizePolicy
)
from handlers.console import send_messages

API_URL = "https://api.natemarcellus.com/updates/missionlauncher"
INI_FILE = "launcher_settings.ini"


def format_changelog_html(notes):
    if isinstance(notes, dict):
        html = ""
        category_colors = {
            "Design": "#A855F7",
            "Functionality": "#6C5CE7",
            "Bug Fixes": "#EC4899",
            "Performance": "#F97316",
            "Security": "#EF4444",
            "Other": "#53D8FB",
        }
        for category, items in notes.items():
            color = category_colors.get(category, "#A855F7")
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
                        ◆&nbsp; {category.upper()}
                    </div>
                    <div style="margin-left: 4px;">
            """
            if isinstance(items, list):
                for item in items:
                    html += f"""
                        <div style="
                            color: #C9C8D0;
                            font-size: 13px;
                            padding: 3px 0 3px 12px;
                            line-height: 1.5;
                        ">
                            <span style="color: {color}80;">●</span>&nbsp;&nbsp;{item}
                        </div>
                    """
            elif isinstance(items, str):
                html += f"""
                    <div style="
                        color: #C9C8D0;
                        font-size: 13px;
                        padding: 3px 0 3px 12px;
                        line-height: 1.5;
                    ">
                        <span style="color: {color}80;">●</span>&nbsp;&nbsp;{items}
                    </div>
                """
            html += "</div></div>"
        return html

    elif isinstance(notes, list):
        html = ""
        for item in notes:
            html += f"""
                <div style="
                    color: #C9C8D0;
                    font-size: 13px;
                    padding: 3px 0 3px 12px;
                    line-height: 1.5;
                ">
                    <span style="color: #A855F780;">●</span>&nbsp;&nbsp;{item}
                </div>
            """
        return html

    elif isinstance(notes, str):
        return f'<div style="color: #C9C8D0; font-size: 13px; padding: 8px 0;">{notes}</div>'

    return '<div style="color: #4A4458; font-size: 13px;">No details provided.</div>'


class AccentBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(3)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        gradient = QLinearGradient(0, 0, self.width(), 0)
        gradient.setColorAt(0.0, QColor("#6C5CE7"))
        gradient.setColorAt(0.3, QColor("#A855F7"))
        gradient.setColorAt(0.6, QColor("#EC4899"))
        gradient.setColorAt(1.0, QColor("#F97316"))
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
        glow_gradient.setColorAt(0.0, QColor(168, 85, 247, glow_opacity))
        glow_gradient.setColorAt(1.0, QColor(168, 85, 247, 0))
        painter.setBrush(QBrush(glow_gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(0, 0, 56, 56)
        bg_gradient = QLinearGradient(8, 8, 48, 48)
        bg_gradient.setColorAt(0.0, QColor("#6C5CE7"))
        bg_gradient.setColorAt(1.0, QColor("#A855F7"))
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
        painter.setBrush(QBrush(QColor("#1E1B2E")))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPath(bg_path)
        if self._indeterminate:
            center = (self._sweep / 360.0) * (self.width() + 120) - 60
            bar_width = 120
            x_start = max(0, center - bar_width / 2)
            x_end = min(self.width(), center + bar_width / 2)
            if x_end > x_start:
                gradient = QLinearGradient(x_start, 0, x_end, 0)
                gradient.setColorAt(0.0, QColor(108, 92, 231, 0))
                gradient.setColorAt(0.5, QColor(168, 85, 247, 255))
                gradient.setColorAt(1.0, QColor(236, 72, 153, 0))
                fill_path = QPainterPath()
                fill_path.addRoundedRect(x_start, 0, x_end - x_start, self.height(), 3, 3)
                painter.setBrush(QBrush(gradient))
                painter.drawPath(fill_path)
        else:
            fill_width = (self._animated_value / 100.0) * self.width()
            if fill_width > 0:
                gradient = QLinearGradient(0, 0, self.width(), 0)
                gradient.setColorAt(0.0, QColor("#6C5CE7"))
                gradient.setColorAt(0.5, QColor("#A855F7"))
                gradient.setColorAt(1.0, QColor("#EC4899"))
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
        self.setWindowTitle("Update Available")
        self.setFixedSize(520, 580)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        self.container = QWidget(self)
        self.container.setGeometry(0, 0, 520, 580)
        self.container.setStyleSheet("""
            QWidget {
                background-color: #13111C;
                border-radius: 16px;
                border: 1px solid #2A2540;
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

        title_text = "Required Update" if mandatory else "Update Available"
        title_label = QLabel(title_text)
        title_label.setStyleSheet("""
            QLabel {
                color: #F1F0F5;
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
                color: #7C7A85;
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
        divider.setStyleSheet("QFrame { background-color: #1E1B2E; border: none; }")
        content_layout.addWidget(divider)

        content_layout.addSpacing(20)

        section_header = QHBoxLayout()
        section_header.setSpacing(8)

        dot = QLabel("●")
        dot.setStyleSheet("""
            QLabel {
                color: #A855F7;
                font-size: 8px;
                background: transparent;
                border: none;
            }
        """)
        section_header.addWidget(dot, alignment=Qt.AlignmentFlag.AlignVCenter)

        changelog_title = QLabel("CHANGELOG")
        changelog_title.setStyleSheet("""
            QLabel {
                color: #9CA3AF;
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
                background-color: #0E0C15;
                color: #C9C8D0;
                border: 1px solid #1E1B2E;
                border-radius: 10px;
                padding: 16px 18px;
                font-size: 13px;
                font-family: 'Segoe UI', sans-serif;
                selection-background-color: #6C5CE7;
                selection-color: #FFFFFF;
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

        self.status_label = QLabel("Preparing update...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                color: #7C7A85;
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
            self.skip_btn = QPushButton("Skip")
            self.skip_btn.setFixedHeight(44)
            self.skip_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.skip_btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    color: #6B6878;
                    font-size: 13px;
                    font-weight: 600;
                    border: 1px solid #2A2540;
                    border-radius: 10px;
                    padding: 0 28px;
                }
                QPushButton:hover {
                    color: #9CA3AF;
                    border-color: #3D3756;
                    background: rgba(30, 27, 46, 0.5);
                }
                QPushButton:pressed {
                    background: #1E1B2E;
                    color: #C9C8D0;
                }
            """)
            self.skip_btn.clicked.connect(self.reject)
            btn_layout.addWidget(self.skip_btn)

        self.update_btn = QPushButton("Install Update")
        self.update_btn.setFixedHeight(44)
        self.update_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.update_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6C5CE7, stop:0.5 #A855F7, stop:1 #EC4899);
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
                    stop:0 #7C6CF7, stop:0.5 #B86AF7, stop:1 #F472B6);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #5B4BD7, stop:0.5 #9645E7, stop:1 #DB2777);
            }
        """)
        self.update_btn.clicked.connect(self._on_install)
        btn_layout.addWidget(self.update_btn)

        content_layout.addWidget(self.btn_container)
        main_layout.addLayout(content_layout)

    def _on_install(self):
        self.update_btn.setEnabled(False)
        self.update_btn.setText("Installing...")
        self.update_btn.setStyleSheet("""
            QPushButton {
                background: #1E1B2E;
                color: #4A4458;
                font-size: 14px;
                font-weight: 700;
                border: 1px solid #2A2540;
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
        self.status_label.setText("Launching updater...")

        self.setFixedSize(520, 320)
        self.container.setGeometry(0, 0, 520, 320)

        QTimer.singleShot(800, lambda: run_updater(self.download_url))

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


def check_updates(parent):
    try:
        if getattr(parent, "update_declined_this_session", False):
            return

        config = configparser.ConfigParser()
        config.read(INI_FILE)
        local_version = config.get("Launcher", "version")

        resp = requests.get(API_URL, timeout=5)
        data = resp.json()

        remote_version = data.get("version")
        mandatory = data.get("mandatory", False)
        notes = data.get("notes", {})

        if not remote_version or remote_version == local_version:
            return

        dialog = UpdateDialog(parent, remote_version, local_version, notes, mandatory, data["url"])
        result = dialog.exec()

        if result == QDialog.DialogCode.Rejected and not mandatory:
            parent.update_declined_this_session = True

    except Exception as e:
        print("Update check failed:", e)


def run_updater(download_url):
    import tempfile
    import textwrap

    launcher_pid = os.getpid()
    target_exe = sys.executable

    updater_code = textwrap.dedent("""
    import sys, os, shutil, requests, psutil, subprocess
    from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QProgressBar
    from PyQt6.QtCore import QTimer, Qt, QThread, pyqtSignal

    class DownloadThread(QThread):
        progress = pyqtSignal(int)
        finished = pyqtSignal()

        def __init__(self, url, target_exe):
            super().__init__()
            self.url = url
            self.target_exe = target_exe

        def run(self):
            resp = requests.get(self.url, stream=True)
            total = int(resp.headers.get("content-length", 0))
            tmp_file = self.target_exe + ".new"
            downloaded = 0

            with open(tmp_file, "wb") as f:
                for chunk in resp.iter_content(8192):
                    if not chunk:
                        continue
                    f.write(chunk)
                    downloaded += len(chunk)

                    if total > 0:
                        percent = int(downloaded * 100 / total)
                        self.progress.emit(percent)

            old_file = self.target_exe + ".old"

            try:
                if os.path.exists(old_file):
                    os.remove(old_file)
            except:
                pass

            os.rename(self.target_exe, old_file)
            os.rename(tmp_file, self.target_exe)

            try:
                os.remove(old_file)
            except:
                pass

            self.finished.emit()

    class UpdaterWindow(QWidget):
        def __init__(self, download_url, target_exe, target_pid):
            super().__init__()

            self.download_url = download_url
            self.target_exe = target_exe
            self.target_pid = target_pid

            self.setWindowTitle("Mission Helper Updater")
            self.setFixedSize(500, 160)

            layout = QVBoxLayout(self)

            self.status = QLabel("Preparing update...", self)
            self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.status.setStyleSheet("font-size: 12pt; color: #EAEAEA;")
            layout.addWidget(self.status)

            self.progress = QProgressBar(self)
            self.progress.setRange(0, 100)
            self.progress.setFixedHeight(30)
            self.progress.setStyleSheet(\"\"\"
                QProgressBar {
                    border: 2px solid #444;
                    border-radius: 10px;
                    text-align: center;
                    font-size: 10pt;
                }

                QProgressBar::chunk {
                    background-color: #0078d7;
                    width: 20px;
                }
            \"\"\")
            layout.addWidget(self.progress)

            QTimer.singleShot(100, self.run_update)

        def run_update(self):
            if self.is_pid_running(self.target_pid):
                self.status.setText("Waiting for Mission Helper to close...")
                QTimer.singleShot(3000, self.run_update)
            else:
                self.status.setText("Downloading update...")
                self.start_download()

        def is_pid_running(self, pid):
            try:
                proc = psutil.Process(pid)
                return proc.is_running()
            except:
                return False

        def start_download(self):
            self.thread = DownloadThread(self.download_url, self.target_exe)
            self.thread.progress.connect(self.progress.setValue)
            self.thread.finished.connect(self.restart_app)
            self.thread.start()

        def restart_app(self):
            self.status.setText("Restarting Mission Helper...")
            subprocess.Popen([self.target_exe])
            QApplication.quit()

    def main():
        if len(sys.argv) < 4:
            sys.exit(1)

        app = QApplication(sys.argv)

        win = UpdaterWindow(
            sys.argv[1],
            sys.argv[2],
            int(sys.argv[3])
        )

        win.show()

        sys.exit(app.exec())

    if __name__ == "__main__":
        main()
    """)

    temp_dir = tempfile.gettempdir()
    updater_script = os.path.join(temp_dir, "mission_runtime_updater.py")

    with open(updater_script, "w", encoding="utf-8") as f:
        f.write(updater_code)

    subprocess.Popen([
        sys.executable,
        updater_script,
        download_url,
        target_exe,
        str(launcher_pid)
    ])

    QApplication.quit()
    sys.exit(0)


def run_update_check(version, config_file, status_bar):
    try:
        response = requests.get(
            "https://api.natemarcellus.com/updates/missionhelper",
            params={"current_version": version},
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            latest_version = data.get("version")
            update_url = data.get("url")
            if latest_version and latest_version != version:
                send_messages(f"Update available: {latest_version}. Downloading...")
                status_bar.showMessage(f"Updating to version {latest_version}...")
                update_response = requests.get(update_url, stream=True)
                update_response.raise_for_status()
                with open("update.zip", "wb") as f:
                    for chunk in update_response.iter_content(chunk_size=8192):
                        f.write(chunk)
                send_messages("Update downloaded. Applying update...")
                status_bar.showMessage("Applying update...")
                temp_extract = os.path.join(os.getcwd(), "temp_update")
                if os.path.exists(temp_extract):
                    shutil.rmtree(temp_extract)
                os.makedirs(temp_extract, exist_ok=True)
                with zipfile.ZipFile("update.zip", "r") as z:
                    z.extractall(temp_extract)
                bot_folder = os.path.join(os.getcwd(), "bot")
                if os.path.exists(bot_folder):
                    shutil.rmtree(bot_folder)
                extracted_items = os.listdir(temp_extract)
                if extracted_items:
                    new_folder = os.path.join(temp_extract, extracted_items[0])
                    shutil.move(new_folder, bot_folder)
                shutil.rmtree(temp_extract)
                os.remove("update.zip")
                if os.path.exists(config_file):
                    with open(config_file, "r") as f:
                        old_settings = f.read()
                    with open(config_file, "w") as f:
                        f.write(old_settings)
                send_messages("Update applied successfully.")
                status_bar.showMessage("Update applied successfully.")
    except Exception as e:
        send_messages(f"Update check failed: {e}")
        status_bar.showMessage("Update check failed")