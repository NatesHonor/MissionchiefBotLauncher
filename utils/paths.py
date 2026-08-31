"""Centralized paths for both source and packaged launcher runs.

The launcher must not depend on the process working directory.  Shortcuts,
PyInstaller, and IDEs all choose different working directories, so every
runtime path is resolved from the launcher installation/data directory here.
"""

from __future__ import annotations

import os
import sys
import tempfile
import uuid
from functools import lru_cache
from pathlib import Path


APP_NAME = "Mission Helper"
PROJECT_ROOT = Path(__file__).resolve().parents[1]


def resource_root() -> Path:
    """Return the read-only directory containing bundled application assets."""

    bundled_root = getattr(sys, "_MEIPASS", None)
    if bundled_root:
        return Path(bundled_root).resolve()
    return PROJECT_ROOT


def install_root() -> Path:
    """Return the directory containing the source tree or packaged executable."""

    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return PROJECT_ROOT


def _can_write(directory: Path) -> bool:
    """Check write access without leaving a probe file behind."""

    try:
        directory.mkdir(parents=True, exist_ok=True)
        probe = directory / f".write-test-{uuid.uuid4().hex}"
        probe.touch(exist_ok=False)
        probe.unlink()
        return True
    except (OSError, PermissionError):
        return False


def _fallback_data_root() -> Path:
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / APP_NAME

    return Path.home() / ".mission-helper"


@lru_cache(maxsize=1)
def data_root() -> Path:
    """Return the writable directory for settings, bot files, logs, and cache."""

    configured = os.environ.get("MISSION_HELPER_DATA_DIR", "").strip()
    if configured:
        configured_root = Path(os.path.expandvars(configured)).expanduser().resolve()
        configured_root.mkdir(parents=True, exist_ok=True)
        return configured_root

    preferred = install_root()
    if _can_write(preferred):
        return preferred

    for candidate in (
        _fallback_data_root().resolve(),
        (Path(tempfile.gettempdir()) / APP_NAME).resolve(),
    ):
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            return candidate
        except (OSError, PermissionError):
            continue
    return preferred


RESOURCE_ROOT = resource_root()
INSTALL_ROOT = install_root()
DATA_ROOT = data_root()

LAUNCHER_CONFIG = DATA_ROOT / "launcher_settings.ini"
BOT_FOLDER = DATA_ROOT / "bot"
CACHE_FOLDER = DATA_ROOT / "cache" / "bot"
TEMP_FOLDER = DATA_ROOT / "temp_extract"
UPDATE_FOLDER = DATA_ROOT / "updates"
LOG_FOLDER = DATA_ROOT / "logs"
LOCK_FILE = DATA_ROOT / "launcher.lock"


def resource_path(*parts: str) -> Path:
    return RESOURCE_ROOT.joinpath(*parts)


def resolve_data_path(path_value: str | os.PathLike[str]) -> Path:
    """Resolve a user-configured path relative to the writable data directory."""

    value = os.path.expandvars(os.fspath(path_value)).strip()
    path = Path(value).expanduser()
    if path.is_absolute():
        return path.resolve()
    return (DATA_ROOT / path).resolve()


def resolve_venv_path(path_value: str | os.PathLike[str]) -> Path:
    value = os.fspath(path_value).strip()
    return resolve_data_path(value or "missionchief_venv")


def ensure_runtime_directories() -> None:
    for directory in (DATA_ROOT, BOT_FOLDER, CACHE_FOLDER.parent, TEMP_FOLDER.parent, UPDATE_FOLDER, LOG_FOLDER):
        directory.mkdir(parents=True, exist_ok=True)
