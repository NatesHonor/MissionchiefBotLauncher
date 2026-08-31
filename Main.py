import sys
import time
import urllib.request
from pathlib import Path

from PyQt6.QtCore import QLockFile
from PyQt6.QtWidgets import QApplication, QMessageBox

from handlers.logging import generate_log_file, log_exception
from ui.theme import current_theme_name, stylesheet
from utils.localization import tr
from utils.paths import LAUNCHER_CONFIG, LOCK_FILE, ensure_runtime_directories
from utils.settings_store import get as get_setting
from utils.settings_store import ensure_launcher_settings
from windows.main import MissionChiefBotApp


def _process_exists(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        import ctypes
        handle = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)
        if not handle:
            return False
        ctypes.windll.kernel32.CloseHandle(handle)
        return True
    except (AttributeError, OSError):
        return False


def apply_update_mode(arguments: list[str]) -> int:
    """Apply a packaged launcher update from a second process."""

    if len(arguments) < 4:
        return 2

    download_url, target_name, pid_text = arguments[1:4]
    try:
        target = Path(target_name).resolve()
        launcher_pid = int(pid_text)
    except (TypeError, ValueError):
        return 2

    if not getattr(sys, "frozen", False) or target != Path(sys.executable).resolve():
        return 3

    for _ in range(120):
        if not _process_exists(launcher_pid):
            break
        time.sleep(0.25)
    else:
        return 4

    temporary = target.with_suffix(target.suffix + ".new")
    backup = target.with_suffix(target.suffix + ".old")
    try:
        request = urllib.request.Request(download_url, headers={"User-Agent": "MissionHelper-Launcher"})
        with urllib.request.urlopen(request, timeout=60) as response, temporary.open("wb") as handle:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                handle.write(chunk)
            handle.flush()

        if temporary.stat().st_size < 1024:
            return 5

        if backup.exists():
            backup.unlink()
        target.replace(backup)
        temporary.replace(target)
        backup.unlink(missing_ok=True)
    except Exception:
        temporary.unlink(missing_ok=True)
        if not target.exists() and backup.exists():
            backup.replace(target)
        return 6

    try:
        import subprocess
        subprocess.Popen([str(target)], cwd=str(target.parent), close_fds=True)
    except OSError:
        return 7
    return 0


def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] == "--apply-update":
        return apply_update_mode(sys.argv[1:])

    try:
        ensure_runtime_directories()
        ensure_launcher_settings()
    except Exception:
        log_exception("Launcher initialization failed")
        return 1

    app = QApplication(sys.argv)
    app.setApplicationName(tr("app_name"))
    app.setOrganizationName("NatesHonor")
    app.setStyleSheet(stylesheet(current_theme_name(get_setting("theme", "ocean"))))

    lock = QLockFile(str(LOCK_FILE))
    lock.setStaleLockTime(10_000)
    if not lock.tryLock(100):
        QMessageBox.information(None, tr("app_name"), tr("already_running"))
        return 0

    app.aboutToQuit.connect(lock.unlock)
    try:
        generate_log_file()
        window = MissionChiefBotApp()
        window.show()
        return app.exec()
    except Exception:
        log_exception("Unhandled launcher error")
        QMessageBox.critical(None, tr("app_name"), tr("startup_failed"))
        return 1


if __name__ == "__main__":
    sys.exit(main())
