"""Bot-process validation and lifecycle management."""

from __future__ import annotations

import os
import subprocess
import threading
import time
from pathlib import Path
from typing import Callable

from handlers.console import send_error, send_info, send_success, send_system
from handlers.logging import log_error, log_exception, log_info
from utils import state
from utils.paths import BOT_FOLDER, resolve_venv_path


def _get_python_path(venv_name: str | None) -> Path | None:
    if not venv_name:
        return None
    venv_path = resolve_venv_path(venv_name)
    executable = "python.exe" if os.name == "nt" else "python"
    return venv_path / ("Scripts" if os.name == "nt" else "bin") / executable


def _find_entrypoint() -> Path | None:
    if not BOT_FOLDER.is_dir():
        return None
    candidates = {"main.py", "run.py", "launcher.py"}
    for path in BOT_FOLDER.iterdir():
        if path.is_file() and path.name.lower() in candidates:
            return path
    return None


def _validate_environment(venv_name: str | None):
    if not BOT_FOLDER.is_dir():
        message = "Bot folder not found — run install first"
        send_error(message)
        log_error("Bot folder missing")
        return None, None, message

    entrypoint = _find_entrypoint()
    if entrypoint is None:
        message = "No bot entrypoint found in the bot folder"
        send_error(message)
        log_error(f"No supported bot entrypoint found in {BOT_FOLDER}")
        return None, None, message

    python_path = _get_python_path(venv_name)
    if python_path is None or not python_path.is_file():
        message = "Python executable not found in virtual environment"
        send_error(message)
        log_error(f"Python not found: {python_path}")
        return None, None, message

    return python_path, entrypoint, None


def _call(callback: Callable | None, *args):
    if callback is None:
        return
    try:
        callback(*args)
    except Exception:
        log_exception("Bot lifecycle callback failed")


def _status(status_bar, message: str):
    if status_bar is not None:
        try:
            status_bar.showMessage(message)
        except Exception:
            log_exception("Could not update launcher status bar")


def run_bot(
    venv_name: str | None = None,
    status_bar=None,
    on_started: Callable | None = None,
    on_finished: Callable | None = None,
    on_failed: Callable | None = None,
):
    """Start the bot in a worker thread and report its complete lifecycle."""
    python_path, entrypoint, validation_error = _validate_environment(venv_name)
    if validation_error:
        _status(status_bar, validation_error)
        _call(on_failed, validation_error)
        return None

    send_system("Launching bot runtime...")
    log_info(f"Starting bot: {python_path} {entrypoint}")
    _status(status_bar, "Bot is starting...")

    def worker():
        start_time = time.monotonic()
        process = None
        try:
            if state.is_stop_requested():
                _call(on_failed, "Bot start cancelled")
                return

            environment = os.environ.copy()
            environment.setdefault("PYTHONUNBUFFERED", "1")
            creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
            process = subprocess.Popen(
                [str(python_path), str(entrypoint)],
                cwd=str(BOT_FOLDER),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                env=environment,
                creationflags=creationflags,
            )
            state.add_process("bot_runtime", process)
            send_success(f"Bot process started (PID: {process.pid})")
            log_info(f"Bot process started (PID: {process.pid})")
            _status(status_bar, "Bot is running")
            _call(on_started)

            if process.stdout is not None:
                for line in process.stdout:
                    stripped = line.strip()
                    if stripped:
                        send_info(stripped)

            returncode = process.wait()
            elapsed = int(time.monotonic() - start_time)
            hours, remainder = divmod(elapsed, 3600)
            minutes, seconds = divmod(remainder, 60)
            runtime = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            if returncode == 0:
                send_success(f"Bot finished successfully (runtime: {runtime})")
                log_info(f"Bot exited cleanly after {runtime}")
                _status(status_bar, f"Bot finished — runtime: {runtime}")
            else:
                send_error(f"Bot exited with code {returncode} (runtime: {runtime})")
                log_error(f"Bot exited with code {returncode} after {runtime}")
                _status(status_bar, f"Bot stopped — exit code {returncode}")
            _call(on_finished, returncode)
        except Exception as exc:
            send_error(f"Bot runtime failed: {exc}")
            log_exception("Exception in bot runtime worker")
            _status(status_bar, "Bot runtime failed")
            _call(on_failed, str(exc))
        finally:
            state.remove_process("bot_runtime")

    thread = threading.Thread(target=worker, daemon=True, name="BotRuntimeThread")
    thread.start()
    log_info("Bot worker thread started")
    return thread
