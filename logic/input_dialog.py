from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPainter, QPainterPath, QLinearGradient, QBrush, QPen, QFont
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QWidget, QGraphicsDropShadowEffect, QPushButton
)
from PyQt6.QtWidgets import QDialogButtonBox

from ui.theme import current_theme_name, stylesheet
from utils.localization import tr
from utils.settings_store import get as get_setting


def _legacy_show_input_dialog(title="Input", prompt="Enter value:", placeholder="", parent=None):
    dialog = QDialog(parent)
    dialog.setWindowTitle(title)
    dialog.setFixedSize(400, 220)
    dialog.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
    dialog.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

    dialog._drag_pos = None
    dialog._result = None

    def mouse_press(event):
        if event.button() == Qt.MouseButton.LeftButton:
            dialog._drag_pos = event.globalPosition().toPoint() - dialog.frameGeometry().topLeft()

    def mouse_move(event):
        if dialog._drag_pos and event.buttons() == Qt.MouseButton.LeftButton:
            dialog.move(event.globalPosition().toPoint() - dialog._drag_pos)

    def mouse_release(event):
        dialog._drag_pos = None

    dialog.mousePressEvent = mouse_press
    dialog.mouseMoveEvent = mouse_move
    dialog.mouseReleaseEvent = mouse_release

    container = QWidget(dialog)
    container.setGeometry(0, 0, 400, 220)
    container.setStyleSheet("""
        QWidget {
            background-color: #0B1B2D;
            border-radius: 14px;
            border: 1px solid #1D3B5B;
        }
    """)

    shadow = QGraphicsDropShadowEffect(dialog)
    shadow.setBlurRadius(40)
    shadow.setColor(QColor(0, 0, 0, 150))
    shadow.setOffset(0, 8)
    container.setGraphicsEffect(shadow)

    layout = QVBoxLayout(container)
    layout.setContentsMargins(24, 20, 24, 20)
    layout.setSpacing(12)

    accent = QWidget()
    accent.setFixedHeight(3)
    accent.setStyleSheet("""
        QWidget {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #1D65D8, stop:0.5 #2583E8, stop:1 #21B8D4);
            border: none; border-radius: 0;
        }
    """)
    layout.addWidget(accent)

    title_label = QLabel(title)
    title_label.setStyleSheet("""
        QLabel {
            color: #EAF4FF; font-size: 16px; font-weight: 700;
            background: transparent; border: none;
        }
    """)
    layout.addWidget(title_label)

    prompt_label = QLabel(prompt)
    prompt_label.setStyleSheet("""
        QLabel {
            color: #7F9DB8; font-size: 13px;
            background: transparent; border: none;
        }
    """)
    layout.addWidget(prompt_label)

    input_field = QLineEdit()
    input_field.setPlaceholderText(placeholder)
    input_field.setFixedHeight(40)
    input_field.setStyleSheet("""
        QLineEdit {
            background-color: #07111F; color: #C7D8EA;
            border: 1px solid #1D3B5B; border-radius: 8px;
            padding: 0 12px; font-size: 13px;
            font-family: 'Segoe UI', sans-serif;
            selection-background-color: #2583E8;
        }
        QLineEdit:focus { border-color: #2583E8; }
    """)
    layout.addWidget(input_field)

    btn_row = QHBoxLayout()
    btn_row.setSpacing(10)

    cancel_btn = QPushButton("Cancel")
    cancel_btn.setFixedHeight(38)
    cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
    cancel_btn.setStyleSheet("""
        QPushButton {
            background: transparent; color: #7890AD;
            font-size: 13px; font-weight: 600;
            border: 1px solid #1D3B5B; border-radius: 8px; padding: 0 20px;
        }
        QPushButton:hover { color: #A8BCD1; border-color: #2D537A; background: #102640; }
    """)
    cancel_btn.clicked.connect(dialog.reject)
    btn_row.addWidget(cancel_btn)

    confirm_btn = QPushButton("Confirm")
    confirm_btn.setFixedHeight(38)
    confirm_btn.setCursor(Qt.CursorShape.PointingHandCursor)
    confirm_btn.setStyleSheet("""
        QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #1D65D8, stop:0.5 #2583E8, stop:1 #21B8D4);
            color: #FFFFFF; font-size: 13px; font-weight: 700;
            border: none; border-radius: 8px; padding: 0 24px;
        }
        QPushButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #3B82F6, stop:0.5 #4BA3FF, stop:1 #32B9E8);
        }
    """)

    def on_confirm():
        text = input_field.text().strip()
        if text:
            dialog._result = text
            dialog.accept()

    confirm_btn.clicked.connect(on_confirm)
    input_field.returnPressed.connect(on_confirm)
    btn_row.addWidget(confirm_btn)

    layout.addLayout(btn_row)

    input_field.setFocus()

    if dialog.exec() == QDialog.DialogCode.Accepted:
        return dialog._result
    return None


def show_input_dialog(title=None, prompt=None, placeholder="", parent=None):
    """Show a compact, themed input dialog and return text or None."""

    dialog = QDialog(parent)
    dialog.setObjectName("InputDialog")
    dialog.setWindowTitle(title or tr("input"))
    dialog.setMinimumWidth(440)
    dialog.setModal(True)
    dialog.setStyleSheet(stylesheet(current_theme_name(get_setting("theme", "ocean"))))

    layout = QVBoxLayout(dialog)
    layout.setContentsMargins(24, 22, 24, 20)
    layout.setSpacing(12)

    title_label = QLabel(title or tr("input"))
    title_label.setObjectName("PageTitle")
    layout.addWidget(title_label)

    prompt_label = QLabel(prompt or tr("enter_value"))
    prompt_label.setObjectName("Hint")
    prompt_label.setWordWrap(True)
    layout.addWidget(prompt_label)

    input_field = QLineEdit()
    input_field.setPlaceholderText(placeholder)
    input_field.setClearButtonEnabled(True)
    layout.addWidget(input_field)

    buttons = QDialogButtonBox(
        QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok
    )
    buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(tr("cancel"))
    buttons.button(QDialogButtonBox.StandardButton.Ok).setText(tr("confirm"))
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)
    layout.addWidget(buttons)

    input_field.returnPressed.connect(dialog.accept)
    input_field.setFocus()
    if dialog.exec() != QDialog.DialogCode.Accepted:
        return None
    value = input_field.text().strip()
    return value or None
