"""Verify the cached bot release and restore local changes safely."""

from __future__ import annotations

import hashlib
import shutil
from pathlib import Path
from typing import Callable

from handlers.console import send_error, send_info, send_success, send_system, send_warning
from handlers.logging import log_error, log_exception, log_info, log_warning
from utils import state
from utils.install import install_requirements, run_install
from utils.paths import BOT_FOLDER, CACHE_FOLDER
from utils.runbot import run_bot


def _status(status_bar, message: str):
    if status_bar is not None:
        try:
            status_bar.showMessage(message)
        except Exception:
            log_exception("Could not update launcher status bar")


def _call(callback: Callable | None, *args):
    if callback is None:
        return
    try:
        callback(*args)
    except Exception:
        log_exception("Integrity lifecycle callback failed")


def _file_hash(filepath: Path, algorithm="sha256"):
    digest = hashlib.new(algorithm)
    try:
        with filepath.open("rb") as handle:
            for chunk in iter(lambda: handle.read(65536), b""):
                digest.update(chunk)
        return digest.hexdigest()
    except OSError:
        return None


def _collect_cache_files():
    if not CACHE_FOLDER.is_dir():
        return []
    files = []
    for cache_path in CACHE_FOLDER.rglob("*"):
        if cache_path.is_file():
            relative = cache_path.relative_to(CACHE_FOLDER)
            files.append((cache_path, BOT_FOLDER / relative, str(relative)))
    return files


def _verify_files(cache_files, status_bar):
    total = len(cache_files)
    missing, corrupted, verified = [], [], 0
    last_percent = -1
    for index, (cache_path, target_path, relative) in enumerate(cache_files, start=1):
        if state.is_stop_requested():
            break
        if not target_path.is_file():
            missing.append((cache_path, target_path, relative))
        elif _file_hash(cache_path) != _file_hash(target_path):
            corrupted.append((cache_path, target_path, relative))
        else:
            verified += 1
        percent = int(index * 100 / total) if total else 100
        if percent >= last_percent + 10:
            last_percent = percent
            send_info(f"Scanning: {percent}% ({index}/{total} files)")
            _status(status_bar, f"Integrity scan: {percent}%")
    return missing, corrupted, verified


def _restore_files(files, label, status_bar):
    if not files:
        return 0
    send_warning(f"Restoring {len(files)} {label} file{'s' if len(files) != 1 else ''}...")
    _status(status_bar, f"Restoring {len(files)} {label} file{'s' if len(files) != 1 else ''}...")
    restored = 0
    for cache_path, target_path, relative in files:
        try:
            if state.is_stop_requested():
                break
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(cache_path, target_path)
            send_info(f"Restored: {relative}")
            restored += 1
        except Exception as exc:
            send_error(f"Failed to restore {relative}: {exc}")
            log_error(f"Failed to restore {relative}: {exc}")
    return restored


def run_integrity_check(venv_name=None, status_bar=None, on_started: Callable | None = None, on_finished: Callable | None = None, on_failed: Callable | None = None):
    send_system("Starting integrity check...")
    log_info("Integrity check started")
    _status(status_bar, "Running integrity check...")

    if not CACHE_FOLDER.is_dir():
        send_warning("Cache folder not found — running fresh install")
        log_warning("Cache folder missing, triggering install")
        if venv_name:
            return run_install(venv_name, status_bar, on_started, on_finished, on_failed)
        message = "Bot cache is missing — run install first"
        _call(on_failed, message)
        return None

    if not BOT_FOLDER.is_dir():
        send_warning("Bot folder missing — restoring from cache")
        try:
            shutil.copytree(CACHE_FOLDER, BOT_FOLDER)
            send_success("Bot folder restored from cache")
        except Exception as exc:
            send_error(f"Failed to restore bot folder: {exc}")
            log_exception("Failed to copy cache to bot folder")
            if venv_name:
                return run_install(venv_name, status_bar, on_started, on_finished, on_failed)
            _call(on_failed, "Failed to restore bot folder")
            return None

    cache_files = _collect_cache_files()
    if not cache_files:
        send_warning("Cache is empty — running fresh install")
        if venv_name:
            return run_install(venv_name, status_bar, on_started, on_finished, on_failed)
        _call(on_failed, "Bot cache is empty")
        return None

    send_info(f"Scanning {len(cache_files)} files...")
    missing, corrupted, verified = _verify_files(cache_files, status_bar)
    restored = _restore_files(missing, "missing", status_bar) + _restore_files(corrupted, "corrupted", status_bar)
    issues = len(missing) + len(corrupted)
    if issues:
        send_success(f"Integrity restored — {restored}/{issues} issues fixed")
        _status(status_bar, f"Restored {restored} file{'s' if restored != 1 else ''}")
    else:
        send_success(f"Integrity verified — {verified}/{len(cache_files)} files OK")
        _status(status_bar, f"Integrity OK — {verified} files verified")
    log_info(f"Integrity check complete: {verified} verified, {restored} restored")

    if not venv_name:
        _call(on_finished, 0)
        return None
    if not install_requirements(venv_name, status_bar):
        _call(on_failed, "Dependency installation failed")
        return None
    send_system("Launching bot...")
    _status(status_bar, "Launching bot...")
    return run_bot(venv_name, status_bar, on_started, on_finished, on_failed)
