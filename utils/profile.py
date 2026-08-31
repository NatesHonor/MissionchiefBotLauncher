"""Local operator profile storage; no account or sign-in service is involved."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import uuid
from pathlib import Path

from utils.paths import DATA_ROOT


PROFILE_FILE = DATA_ROOT / "profile.json"
AVATAR_FOLDER = DATA_ROOT / "profile"
DEFAULT_PROFILE = {
    "display_name": "Operator",
    "role": "Mission Chief",
    "avatar": "",
}
ALLOWED_AVATAR_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"}
MAX_AVATAR_BYTES = 5 * 1024 * 1024


def _normalise(profile: dict | None) -> dict:
    values = dict(DEFAULT_PROFILE)
    if isinstance(profile, dict):
        for key in values:
            value = profile.get(key)
            if isinstance(value, str):
                values[key] = value.strip()[:64]
    values["display_name"] = values["display_name"] or DEFAULT_PROFILE["display_name"]
    values["role"] = values["role"] or DEFAULT_PROFILE["role"]
    return values


def load_profile() -> dict:
    try:
        with PROFILE_FILE.open("r", encoding="utf-8") as handle:
            return _normalise(json.load(handle))
    except (OSError, ValueError, TypeError):
        return dict(DEFAULT_PROFILE)


def save_profile(profile: dict) -> dict:
    values = _normalise(profile)
    PROFILE_FILE.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=f".{PROFILE_FILE.name}.", suffix=".tmp", dir=PROFILE_FILE.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            json.dump(values, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, PROFILE_FILE)
    finally:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
    return values


def update_profile(display_name: str | None = None, role: str | None = None) -> dict:
    profile = load_profile()
    if display_name is not None:
        profile["display_name"] = display_name
    if role is not None:
        profile["role"] = role
    return save_profile(profile)


def avatar_path(profile: dict | None = None) -> Path | None:
    values = _normalise(profile or load_profile())
    filename = values.get("avatar", "")
    if not filename:
        return None
    path = (AVATAR_FOLDER / Path(filename).name).resolve()
    try:
        path.relative_to(AVATAR_FOLDER.resolve())
    except ValueError:
        return None
    return path if path.is_file() else None


def set_avatar(source: str | os.PathLike[str]) -> dict:
    source_path = Path(source).expanduser().resolve()
    if not source_path.is_file():
        raise ValueError("Selected avatar file does not exist")
    if source_path.suffix.lower() not in ALLOWED_AVATAR_EXTENSIONS:
        raise ValueError("Choose a PNG, JPG, WEBP, BMP, or GIF image")
    if source_path.stat().st_size > MAX_AVATAR_BYTES:
        raise ValueError("Avatar images must be 5 MB or smaller")

    AVATAR_FOLDER.mkdir(parents=True, exist_ok=True)
    filename = f"avatar-{uuid.uuid4().hex}{source_path.suffix.lower()}"
    destination = AVATAR_FOLDER / filename
    shutil.copy2(source_path, destination)
    profile = load_profile()
    old_path = avatar_path(profile)
    profile["avatar"] = filename
    saved = save_profile(profile)
    if old_path and old_path != destination:
        try:
            old_path.unlink()
        except OSError:
            pass
    return saved


def clear_avatar() -> dict:
    profile = load_profile()
    old_path = avatar_path(profile)
    profile["avatar"] = ""
    saved = save_profile(profile)
    if old_path:
        try:
            old_path.unlink()
        except OSError:
            pass
    return saved
