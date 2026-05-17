from typing import Optional
from datetime import datetime
from PyQt6.QtCore import QMetaObject, Qt, Q_ARG, QObject, pyqtSignal


class ConsoleSignalBridge(QObject):
    message_signal = pyqtSignal(str, str)


_console_instance = None
_signal_bridge = ConsoleSignalBridge()


def set_console_instance(console):
    global _console_instance
    _console_instance = console
    _signal_bridge.message_signal.connect(_handle_message)


def _handle_message(message, level):
    if _console_instance is None:
        return

    if hasattr(_console_instance, 'append_message'):
        _console_instance.append_message(message, level)
    else:
        QMetaObject.invokeMethod(
            _console_instance,
            "append",
            Qt.ConnectionType.QueuedConnection,
            Q_ARG(str, message)
        )


def _detect_level(message):
    msg = message.lower()

    error_keywords = ["error", "failed", "exception", "traceback", "critical", "fatal"]
    if any(k in msg for k in error_keywords):
        return "error"

    warning_keywords = ["warning", "warn", "caution", "deprecated", "timeout"]
    if any(k in msg for k in warning_keywords):
        return "warning"

    success_keywords = ["success", "completed", "saved", "connected", "started", "applied", "done", "ready"]
    if any(k in msg for k in success_keywords):
        return "success"

    system_keywords = ["update", "version", "checking", "initializing", "loading", "setup", "config"]
    if any(k in msg for k in system_keywords):
        return "system"

    debug_keywords = ["debug", "verbose", "trace"]
    if any(k in msg for k in debug_keywords):
        return "debug"

    return "info"


def insert_message(message, level=None):
    if _console_instance is None:
        raise RuntimeError("Console instance not set.")

    if level is None:
        level = _detect_level(message)

    _signal_bridge.message_signal.emit(message, level)


def send_messages(message, level=None):
    insert_message(message, level)
    from handlers.logging import log_to_latest_file
    log_to_latest_file(message)


def send_info(message):
    send_messages(message, "info")


def send_success(message):
    send_messages(message, "success")


def send_warning(message):
    send_messages(message, "warning")


def send_error(message):
    send_messages(message, "error")


def send_system(message):
    send_messages(message, "system")


def send_debug(message):
    send_messages(message, "debug")