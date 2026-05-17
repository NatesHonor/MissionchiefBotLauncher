from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, QPoint, QTimer
from PyQt6.QtWidgets import QWidget

if TYPE_CHECKING:
    from PyQt6.QtGui import QMouseEvent


class WindowDragMixin(QWidget):
    _drag_offset: QPoint | None = None
    _drag_active: bool = False
    _snap_margin: int = 16
    _was_maximized: bool = False
    _pending_pos: QPoint | None = None
    _move_timer: QTimer | None = None

    def _ensure_move_timer(self) -> None:
        if self._move_timer is None:
            self._move_timer = QTimer(self)
            self._move_timer.setInterval(16)
            self._move_timer.setSingleShot(True)
            self._move_timer.timeout.connect(self._apply_pending_move)

    def _apply_pending_move(self) -> None:
        if self._pending_pos is not None:
            self.move(self._pending_pos)
            self._pending_pos = None

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._ensure_move_timer()
            self._drag_active = True
            self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self._was_maximized = self.isMaximized()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if not self._drag_active or not self._drag_offset:
            return
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return

        if self._was_maximized:
            old_width = self.width()
            self.showNormal()
            ratio = event.globalPosition().toPoint().x() / old_width
            new_x = int(self.width() * ratio)
            self._drag_offset = QPoint(new_x, self._drag_offset.y())
            self._was_maximized = False

        new_pos = event.globalPosition().toPoint() - self._drag_offset
        screen = self.screen().availableGeometry()

        snapped_x = new_pos.x()
        snapped_y = new_pos.y()

        if abs(new_pos.x() - screen.left()) < self._snap_margin:
            snapped_x = screen.left()
        elif abs(new_pos.x() + self.width() - screen.right()) < self._snap_margin:
            snapped_x = screen.right() - self.width()

        if abs(new_pos.y() - screen.top()) < self._snap_margin:
            snapped_y = screen.top()
        elif abs(new_pos.y() + self.height() - screen.bottom()) < self._snap_margin:
            snapped_y = screen.bottom() - self.height()

        self._pending_pos = QPoint(snapped_x, snapped_y)
        if not self._move_timer.isActive():
            self._move_timer.start()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self._drag_active:
            if self._move_timer and self._move_timer.isActive():
                self._move_timer.stop()
            if self._pending_pos is not None:
                self.move(self._pending_pos)
                self._pending_pos = None

            screen = self.screen().availableGeometry()
            pos = self.frameGeometry().topLeft()

            if pos.y() <= screen.top() + 2:
                self.showMaximized()

            self._drag_active = False
            self._drag_offset = None