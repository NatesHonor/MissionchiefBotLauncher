import os
import sys
import tempfile
import traceback
from datetime import datetime
from pathlib import Path

from utils.paths import LOG_FOLDER

_log_file_path = None
_session_start = None
_log_count = 0

LOG_DIR = str(LOG_FOLDER)
LOG_PREFIX = "MissionchiefBot"
MAX_LOG_FILES_PER_DAY = 50
MAX_LOG_DAYS = 30


def generate_log_file():
    global _log_file_path, _session_start, _log_count

    _session_start = datetime.now()
    _log_count = 0

    today = _session_start.strftime("%Y-%m-%d")
    date_dir = _get_log_directory(today)

    counter = 1
    while counter <= MAX_LOG_FILES_PER_DAY:
        candidate = os.path.join(date_dir, f"{LOG_PREFIX}_{counter}.log")
        if not os.path.exists(candidate):
            break
        counter += 1

    _log_file_path = os.path.join(str(date_dir), f"{LOG_PREFIX}_{counter}.log")

    header = [
        f"{'=' * 60}",
        f"  Mission Helper — Session Log",
        f"  Started: {_session_start.strftime('%Y-%m-%d %H:%M:%S')}",
        f"  Platform: {sys.platform}",
        f"  Python: {sys.version.split()[0]}",
        f"  Executable: {sys.executable}",
        f"{'=' * 60}",
        "",
    ]

    try:
        with open(_log_file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(header) + "\n")
    except (IOError, OSError):
        fallback = Path(tempfile.gettempdir()) / "Mission Helper" / "logs" / today
        fallback.mkdir(parents=True, exist_ok=True)
        _log_file_path = str(fallback / f"{LOG_PREFIX}_{counter}.log")
        with open(_log_file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(header) + "\n")

    _cleanup_old_logs()

    return _log_file_path


def _get_log_directory(today):
    preferred = Path(LOG_DIR) / today
    try:
        preferred.mkdir(parents=True, exist_ok=True)
        return preferred
    except (IOError, OSError):
        fallback = Path(tempfile.gettempdir()) / "Mission Helper" / "logs" / today
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback


def log_to_latest_file(message, level=None):
    global _log_file_path, _log_count

    if _log_file_path is None:
        generate_log_file()

    _log_count += 1
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

    if level is None:
        level = _detect_level(message)

    level_tag = level.upper().ljust(7)
    formatted = f"[{timestamp}] [{level_tag}] {message}"

    try:
        with open(_log_file_path, "a", encoding="utf-8") as f:
            f.write(formatted + "\n")
    except (IOError, OSError):
        pass


def log_info(message):
    log_to_latest_file(message, "info")


def log_success(message):
    log_to_latest_file(message, "success")


def log_warning(message):
    log_to_latest_file(message, "warning")


def log_error(message):
    log_to_latest_file(message, "error")


def log_debug(message):
    log_to_latest_file(message, "debug")


def log_system(message):
    log_to_latest_file(message, "system")


def log_exception(message="An exception occurred"):
    tb = traceback.format_exc()
    log_to_latest_file(f"{message}\n{tb}", "error")


def get_log_path():
    return _log_file_path


def get_session_stats():
    if _session_start is None:
        return None

    elapsed = datetime.now() - _session_start
    hours, remainder = divmod(int(elapsed.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)

    return {
        "session_start": _session_start.strftime("%Y-%m-%d %H:%M:%S"),
        "elapsed": f"{hours:02d}:{minutes:02d}:{seconds:02d}",
        "log_entries": _log_count,
        "log_file": _log_file_path,
    }


def _detect_level(message):
    msg = message.lower()

    if any(k in msg for k in ["error", "failed", "exception", "traceback", "critical", "fatal"]):
        return "error"
    if any(k in msg for k in ["warning", "warn", "caution", "deprecated", "timeout"]):
        return "warning"
    if any(k in msg for k in ["success", "completed", "saved", "connected", "started", "applied", "done"]):
        return "success"
    if any(k in msg for k in ["update", "version", "checking", "initializing", "loading", "setup", "config"]):
        return "system"
    if any(k in msg for k in ["debug", "verbose", "trace"]):
        return "debug"

    return "info"


def _cleanup_old_logs():
    try:
        if not os.path.exists(LOG_DIR):
            return

        today = datetime.now()
        for entry in sorted(os.listdir(LOG_DIR)):
            entry_path = os.path.join(LOG_DIR, entry)
            if not os.path.isdir(entry_path):
                continue

            try:
                folder_date = datetime.strptime(entry, "%Y-%m-%d")
                age = (today - folder_date).days

                if age > MAX_LOG_DAYS:
                    import shutil
                    shutil.rmtree(entry_path, ignore_errors=True)
            except ValueError:
                continue
    except (IOError, OSError):
        pass
