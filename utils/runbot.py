import os
import subprocess
import threading
import time
from handlers.console import (
    send_info, send_success, send_warning,
    send_error, send_system
)
from handlers.logging import log_info, log_error, log_exception
from utils import state

BOT_FOLDER = os.path.join(os.getcwd(), "bot")


def _get_python_path(venv_name):
    if os.name == "nt":
        return os.path.join(venv_name, "Scripts", "python.exe")
    return os.path.join(venv_name, "bin", "python")


def _validate_environment(venv_name):
    if not os.path.exists(BOT_FOLDER):
        send_error("Bot folder not found — run install first")
        log_error("Bot folder missing")
        return None, "Bot folder not found"

    main_py = os.path.join(BOT_FOLDER, "main.py")
    if not os.path.exists(main_py):
        send_error("main.py not found in bot folder")
        log_error("main.py missing from bot/")
        return None, "main.py not found"

    python_path = _get_python_path(venv_name)
    if not os.path.exists(python_path):
        send_error("Python executable not found in virtual environment")
        log_error(f"Python not found: {python_path}")
        return None, "Python not found in venv"

    return python_path, main_py


def run_bot(venv_name=None, status_bar=None):
    if not venv_name:
        send_error("No virtual environment specified")
        return

    result = _validate_environment(venv_name)
    python_path, main_py = result

    if python_path is None:
        if status_bar:
            status_bar.showMessage(main_py)
        return

    send_system("Launching bot runtime...")
    log_info(f"Starting bot: {python_path} {main_py}")

    if status_bar:
        status_bar.showMessage("Bot is starting...")

    def worker():
        start_time = time.time()

        try:
            process = subprocess.Popen(
                [python_path, main_py],
                cwd=BOT_FOLDER,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            state.add_process("bot_runtime", process)

            send_success("Bot process started")
            log_info(f"Bot process started (PID: {process.pid})")

            if status_bar:
                status_bar.showMessage("Bot is running")

            while True:
                line = process.stdout.readline()

                if not line and process.poll() is not None:
                    break

                if line:
                    stripped = line.strip()
                    if stripped:
                        send_info(stripped)

            process.wait()
            elapsed = time.time() - start_time
            hours, remainder = divmod(int(elapsed), 3600)
            minutes, seconds = divmod(remainder, 60)
            runtime = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

            if process.returncode == 0:
                send_success(f"Bot finished successfully (runtime: {runtime})")
                log_info(f"Bot exited cleanly after {runtime}")
                if status_bar:
                    status_bar.showMessage(f"Bot finished — runtime: {runtime}")
            else:
                send_error(f"Bot exited with code {process.returncode} (runtime: {runtime})")
                log_error(f"Bot exited with code {process.returncode} after {runtime}")
                if status_bar:
                    status_bar.showMessage(f"Bot crashed — exit code {process.returncode}")

            state.remove_process("bot_runtime")

        except Exception as e:
            send_error(f"Bot runtime failed: {e}")
            log_exception("Exception in bot runtime worker")
            if status_bar:
                status_bar.showMessage("Bot runtime failed")
            state.remove_process("bot_runtime")

    thread = threading.Thread(target=worker, daemon=True)
    thread.name = "BotRuntimeThread"
    thread.start()

    log_info("Bot worker thread started")