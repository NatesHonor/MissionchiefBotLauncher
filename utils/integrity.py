import os
import hashlib
import shutil
import subprocess
from handlers.console import (
    send_messages, send_info, send_success,
    send_warning, send_error, send_system
)
from handlers.logging import log_info, log_warning, log_error, log_exception
from utils.install import run_install
from utils.runbot import run_bot
from utils import state

BOT_FOLDER = os.path.join(os.getcwd(), "bot")
CACHE_FOLDER = os.path.join(os.getcwd(), "cache", "bot")


def _get_pip_path(venv_name):
    if os.name == "nt":
        return os.path.join(venv_name, "Scripts", "pip.exe")
    return os.path.join(venv_name, "bin", "pip")


def _file_hash(filepath, algorithm="sha256"):
    h = hashlib.new(algorithm)
    try:
        with open(filepath, "rb") as f:
            while True:
                chunk = f.read(65536)
                if not chunk:
                    break
                h.update(chunk)
        return h.hexdigest()
    except (IOError, OSError):
        return None


def _collect_cache_files():
    cache_files = []
    if not os.path.exists(CACHE_FOLDER):
        return cache_files

    for root, _, files in os.walk(CACHE_FOLDER):
        for file in files:
            cache_path = os.path.join(root, file)
            rel_path = os.path.relpath(cache_path, CACHE_FOLDER)
            target_path = os.path.join(BOT_FOLDER, rel_path)
            cache_files.append((cache_path, target_path, rel_path))

    return cache_files


def _verify_files(cache_files, status_bar):
    total = len(cache_files)
    if total == 0:
        return [], [], 0

    missing = []
    corrupted = []
    verified = 0
    last_percent = -1

    for i, (cache_path, target_path, rel_path) in enumerate(cache_files, start=1):
        if not os.path.exists(target_path):
            missing.append((cache_path, target_path, rel_path))
        else:
            cache_hash = _file_hash(cache_path)
            target_hash = _file_hash(target_path)

            if cache_hash and target_hash and cache_hash != target_hash:
                corrupted.append((cache_path, target_path, rel_path))
            else:
                verified += 1

        percent = int((i / total) * 100)
        if percent >= last_percent + 10:
            last_percent = percent
            send_info(f"Scanning: {percent}% ({i}/{total} files)")
            status_bar.showMessage(f"Integrity scan: {percent}%")

    return missing, corrupted, verified


def _restore_files(files, label, status_bar):
    count = len(files)
    if count == 0:
        return 0

    send_warning(f"Restoring {count} {label} file{'s' if count != 1 else ''}...")
    status_bar.showMessage(f"Restoring {count} {label} file{'s' if count != 1 else ''}...")
    log_warning(f"Restoring {count} {label} files")

    restored = 0
    for cache_path, target_path, rel_path in files:
        try:
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            shutil.copy2(cache_path, target_path)
            send_info(f"Restored: {rel_path}")
            restored += 1
        except Exception as e:
            send_error(f"Failed to restore {rel_path}: {e}")
            log_error(f"Failed to restore {rel_path}: {e}")

    return restored


def _install_requirements(venv_name, status_bar):
    requirements_file = os.path.join(BOT_FOLDER, "requirements.txt")

    if not os.path.exists(requirements_file):
        send_info("No requirements.txt found — skipping dependency install")
        return True

    pip_path = _get_pip_path(venv_name)
    if not os.path.exists(pip_path):
        send_error(f"pip not found at: {pip_path}")
        log_error(f"pip not found: {pip_path}")
        return False

    send_system("Installing dependencies...")
    status_bar.showMessage("Installing dependencies...")
    log_info("Installing requirements from requirements.txt")

    try:
        process = subprocess.Popen(
            [pip_path, "install", "-r", requirements_file, "--quiet"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        state.add_process("pip_integrity", process)

        for line in process.stdout:
            stripped = line.strip()
            if stripped:
                send_info(stripped)

        process.wait()

        if process.returncode == 0:
            send_success("Dependencies installed successfully")
            status_bar.showMessage("Dependencies ready")
            log_info("Requirements installed successfully")
            return True
        else:
            send_error(f"Dependency install failed (exit code {process.returncode})")
            status_bar.showMessage("Dependency install failed")
            log_error(f"pip install failed with code {process.returncode}")
            return False

    except Exception as e:
        send_error(f"Failed to install dependencies: {e}")
        log_exception("Exception during pip install")
        return False


def run_integrity_check(venv_name=None, status_bar=None):
    send_system("Starting integrity check...")
    log_info("Integrity check started")

    if status_bar:
        status_bar.showMessage("Running integrity check...")

    if not os.path.exists(CACHE_FOLDER):
        send_warning("Cache folder not found — running fresh install")
        log_warning("Cache folder missing, triggering install")
        if venv_name and status_bar:
            run_install(venv_name, status_bar)
        return

    if not os.path.exists(BOT_FOLDER):
        send_warning("Bot folder missing — restoring from cache")
        log_warning("Bot folder missing, copying from cache")
        if status_bar:
            status_bar.showMessage("Restoring bot folder from cache...")
        try:
            shutil.copytree(CACHE_FOLDER, BOT_FOLDER)
            send_success("Bot folder restored from cache")
            log_info("Bot folder restored from cache")
        except Exception as e:
            send_error(f"Failed to restore bot folder: {e}")
            log_exception("Failed to copy cache to bot folder")
            if venv_name and status_bar:
                run_install(venv_name, status_bar)
            return

    cache_files = _collect_cache_files()
    total = len(cache_files)

    if total == 0:
        send_warning("Cache is empty — nothing to verify")
        if status_bar:
            status_bar.showMessage("Cache empty")
        return

    send_info(f"Scanning {total} file{'s' if total != 1 else ''}...")

    missing, corrupted, verified = _verify_files(cache_files, status_bar or _DummyStatusBar())

    restored_missing = _restore_files(missing, "missing", status_bar or _DummyStatusBar())
    restored_corrupted = _restore_files(corrupted, "corrupted", status_bar or _DummyStatusBar())

    total_issues = len(missing) + len(corrupted)
    total_restored = restored_missing + restored_corrupted

    if total_issues == 0:
        send_success(f"Integrity verified — {verified}/{total} files OK")
        log_info(f"Integrity check passed: {verified}/{total} files verified")
        if status_bar:
            status_bar.showMessage(f"Integrity OK — {verified} files verified")
    else:
        send_success(f"Integrity restored — {total_restored}/{total_issues} issues fixed")
        log_info(f"Integrity restored: {total_restored}/{total_issues} fixed, {verified} already OK")
        if status_bar:
            status_bar.showMessage(f"Restored {total_restored} file{'s' if total_restored != 1 else ''}")

    if venv_name:
        if not _install_requirements(venv_name, status_bar or _DummyStatusBar()):
            return

        send_system("Launching bot...")
        if status_bar:
            status_bar.showMessage("Launching bot...")
        run_bot(venv_name, status_bar)


class _DummyStatusBar:
    def showMessage(self, *args, **kwargs):
        pass