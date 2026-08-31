"""Download, validate, and deploy bot releases transactionally."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
import zipfile
from io import BytesIO
from pathlib import Path
from typing import Callable

import requests

from handlers.console import send_error, send_info, send_success, send_system, send_warning
from handlers.logging import log_error, log_exception, log_info, log_warning
from utils import state
from utils.paths import BOT_FOLDER, CACHE_FOLDER, DATA_ROOT, TEMP_FOLDER, resolve_venv_path
from utils.runbot import run_bot


DOWNLOAD_URL = "https://github.com/NatesHonor/MissionchiefBot-X/archive/refs/tags/latest.zip"
_STAGING_ROOT = DATA_ROOT / ".bot-deployment"


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
        log_exception("Install lifecycle callback failed")


def _get_pip_path(venv_name: str) -> Path:
    venv_path = resolve_venv_path(venv_name)
    return venv_path / ("Scripts" if os.name == "nt" else "bin") / ("pip.exe" if os.name == "nt" else "pip")


def _get_python_path(venv_name: str) -> Path:
    venv_path = resolve_venv_path(venv_name)
    return venv_path / ("Scripts" if os.name == "nt" else "bin") / ("python.exe" if os.name == "nt" else "python")


def _python_version(python_path: Path) -> tuple[int, int] | None:
    """Read the target venv's Python version without importing the bot."""

    if not python_path.is_file():
        return None
    try:
        result = subprocess.run(
            [str(python_path), "-c", "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
            check=False,
        )
        if result.returncode != 0:
            return None
        major, minor = (int(value) for value in result.stdout.strip().split(".", 1))
        return major, minor
    except (OSError, ValueError, subprocess.SubprocessError):
        return None


def _effective_requirements_file(requirements_file: Path, venv_name: str) -> Path:
    """Upgrade the old Playwright pin when a downloaded release targets Python 3.14.

    The launcher downloads the bot release at runtime, so an older GitHub archive
    can still contain the incompatible 1.48 requirement even after the checked-in
    requirements file is updated. Keep that release usable until it is republished.
    """

    python_version = _python_version(_get_python_path(venv_name))
    if python_version is None or python_version < (3, 14):
        return requirements_file

    try:
        lines = requirements_file.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        log_warning(f"Could not inspect bot requirements for compatibility: {exc}")
        return requirements_file

    changed = False
    normalized_lines = []
    for line in lines:
        if re.match(r"^\s*playwright(?:\s|[<>=!~])", line, flags=re.IGNORECASE) and "1.48" in line:
            normalized_lines.append("playwright>=1.62,<1.63")
            changed = True
        else:
            normalized_lines.append(line)

    if not changed:
        return requirements_file

    TEMP_FOLDER.mkdir(parents=True, exist_ok=True)
    compatible_file = TEMP_FOLDER / "requirements.python314.txt"
    compatible_file.write_text("\n".join(normalized_lines) + "\n", encoding="utf-8")
    message = "Updated legacy Playwright dependency for Python 3.14 compatibility"
    send_warning(message)
    log_info(f"Using compatibility requirements file: {compatible_file}")
    return compatible_file


def _download_release(status_bar):
    send_system("Downloading latest release...")
    _status(status_bar, "Downloading latest release...")
    log_info(f"Downloading from: {DOWNLOAD_URL}")

    chunks = []
    downloaded = 0
    with requests.get(DOWNLOAD_URL, stream=True, timeout=(10, 90)) as response:
        response.raise_for_status()
        total_size = int(response.headers.get("content-length", 0) or 0)
        for chunk in response.iter_content(chunk_size=65536):
            if state.is_stop_requested():
                raise RuntimeError("Installation cancelled")
            if not chunk:
                continue
            chunks.append(chunk)
            downloaded += len(chunk)
            if total_size > 0:
                percent = min(100, int(downloaded * 100 / total_size))
                _status(status_bar, f"Downloading: {percent}% ({downloaded / 1048576:.1f}/{total_size / 1048576:.1f} MB)")

    if not downloaded:
        raise RuntimeError("Release download was empty")
    send_success(f"Download complete ({downloaded / 1048576:.1f} MB)")
    log_info(f"Download complete: {downloaded} bytes")
    return b"".join(chunks)


def _safe_member_path(member_name: str) -> Path:
    member_path = Path(member_name)
    if member_path.is_absolute() or ".." in member_path.parts:
        raise RuntimeError(f"Unsafe archive path: {member_name}")
    destination = (TEMP_FOLDER / member_path).resolve()
    try:
        destination.relative_to(TEMP_FOLDER.resolve())
    except ValueError as exc:
        raise RuntimeError(f"Unsafe archive path: {member_name}") from exc
    return destination


def _extract_release(data, status_bar):
    send_system("Extracting release archive...")
    _status(status_bar, "Extracting files...")
    _cleanup_temp()
    TEMP_FOLDER.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(BytesIO(data)) as archive:
        members = [member for member in archive.infolist() if member.filename]
        if not members:
            raise RuntimeError("Release archive is empty")
        top_levels = set()
        for member in members:
            _safe_member_path(member.filename)
            parts = Path(member.filename).parts
            if parts:
                top_levels.add(parts[0])
        if len(top_levels) != 1:
            raise RuntimeError("Release archive has an unexpected layout")
        for member in members:
            archive.extract(member, TEMP_FOLDER)

    source_dir = TEMP_FOLDER / next(iter(top_levels))
    if not source_dir.is_dir():
        raise RuntimeError("Release archive did not contain a root folder")
    entrypoint = next((path for path in source_dir.iterdir() if path.is_file() and path.name.lower() in {"main.py", "run.py", "launcher.py"}), None)
    if entrypoint is None:
        raise RuntimeError("Release archive does not contain a supported bot entrypoint")

    send_success(f"Extracted {len(members)} files")
    log_info(f"Extracted {len(members)} files from archive")
    return source_dir


def _deployment_cleanup():
    shutil.rmtree(_STAGING_ROOT, ignore_errors=True)


def _deploy_files(source_dir, status_bar):
    """Validate and atomically replace bot/cache, retaining user config."""
    source_dir = Path(source_dir).resolve()
    if not source_dir.is_dir():
        raise RuntimeError("Deployment source folder is missing")

    send_system("Deploying files...")
    _status(status_bar, "Deploying bot files...")
    _deployment_cleanup()
    staging_bot = _STAGING_ROOT / "bot"
    staging_cache = _STAGING_ROOT / "cache" / "bot"
    backup_bot = _STAGING_ROOT / "backup" / "bot"
    backup_cache = _STAGING_ROOT / "backup" / "cache" / "bot"
    _STAGING_ROOT.mkdir(parents=True, exist_ok=True)

    old_config = BOT_FOLDER / "config.ini"
    preserved_config = old_config.read_bytes() if old_config.is_file() else None
    shutil.copytree(source_dir, staging_bot)
    shutil.copytree(source_dir, staging_cache)
    if preserved_config is not None:
        (staging_bot / "config.ini").write_bytes(preserved_config)
        send_info("Preserved existing bot configuration")

    if not any(path.is_file() and path.name.lower() in {"main.py", "run.py", "launcher.py"} for path in staging_bot.iterdir()):
        raise RuntimeError("Staged release failed entrypoint validation")

    moved_bot = False
    moved_cache = False
    try:
        if BOT_FOLDER.exists():
            backup_bot.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(BOT_FOLDER), str(backup_bot))
            moved_bot = True
        if CACHE_FOLDER.exists():
            backup_cache.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(CACHE_FOLDER), str(backup_cache))
            moved_cache = True
        BOT_FOLDER.parent.mkdir(parents=True, exist_ok=True)
        CACHE_FOLDER.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(staging_bot), str(BOT_FOLDER))
        shutil.move(str(staging_cache), str(CACHE_FOLDER))
    except Exception:
        shutil.rmtree(BOT_FOLDER, ignore_errors=True)
        shutil.rmtree(CACHE_FOLDER, ignore_errors=True)
        if moved_bot and backup_bot.exists():
            shutil.move(str(backup_bot), str(BOT_FOLDER))
        if moved_cache and backup_cache.exists():
            shutil.move(str(backup_cache), str(CACHE_FOLDER))
        raise
    finally:
        _deployment_cleanup()

    send_success("Files deployed to bot and cache folders")
    log_info("Files deployed to bot/ and cache/bot/")


def _cleanup_temp():
    if TEMP_FOLDER.exists():
        shutil.rmtree(TEMP_FOLDER, ignore_errors=True)
        log_info("Temporary extraction folder cleaned up")


def _run_command(label: str, command: list[str], status_bar, start_message: str, success_message: str) -> bool:
    if not command or not Path(command[0]).is_file():
        send_error(f"Executable not found: {command[0] if command else '<missing>'}")
        log_error(f"Executable not found for {label}: {command}")
        return False
    send_system(start_message)
    _status(status_bar, start_message)
    process = None
    try:
        process = subprocess.Popen(
            [str(item) for item in command],
            cwd=str(BOT_FOLDER),
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
            send_error(f"{label} failed (exit code {returncode})")
            log_error(f"{label} failed with exit code {returncode}")
            return False
        send_success(success_message)
        log_info(success_message)
        _status(status_bar, success_message)
        return True
    except Exception as exc:
        send_error(f"{label} failed: {exc}")
        log_exception(f"Exception during {label}")
        _status(status_bar, f"{label} failed")
        return False
    finally:
        state.remove_process(label)


def install_requirements(venv_name, status_bar=None) -> bool:
    requirements_file = BOT_FOLDER / "requirements.txt"
    if not requirements_file.is_file():
        send_info("No requirements.txt found — skipping")
        return True
    requirements_file = _effective_requirements_file(requirements_file, venv_name)
    python_path = _get_python_path(venv_name)
    command = [
        str(python_path),
        "-m",
        "pip",
        "install",
        "-r",
        str(requirements_file),
        "--quiet",
        "--no-warn-script-location",
        "--disable-pip-version-check",
    ]
    return _run_command("pip_install", command, status_bar, "Installing Python dependencies...", "Python dependencies installed")


def _install_requirements(venv_name, status_bar=None):
    return install_requirements(venv_name, status_bar)


def install_playwright(venv_name, status_bar=None) -> bool:
    python_path = _get_python_path(venv_name)
    command = [str(python_path), "-m", "playwright", "install", "chromium"]
    return _run_command("playwright_install", command, status_bar, "Installing Playwright browser...", "Playwright browser installed")


def _install_playwright(venv_name, status_bar=None):
    return install_playwright(venv_name, status_bar)


def run_install(venv_name, status_bar=None, on_started: Callable | None = None, on_finished: Callable | None = None, on_failed: Callable | None = None):
    send_system(f"Starting installation for venv: {venv_name}")
    log_info(f"Install started: venv={venv_name}")
    _status(status_bar, "Starting installation...")
    try:
        data = _download_release(status_bar)
        source_dir = _extract_release(data, status_bar)
        _deploy_files(source_dir, status_bar)
        _cleanup_temp()
        if not install_requirements(venv_name, status_bar):
            _status(status_bar, "Installation failed — dependency error")
            _call(on_failed, "Dependency installation failed")
            return None
        if not install_playwright(venv_name, status_bar):
            _status(status_bar, "Installation failed — Playwright error")
            _call(on_failed, "Playwright installation failed")
            return None
        send_success("Installation complete")
        log_info("Installation completed successfully")
        _status(status_bar, "Installation complete")
        return run_bot(venv_name, status_bar, on_started, on_finished, on_failed)
    except requests.RequestException as exc:
        send_error(f"Download failed: {exc}")
        log_exception("Download failed during install")
        _status(status_bar, "Download failed")
        _call(on_failed, "Download failed")
    except zipfile.BadZipFile:
        send_error("Downloaded file is not a valid zip archive")
        log_error("Bad zip file received")
        _status(status_bar, "Invalid download — bad archive")
        _call(on_failed, "Invalid release archive")
    except Exception as exc:
        send_error(f"Installation failed: {exc}")
        log_exception("Installation failed")
        _status(status_bar, "Installation failed")
        _call(on_failed, str(exc))
    finally:
        _cleanup_temp()
    return None
