import html
import threading

from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QTextCursor
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QTextEdit, QVBoxLayout

from handlers.console import set_console_instance
from ui.icons import icon, icon_size
from ui.theme import THEMES, current_theme_name
from utils.localization import tr
from utils.settings_store import get as get_setting
from utils.start import run_start_logic
from utils.stop_bot import stop_bot


class ConsoleOutput(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ConsoleOutput")
        self.setReadOnly(True)
        self.setPlaceholderText(tr("console_placeholder"))

    @pyqtSlot(str, str)
    def append_message(self, message, level="info"):
        colors = {"info": "#B9D1E7", "success": "#35D399", "warning": "#F6C453", "error": "#F06B7A", "system": "#4BA3FF", "debug": "#7F9DB8"}
        prefixes = {"info": "›", "success": "✓", "warning": "!", "error": "×", "system": "•", "debug": "·"}
        color = colors.get(level, colors["info"])
        prefix = prefixes.get(level, "›")
        self.moveCursor(QTextCursor.MoveOperation.End)
        self.insertHtml(
            f'<div style="margin:2px 0;color:{color};"><b>{prefix}</b>&nbsp;{html.escape(str(message))}</div>'
        )
        self.ensureCursorVisible()


class StatusFooter(QFrame):
    _message_signal = pyqtSignal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("StatusFooter")
        self._message = tr("ready")
        self._level = "idle"
        self._label = QLabel(self._message)
        self._label.setObjectName("Muted")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        self._dot = QLabel("●")
        self._dot.setObjectName("StatusDot")
        layout.addWidget(self._dot)
        layout.addWidget(self._label)
        layout.addStretch()
        self._message_signal.connect(self._apply_message)
        self._apply_message(self._message, self._level)

    def set_message(self, text, level="info"):
        self._apply_message(str(text), level)

    def showMessage(self, text):
        self._message_signal.emit(str(text), "info")

    @pyqtSlot(str, str)
    def _apply_message(self, text, level="info"):
        self._message = text
        self._level = level
        self._label.setText(text)
        self._dot.setStyleSheet({
            "success": "color:#35D399;", "warning": "color:#F6C453;", "error": "color:#F06B7A;",
            "idle": "color:#4B6A84;", "info": "color:#4BA3FF;",
        }.get(level, "color:#4BA3FF;"))


class ConsolePanel(QFrame):
    _started_signal = pyqtSignal()
    _failed_signal = pyqtSignal(str)
    _finished_signal = pyqtSignal(int)
    _stopped_signal = pyqtSignal()
    _log_upload_finished = pyqtSignal(str, bool)

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self._operation_active = False
        self._stop_thread = None
        self.setObjectName("Card")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)

        header = QHBoxLayout()
        self.heading = QLabel(tr("console"))
        self.heading.setObjectName("CardTitle")
        header.addWidget(self.heading)
        header.addStretch()
        self.live_label = QLabel(tr("idle"))
        self.live_label.setObjectName("StatusBadge")
        header.addWidget(self.live_label)
        self.clear_btn = QPushButton()
        self.clear_btn.setObjectName("IconButton")
        self.clear_btn.setIconSize(icon_size(16))
        self._set_clear_icon()
        self.clear_btn.setToolTip(tr("clear_console"))
        self.clear_btn.clicked.connect(self._clear_console)
        header.addWidget(self.clear_btn)
        self.share_log_btn = QPushButton(tr("share_log"))
        self.share_log_btn.setObjectName("SecondaryButton")
        self.share_log_btn.clicked.connect(self._share_log)
        header.addWidget(self.share_log_btn)
        layout.addLayout(header)

        self.console = ConsoleOutput()
        layout.addWidget(self.console, 1)
        set_console_instance(self.console)

        footer = QHBoxLayout()
        self.control_btn = QPushButton(tr("start_bot"))
        self.control_btn.setObjectName("PrimaryButton")
        self.control_btn.setMinimumWidth(150)
        self.control_btn.clicked.connect(self.toggle_start_stop)
        footer.addWidget(self.control_btn)
        self.status_bar = StatusFooter()
        footer.addWidget(self.status_bar, 1)
        layout.addLayout(footer)

        self._started_signal.connect(self._on_bot_started)
        self._failed_signal.connect(self._on_start_failed)
        self._finished_signal.connect(self._on_bot_finished)
        self._stopped_signal.connect(self._on_bot_stopped)
        self._log_upload_finished.connect(self._on_log_upload_finished)

    def _set_button_style(self, running):
        self.control_btn.setObjectName("DangerButton" if running else "PrimaryButton")
        self.control_btn.style().unpolish(self.control_btn)
        self.control_btn.style().polish(self.control_btn)
        self.control_btn.setText(tr("stop_bot" if running else "start_bot"))

    def toggle_start_stop(self):
        if self._operation_active or self.parent.is_running:
            self._begin_stop()
            return
        self._operation_active = True
        self.control_btn.setText(tr("starting"))
        self.status_bar.set_message(tr("starting"), "info")
        try:
            self._start_thread = run_start_logic(
                self.status_bar,
                on_started=lambda: self._started_signal.emit(),
                on_finished=lambda code: self._finished_signal.emit(int(code)),
                on_failed=lambda message: self._failed_signal.emit(str(message)),
            )
            if self._start_thread is None and not self._operation_active:
                self._on_start_failed(tr("startup_failed"))
        except Exception as exc:
            self._on_start_failed(str(exc))

    def _begin_stop(self):
        if self._stop_thread and self._stop_thread.is_alive():
            return
        self._operation_active = True
        self.control_btn.setEnabled(False)
        self.status_bar.set_message(tr("stop_bot"), "warning")
        self._stop_thread = threading.Thread(
            target=stop_bot,
            kwargs={"on_complete": lambda: self._stopped_signal.emit()},
            name="BotStopThread",
            daemon=True,
        )
        self._stop_thread.start()

    @pyqtSlot()
    def _on_bot_started(self):
        self._operation_active = True
        self.parent.set_running(True)
        self.control_btn.setEnabled(True)
        self._set_button_style(True)
        self.live_label.setText(tr("running"))
        self.status_bar.set_message(tr("running"), "success")

    @pyqtSlot(str)
    def _on_start_failed(self, message):
        self._operation_active = False
        self.parent.set_running(False)
        self.control_btn.setEnabled(True)
        self._set_button_style(False)
        self.live_label.setText(tr("idle"))
        self.status_bar.set_message(message or tr("ready"), "error")

    @pyqtSlot(int)
    def _on_bot_finished(self, returncode):
        self._operation_active = False
        self.parent.set_running(False)
        self.control_btn.setEnabled(True)
        self._set_button_style(False)
        self.live_label.setText(tr("idle"))
        self.status_bar.set_message(tr("ready") if returncode == 0 else f"Exit code {returncode}", "idle" if returncode == 0 else "error")

    @pyqtSlot()
    def _on_bot_stopped(self):
        self._operation_active = False
        self.parent.set_running(False)
        self.control_btn.setEnabled(True)
        self._set_button_style(False)
        self.live_label.setText(tr("idle"))
        self.status_bar.set_message(tr("ready"), "idle")

    def refresh_text(self):
        self.heading.setText(tr("console"))
        self.console.setPlaceholderText(tr("console_placeholder"))
        self.clear_btn.setToolTip(tr("clear_console"))
        self.share_log_btn.setText(tr("share_log"))
        self._set_clear_icon()
        self.live_label.setText(tr("running" if self.parent.is_running else "idle"))
        self._set_button_style(self.parent.is_running)
        if not self._operation_active and not self.parent.is_running:
            self.status_bar.set_message(tr("ready"), "idle")

    def _clear_console(self):
        self.console.clear()
        self.console.append_message(tr("console_cleared"), "system")

    def _share_log(self):
        if getattr(self, "_log_upload_thread", None) and self._log_upload_thread.is_alive():
            return
        self.share_log_btn.setEnabled(False)
        self.status_bar.set_message(tr("uploading_log"), "info")
        self._log_upload_thread = threading.Thread(
            target=self._upload_log_worker,
            name="LauncherLogUploadThread",
            daemon=True,
        )
        self._log_upload_thread.start()

    def _upload_log_worker(self):
        try:
            from utils.log_upload import upload_latest_log

            self._log_upload_finished.emit(upload_latest_log(), True)
        except Exception as exc:
            self._log_upload_finished.emit(str(exc), False)

    @pyqtSlot(str, bool)
    def _on_log_upload_finished(self, result, success):
        self.share_log_btn.setEnabled(True)
        if not success:
            self.status_bar.set_message(result, "error")
            return
        from PyQt6.QtWidgets import QApplication

        QApplication.clipboard().setText(result)
        self.status_bar.set_message(f"{tr('log_url_copied')}: {result}", "success")

    def _set_clear_icon(self):
        theme = THEMES[current_theme_name(get_setting("theme", "ocean"))]
        self.clear_btn.setIcon(icon("trash", theme.muted, 20))
