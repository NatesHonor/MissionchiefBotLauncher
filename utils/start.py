"""Coordinate the launcher startup sequence without blocking the UI."""

from __future__ import annotations

import configparser
import os
import shutil
import subprocess
import sys
import threading
from pathlib import Path
from typing import Callable

from handlers.console import send_error, send_info, send_success, send_system, send_warning
from handlers.logging import log_error, log_exception, log_info
from handlers.updates import run_update_check
from utils import state
from utils.install import run_install
from utils.integrity import run_integrity_check
from utils.paths import BOT_FOLDER, DATA_ROOT, LAUNCHER_CONFIG, resolve_venv_path
from utils.settings_store import get as get_setting, set_values
from utils.localization import tr


def update_start_button_state(button, running):
    if hasattr(button, 'set_running'):
        button.set_running(running)
        return

    if running:
        button.setText("Stop Bot")
        button.setStyleSheet("""
            QPushButton {
                background-color: #EF4444;
                color: #FFFFFF;
                border: none;
                border-radius: 12px;
                font-weight: 600;
                padding: 10px 16px;
            }
            QPushButton:hover { background-color: #F87171; }
            QPushButton:pressed { background-color: #DC2626; }
        """)
    else:
        button.setText("Start Bot")
        button.setStyleSheet("""
            QPushButton {
                background-color: #2583E8;
                color: #FFFFFF;
                border: none;
                border-radius: 12px;
                font-weight: 600;
                padding: 10px 16px;
            }
            QPushButton:hover { background-color: #4BA3FF; }
            QPushButton:pressed { background-color: #1D65D8; }
        """)


def _read_venv_name():
    return get_setting("venv")


def _save_venv_name(name):
    set_values({"venv": name.strip()})


def _prompt_venv_name():
    from PyQt6.QtWidgets import QApplication
    from logic.input_dialog import show_input_dialog

    app = QApplication.instance()
    if app is None:
        return None

    result = show_input_dialog(
        title=tr("virtual_environment"),
        prompt=tr("venv_prompt"),
        placeholder="missionchief_venv",
    )

    return result


def _read_bot_version():
    config_file = BOT_FOLDER / "config.ini"
    if not config_file.exists():
        return None, str(config_file)

    try:
        config = configparser.ConfigParser()
        config.read(config_file, encoding="utf-8")

        for section in config.sections():
            if config.has_option(section, "version"):
                return config.get(section, "version").strip(), str(config_file)

        with config_file.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("version="):
                    return line.split("=", 1)[1].strip(), str(config_file)
    except Exception as e:
        send_error(f"Failed to read bot/config.ini: {e}")
        log_error(f"Failed to read bot/config.ini: {e}")

    return None, config_file


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
        log_exception("Startup lifecycle callback failed")


def run_start_logic(status_bar=None, on_started: Callable | None = None, on_finished: Callable | None = None, on_failed: Callable | None = None):
    if state.is_running("bot_runtime"):
        message = "Bot is already running"
        send_warning(message)
        _status(status_bar, message)
        _call(on_failed, message)
        return None

    venv_name = _read_venv_name()

    if not venv_name:
        venv_name = _prompt_venv_name()

        if not venv_name:
            send_warning("No venv name entered — aborting")
            _status(status_bar, "No venv name entered")
            _call(on_failed, "No virtual environment entered")
            return None

        _save_venv_name(venv_name)
        send_success(f"Virtual environment set: {venv_name}")
        log_info(f"venv name saved: {venv_name}")

    version, config_file = _read_bot_version()

    if version:
        send_system(f"Bot version: {version}")
    else:
        send_warning("No bot version found — may need update")

    send_system("Starting launch sequence...")
    log_info(f"Starting launch sequence with venv: {venv_name}")
    state.clear_stop_request()

    try:
        thread = threading.Thread(
            target=_start_worker,
            args=(status_bar, venv_name, version, config_file, on_started, on_finished, on_failed),
            daemon=True,
            name="LauncherStartThread",
        )
        thread.start()
        return thread
    except Exception as exc:
        message = f"Could not start launcher worker: {exc}"
        send_error(message)
        log_exception("Could not start launcher worker")
        _status(status_bar, message)
        _call(on_failed, message)
        return None


def _python_command():
    if not getattr(sys, "frozen", False):
        return [sys.executable]
    for name in ("python", "python3"):
        executable = shutil.which(name)
        if executable:
            return [executable]
    launcher = shutil.which("py")
    if launcher:
        return [launcher, "-3"]
    return None


def _stream_process(label: str, command: list[str], cwd: Path, status_bar, failure_text: str) -> bool:
    process = None
    try:
        process = subprocess.Popen(
            command,
            cwd=str(cwd),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )
        state.add_process(label, process)
        if process.stdout is not None:
            for line in process.stdout:
                if line.strip():
                    send_info(line.strip())
                if state.is_stop_requested() and process.poll() is None:
                    process.terminate()
        returncode = process.wait()
        if returncode != 0:
            send_error(f"{failure_text} (exit code {returncode})")
            log_error(f"{label} failed with exit code {returncode}")
            _status(status_bar, failure_text)
            return False
        return True
    except Exception as exc:
        send_error(f"{failure_text}: {exc}")
        log_exception(f"Exception during {label}")
        _status(status_bar, failure_text)
        return False
    finally:
        state.remove_process(label)


def _start_worker(status_bar, venv_name, version, config_file, on_started, on_finished, on_failed):
    send_system("Checking launcher environment")
    _status(status_bar, "Checking launcher environment...")
    venv_path = resolve_venv_path(venv_name)

    created_new = False

    try:
        if state.is_stop_requested():
            _call(on_failed, "Startup cancelled")
            return

        if not venv_path.is_dir():
            python_command = _python_command()
            if not python_command:
                _call(on_failed, "A system Python installation is required to create the virtual environment")
                return
            send_info(f"Creating virtual environment: {venv_path}")
            _status(status_bar, "Creating virtual environment...")
            log_info(f"Creating venv: {venv_path}")
            venv_path.parent.mkdir(parents=True, exist_ok=True)
            if not _stream_process("venv_setup", python_command + ["-m", "venv", str(venv_path)], DATA_ROOT, status_bar, "Failed to create virtual environment"):
                _call(on_failed, "Failed to create virtual environment")
                return
            send_success(f"Virtual environment created: {venv_path.name}")
            _status(status_bar, "Virtual environment ready")
            log_info(f"venv created successfully: {venv_path}")
            created_new = True
        else:
            send_success(f"Virtual environment found: {venv_path.name}")
            _status(status_bar, "Virtual environment ready")
            log_info(f"Existing venv found: {venv_path}")

        if state.is_stop_requested():
            _call(on_failed, "Startup cancelled")
            return

        if version:
            _status(status_bar, "Checking for bot updates...")
            run_update_check(version, config_file, status_bar)

        if created_new:
            send_system("Running first-time installation...")
            _status(status_bar, "Installing dependencies...")
            run_install(venv_name, status_bar, on_started, on_finished, on_failed)
        else:
            send_system("Running integrity check...")
            _status(status_bar, "Verifying installation...")
            run_integrity_check(venv_name, status_bar, on_started, on_finished, on_failed)
    except Exception as exc:
        send_error(f"Startup failed: {exc}")
        log_exception("Launcher startup sequence failed")
        _status(status_bar, "Startup failed")
        _call(on_failed, str(exc))
