import os
import shutil
import subprocess
import zipfile
import requests
from io import BytesIO
from handlers.console import (
    send_info, send_success, send_warning,
    send_error, send_system
)
from handlers.logging import log_info, log_error, log_exception
from utils import state
from utils.runbot import run_bot

DOWNLOAD_URL = "https://github.com/NatesHonor/MissionchiefBot-X/archive/refs/tags/latest.zip"
BOT_FOLDER = os.path.join(os.getcwd(), "bot")
CACHE_FOLDER = os.path.join(os.getcwd(), "cache", "bot")
TEMP_FOLDER = os.path.join(os.getcwd(), "temp_extract")


def _get_pip_path(venv_name):
    if os.name == "nt":
        return os.path.join(venv_name, "Scripts", "pip.exe")
    return os.path.join(venv_name, "bin", "pip")


def _get_python_path(venv_name):
    if os.name == "nt":
        return os.path.join(venv_name, "Scripts", "python.exe")
    return os.path.join(venv_name, "bin", "python")


def _download_release(status_bar):
    send_system("Downloading latest release...")
    status_bar.showMessage("Downloading latest release...")
    log_info(f"Downloading from: {DOWNLOAD_URL}")

    response = requests.get(DOWNLOAD_URL, stream=True, timeout=60)
    response.raise_for_status()

    total_size = int(response.headers.get('content-length', 0))
    downloaded = 0
    chunks = []

    for chunk in response.iter_content(chunk_size=65536):
        chunks.append(chunk)
        downloaded += len(chunk)

        if total_size > 0:
            percent = int((downloaded / total_size) * 100)
            mb_done = downloaded / (1024 * 1024)
            mb_total = total_size / (1024 * 1024)
            status_bar.showMessage(f"Downloading: {percent}% ({mb_done:.1f}/{mb_total:.1f} MB)")

    send_success(f"Download complete ({downloaded / (1024 * 1024):.1f} MB)")
    log_info(f"Download complete: {downloaded} bytes")

    return b"".join(chunks)


def _extract_release(data, status_bar):
    send_system("Extracting release archive...")
    status_bar.showMessage("Extracting files...")

    if os.path.exists(TEMP_FOLDER):
        shutil.rmtree(TEMP_FOLDER)
    os.makedirs(TEMP_FOLDER, exist_ok=True)

    with zipfile.ZipFile(BytesIO(data)) as z:
        root_folder = z.namelist()[0].split("/")[0]
        file_count = len(z.namelist())
        z.extractall(TEMP_FOLDER)

    source_dir = os.path.join(TEMP_FOLDER, root_folder)

    send_success(f"Extracted {file_count} files")
    log_info(f"Extracted {file_count} files from archive")

    return source_dir


def _deploy_files(source_dir, status_bar):
    send_system("Deploying files...")
    status_bar.showMessage("Deploying bot files...")

    if os.path.exists(BOT_FOLDER):
        shutil.rmtree(BOT_FOLDER)

    if os.path.exists(CACHE_FOLDER):
        shutil.rmtree(CACHE_FOLDER)

    send_info("Copying to bot folder...")
    shutil.copytree(source_dir, BOT_FOLDER)

    os.makedirs(os.path.dirname(CACHE_FOLDER), exist_ok=True)
    send_info("Copying to cache folder...")
    shutil.copytree(source_dir, CACHE_FOLDER)

    send_success("Files deployed to bot and cache folders")
    log_info("Files deployed to bot/ and cache/bot/")


def _cleanup_temp():
    if os.path.exists(TEMP_FOLDER):
        shutil.rmtree(TEMP_FOLDER, ignore_errors=True)
        log_info("Temporary extraction folder cleaned up")


def _install_requirements(venv_name, status_bar):
    requirements_file = os.path.join(BOT_FOLDER, "requirements.txt")

    if not os.path.exists(requirements_file):
        send_info("No requirements.txt found — skipping")
        return True

    pip_path = _get_pip_path(venv_name)
    if not os.path.exists(pip_path):
        send_error(f"pip not found: {pip_path}")
        log_error(f"pip not found at: {pip_path}")
        return False

    send_system("Installing Python dependencies...")
    status_bar.showMessage("Installing dependencies...")
    log_info("Installing requirements.txt")

    try:
        process = subprocess.Popen(
            [pip_path, "install", "-r", requirements_file, "--quiet", "--no-warn-script-location"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        state.add_process("pip_install", process)

        for line in process.stdout:
            stripped = line.strip()
            if stripped:
                send_info(stripped)

        process.wait()

        if process.returncode != 0:
            send_error(f"Dependency install failed (exit code {process.returncode})")
            log_error(f"pip install failed: exit code {process.returncode}")
            return False

        send_success("Python dependencies installed")
        log_info("Requirements installed successfully")
        return True

    except Exception as e:
        send_error(f"Dependency install failed: {e}")
        log_exception("Exception during pip install")
        return False


def _install_playwright(venv_name, status_bar):
    python_path = _get_python_path(venv_name)

    if not os.path.exists(python_path):
        send_error(f"Python not found: {python_path}")
        log_error(f"Python not found at: {python_path}")
        return False

    send_system("Installing Playwright browsers...")
    status_bar.showMessage("Installing Playwright browsers...")
    log_info("Installing Playwright browsers")

    try:
        process = subprocess.Popen(
            [python_path, "-m", "playwright", "install"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        state.add_process("playwright_install", process)

        for line in process.stdout:
            stripped = line.strip()
            if stripped:
                send_info(stripped)

        process.wait()

        if process.returncode != 0:
            send_error(f"Playwright install failed (exit code {process.returncode})")
            log_error(f"Playwright install failed: exit code {process.returncode}")
            return False

        send_success("Playwright browsers installed")
        log_info("Playwright browsers installed successfully")
        return True

    except Exception as e:
        send_error(f"Playwright install failed: {e}")
        log_exception("Exception during Playwright install")
        return False


def run_install(venv_name, status_bar):
    send_system(f"Starting installation for venv: {venv_name}")
    log_info(f"Install started: venv={venv_name}")

    if status_bar:
        status_bar.showMessage("Starting installation...")

    try:
        data = _download_release(status_bar)
        source_dir = _extract_release(data, status_bar)
        _deploy_files(source_dir, status_bar)
        _cleanup_temp()

        if not _install_requirements(venv_name, status_bar):
            status_bar.showMessage("Installation failed — dependency error")
            return

        if not _install_playwright(venv_name, status_bar):
            status_bar.showMessage("Installation failed — Playwright error")
            return

        send_success("Installation complete")
        log_info("Installation completed successfully")
        status_bar.showMessage("Installation complete")

        run_bot(venv_name, status_bar)

    except requests.RequestException as e:
        send_error(f"Download failed: {e}")
        log_exception("Download failed during install")
        status_bar.showMessage("Download failed")

    except zipfile.BadZipFile:
        send_error("Downloaded file is not a valid zip archive")
        log_error("Bad zip file received")
        status_bar.showMessage("Invalid download — bad archive")
        _cleanup_temp()

    except Exception as e:
        send_error(f"Installation failed: {e}")
        log_exception("Installation failed")
        status_bar.showMessage("Installation failed")
        _cleanup_temp()