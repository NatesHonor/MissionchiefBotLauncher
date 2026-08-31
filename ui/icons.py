"""Small, dependency-free SVG icon set for consistent launcher controls."""

from __future__ import annotations

from PyQt6.QtCore import QByteArray, QSize, Qt
from PyQt6.QtGui import QIcon, QImage, QPainter, QPixmap
from PyQt6.QtSvg import QSvgRenderer


_PATHS = {
    "dashboard": '<rect x="4" y="4" width="6" height="6" rx="1"/><rect x="14" y="4" width="6" height="6" rx="1"/><rect x="4" y="14" width="6" height="6" rx="1"/><rect x="14" y="14" width="6" height="6" rx="1"/>',
    "globe": '<circle cx="12" cy="12" r="8"/><path d="M4 12h16M12 4c2.2 2.2 3.2 4.9 3.2 8S14.2 17.8 12 20M12 4c-2.2 2.2-3.2 4.9-3.2 8S9.8 17.8 12 20"/>',
    "settings": '<path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.38a2 2 0 0 0-.73-2.73l-.15-.09a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/>',
    "play": '<path d="m8 5 11 7-11 7Z" fill="currentColor" stroke="none"/>',
    "stop": '<rect x="7" y="7" width="10" height="10" rx="1.5" fill="currentColor" stroke="none"/>',
    "logout": '<path d="M10 5H6.5A1.5 1.5 0 0 0 5 6.5v11A1.5 1.5 0 0 0 6.5 19H10M14 8l4 4-4 4M18 12H9"/>',
    "external": '<path d="M14 5h5v5M19 5l-8 8"/><path d="M18 13v4.5A1.5 1.5 0 0 1 16.5 19h-10A1.5 1.5 0 0 1 5 17.5v-10A1.5 1.5 0 0 1 6.5 6H11"/>',
    "trash": '<path d="M5 7h14M10 11v5M14 11v5M8 7l.7-2h6.6l.7 2M7 7l.7 12h8.6L17 7"/>',
    "user": '<circle cx="12" cy="8" r="3"/><path d="M5.5 19a6.5 6.5 0 0 1 13 0"/>',
    "minimize": '<path d="M5 12h14"/>',
    "maximize": '<rect x="6" y="6" width="12" height="12" rx="1"/>',
    "close": '<path d="m7 7 10 10M17 7 7 17"/>',
}


def _svg(name: str, color: str) -> QByteArray:
    path = _PATHS.get(name, _PATHS["dashboard"]).replace("currentColor", color)
    return QByteArray(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">{path}</svg>'.encode("utf-8")
    )


def pixmap(name: str, size: int = 20, color: str = "#7F9DB8") -> QPixmap:
    image = QImage(size, size, QImage.Format.Format_ARGB32_Premultiplied)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    renderer = QSvgRenderer(_svg(name, color))
    renderer.render(painter)
    painter.end()
    return QPixmap.fromImage(image)


def icon(name: str, color: str = "#7F9DB8", size: int = 20) -> QIcon:
    result = QIcon()
    result.addPixmap(pixmap(name, size, color), QIcon.Mode.Normal, QIcon.State.Off)
    return result


def icon_size(size: int = 20) -> QSize:
    return QSize(size, size)
