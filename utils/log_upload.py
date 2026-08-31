"""Upload a sanitized launcher session log to a configured sharing service."""

from __future__ import annotations

import os
import re
from pathlib import Path

import requests

from handlers.logging import get_log_path
from utils.paths import LOG_FOLDER
from utils.settings_store import get as get_setting


_SECRET_PATTERN = re.compile(
    r"(?im)(\b(?:password|token|authorization|cookie|secret|private[_ -]?key)\b\s*[:=]\s*)([^\r\n]+)"
)
_URL_KEYS = ("url", "share_url", "shareUrl", "link")


def latest_log_path() -> Path | None:
    """Return the active session log, or the newest retained session log."""

    active = get_log_path()
    if active:
        active_path = Path(active)
        if active_path.is_file():
            return active_path
    candidates = [path for path in LOG_FOLDER.rglob("*.log") if path.is_file()]
    return max(candidates, key=lambda path: path.stat().st_mtime, default=None)


def sanitize_log(text: str) -> str:
    """Redact common secret-shaped values before a log leaves the machine."""

    return _SECRET_PATTERN.sub(r"\1[REDACTED]", str(text or ""))


def _configured_endpoint() -> str:
    return (
        os.getenv("MISSION_HELPER_LOG_UPLOAD_URL", "").strip()
        or get_setting("log_upload_url", "").strip()
    )


def _response_url(response) -> str | None:
    location = str(response.headers.get("Location", "")).strip()
    if location.startswith(("https://", "http://")):
        return location
    try:
        payload = response.json()
    except ValueError:
        payload = None
    if isinstance(payload, dict):
        for key in _URL_KEYS:
            value = str(payload.get(key, "")).strip()
            if value.startswith(("https://", "http://")):
                return value
    if isinstance(payload, str) and payload.startswith(("https://", "http://")):
        return payload
    return None


def upload_latest_log(endpoint: str | None = None) -> str:
    """Upload the current log and return the service-provided share URL."""

    destination = (endpoint or _configured_endpoint()).strip()
    if not destination:
        raise RuntimeError(
            "No log upload endpoint is configured. Set log_upload_url in "
            "launcher_settings.ini or MISSION_HELPER_LOG_UPLOAD_URL."
        )
    log_path = latest_log_path()
    if not log_path:
        raise RuntimeError("No launcher session log is available to upload.")
    try:
        content = sanitize_log(log_path.read_text(encoding="utf-8", errors="replace"))
    except OSError as error:
        raise RuntimeError(f"Could not read the launcher log: {error}") from error

    response = requests.post(
        destination,
        files={"file": (log_path.name, content.encode("utf-8"), "text/plain")},
        timeout=30,
    )
    response.raise_for_status()
    url = _response_url(response)
    if not url:
        raise RuntimeError("The log service did not return a shareable URL.")
    return url
