"""Safe, atomic persistence for launcher settings."""

from __future__ import annotations

import configparser
import os
import re
import tempfile
from pathlib import Path

from utils.paths import LAUNCHER_CONFIG, RESOURCE_ROOT


DEFAULT_SETTINGS = {
    "Launcher": {
        "version": "1.2.3",
        "venv": "",
        "region": "",
        "theme": "ocean",
        "language": "auto",
        "auto_update": "true",
        "check_updates_on_start": "true",
        "log_upload_url": "",
    }
}


def parse_version(value: str | None) -> tuple[int, ...]:
    numbers = re.findall(r"\d+", str(value or ""))
    return tuple(int(number) for number in numbers) or (0,)


def _new_parser() -> configparser.ConfigParser:
    parser = configparser.ConfigParser()
    parser.optionxform = str.lower
    return parser


def _default_parser() -> configparser.ConfigParser:
    parser = _new_parser()
    for section, values in DEFAULT_SETTINGS.items():
        parser[section] = values
    return parser


def load(path: Path = LAUNCHER_CONFIG) -> configparser.ConfigParser:
    parser = _new_parser()
    if path.exists():
        parser.read(path, encoding="utf-8")
    return parser


def write_atomic(parser: configparser.ConfigParser, path: Path = LAUNCHER_CONFIG) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            parser.write(handle)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
    finally:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass


def write_text_atomic(text: str, path: Path) -> None:
    """Write arbitrary text atomically, preserving a valid previous file on failure."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
    finally:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass


def ensure_launcher_settings() -> Path:
    """Create/update the writable settings file while preserving user values."""

    bundled_path = RESOURCE_ROOT / "launcher_settings.ini"
    bundled = load(bundled_path) if bundled_path.exists() else _default_parser()
    existing = load(LAUNCHER_CONFIG)

    if not LAUNCHER_CONFIG.exists():
        write_atomic(bundled, LAUNCHER_CONFIG)
        return LAUNCHER_CONFIG

    merged = _new_parser()
    for section in bundled.sections():
        merged.add_section(section)
        for key, value in bundled.items(section):
            merged.set(section, key, value)

    for section in existing.sections():
        if not merged.has_section(section):
            merged.add_section(section)
        for key, value in existing.items(section):
            if value.strip() or not merged.has_option(section, key):
                merged.set(section, key, value)

    bundled_version = bundled.get("Launcher", "version", fallback="0.0.0")
    existing_version = existing.get("Launcher", "version", fallback="0.0.0")
    if parse_version(bundled_version) > parse_version(existing_version):
        merged.set("Launcher", "version", bundled_version)

    write_atomic(merged, LAUNCHER_CONFIG)
    return LAUNCHER_CONFIG


def get(key: str, fallback: str = "", section: str = "Launcher") -> str:
    parser = load()
    return parser.get(section, key, fallback=fallback).strip()


def set_values(values: dict[str, str], section: str = "Launcher") -> None:
    parser = load()
    if not parser.has_section(section):
        parser.add_section(section)
    for key, value in values.items():
        parser.set(section, key, str(value))
    write_atomic(parser)
