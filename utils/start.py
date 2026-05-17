import os
import configparser
import threading
import subprocess
from handlers.console import send_messages, send_info, send_success, send_warning, send_error, send_system
from handlers.logging import log_info, log_error, log_exception
from utils.install import run_install
from utils.integrity import run_integrity_check
from utils import state
from handlers.updates import run_update_check

INI_FILE = "launcher_settings.ini"


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
                background-color: #6C5CE7;
                color: #FFFFFF;
                border: none;
                border-radius: 12px;
                font-weight: 600;
                padding: 10px 16px;
            }
            QPushButton:hover { background-color: #7C6CF7; }
            QPushButton:pressed { background-color: #5B4BD7; }
        """)


def _read_venv_name():
    config = configparser.ConfigParser()
    config.read(INI_FILE)
    return config.get("Launcher", "venv", fallback="").strip()


def _save_venv_name(name):
    config = configparser.ConfigParser()
    config.read(INI_FILE)

    if not config.has_section("Launcher"):
        config.add_section("Launcher")

    config.set("Launcher", "venv", name)

    with open(INI_FILE, "w") as f:
        config.write(f)


def _prompt_venv_name():
    from PyQt6.QtWidgets import QApplication
    from logic.input_dialog import show_input_dialog

    app = QApplication.instance()
    if app is None:
        return None

    result = show_input_dialog(
        title="Virtual Environment",
        prompt="Enter a name for the Python virtual environment:",
        placeholder="missionchief_venv",
    )

    return result


def _read_bot_version():
    config_file = os.path.join("bot", "config.ini")
    if not os.path.exists(config_file):
        return None, config_file

    try:
        config = configparser.ConfigParser()
        config.read(config_file)

        for section in config.sections():
            if config.has_option(section, "version"):
                return config.get(section, "version").strip(), config_file

        with open(config_file, "r") as f:
            for line in f:
                line = line.strip()
                if line.startswith("version="):
                    return line.split("=", 1)[1].strip(), config_file
    except Exception as e:
        send_error(f"Failed to read bot/config.ini: {e}")
        log_error(f"Failed to read bot/config.ini: {e}")

    return None, config_file


def run_start_logic(status_bar):
    venv_name = _read_venv_name()

    if not venv_name:
        venv_name = _prompt_venv_name()

        if not venv_name:
            send_warning("No venv name entered — aborting")
            status_bar.showMessage("No venv name entered")
            return

        _save_venv_name(venv_name)
        send_success(f"Virtual environment set: {venv_name}")
        log_info(f"venv name saved: {venv_name}")

    version, config_file = _read_bot_version()

    if version:
        send_system(f"Bot version: {version}")
    else:
        send_warning("No bot version found — may need update")

    status_bar.showMessage("Checking for bot updates...")
    run_update_check(version, config_file, status_bar)

    send_system("Starting launch sequence...")
    log_info(f"Starting launch sequence with venv: {venv_name}")

    thread = threading.Thread(
        target=_start_worker,
        args=(status_bar, venv_name),
        daemon=True
    )
    thread.start()


def _start_worker(status_bar, venv_name):
    send_system("Checking launcher environment")
    status_bar.showMessage("Checking launcher environment...")

    created_new = False

    if not os.path.isdir(venv_name):
        send_info(f"Creating virtual environment: {venv_name}")
        status_bar.showMessage(f"Creating venv: {venv_name}...")
        log_info(f"Creating venv: {venv_name}")

        try:
            process = subprocess.Popen(
                ["python", "-m", "venv", venv_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            state.add_process("venv_setup", process)

            for line in process.stdout:
                stripped = line.strip()
                if stripped:
                    send_info(stripped)

            process.wait()

            if process.returncode == 0:
                send_success(f"Virtual environment created: {venv_name}")
                status_bar.showMessage("Virtual environment ready")
                log_info(f"venv created successfully: {venv_name}")
                created_new = True
            else:
                send_error(f"venv creation failed (exit code {process.returncode})")
                status_bar.showMessage("Failed to create virtual environment")
                log_error(f"venv creation failed with code {process.returncode}")
                return

        except Exception as e:
            send_error(f"Failed to create virtual environment: {e}")
            status_bar.showMessage("Failed to create virtual environment")
            log_exception(f"Exception during venv creation: {e}")
            return
    else:
        send_success(f"Virtual environment found: {venv_name}")
        status_bar.showMessage("Virtual environment ready")
        log_info(f"Existing venv found: {venv_name}")

    if created_new:
        send_system("Running first-time installation...")
        status_bar.showMessage("Installing dependencies...")
        run_install(venv_name, status_bar)
    else:
        send_system("Running integrity check...")
        status_bar.showMessage("Verifying installation...")
        run_integrity_check(venv_name, status_bar)