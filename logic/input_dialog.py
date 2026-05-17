from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPainter, QPainterPath, QLinearGradient, QBrush, QPen, QFont
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QWidget, QGraphicsDropShadowEffect, QPushButton
)


def show_input_dialog(title="Input", prompt="Enter value:", placeholder="", parent=None):
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
            background-color: #13111C;
            border-radius: 14px;
            border: 1px solid #2A2540;
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
                stop:0 #6C5CE7, stop:0.5 #A855F7, stop:1 #EC4899);
            border: none; border-radius: 0;
        }
    """)
    layout.addWidget(accent)

    title_label = QLabel(title)
    title_label.setStyleSheet("""
        QLabel {
            color: #F1F0F5; font-size: 16px; font-weight: 700;
            background: transparent; border: none;
        }
    """)
    layout.addWidget(title_label)

    prompt_label = QLabel(prompt)
    prompt_label.setStyleSheet("""
        QLabel {
            color: #7C7A85; font-size: 13px;
            background: transparent; border: none;
        }
    """)
    layout.addWidget(prompt_label)

    input_field = QLineEdit()
    input_field.setPlaceholderText(placeholder)
    input_field.setFixedHeight(40)
    input_field.setStyleSheet("""
        QLineEdit {
            background-color: #08070D; color: #C9C8D0;
            border: 1px solid #1E1B2E; border-radius: 8px;
            padding: 0 12px; font-size: 13px;
            font-family: 'Segoe UI', sans-serif;
            selection-background-color: #6C5CE7;
        }
        QLineEdit:focus { border-color: #6C5CE7; }
    """)
    layout.addWidget(input_field)

    btn_row = QHBoxLayout()
    btn_row.setSpacing(10)

    cancel_btn = QPushButton("Cancel")
    cancel_btn.setFixedHeight(38)
    cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
    cancel_btn.setStyleSheet("""
        QPushButton {
            background: transparent; color: #6B6878;
            font-size: 13px; font-weight: 600;
            border: 1px solid #2A2540; border-radius: 8px; padding: 0 20px;
        }
        QPushButton:hover { color: #9CA3AF; border-color: #3D3756; background: #1A1726; }
    """)
    cancel_btn.clicked.connect(dialog.reject)
    btn_row.addWidget(cancel_btn)

    confirm_btn = QPushButton("Confirm")
    confirm_btn.setFixedHeight(38)
    confirm_btn.setCursor(Qt.CursorShape.PointingHandCursor)
    confirm_btn.setStyleSheet("""
        QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #6C5CE7, stop:0.5 #A855F7, stop:1 #EC4899);
            color: #FFFFFF; font-size: 13px; font-weight: 700;
            border: none; border-radius: 8px; padding: 0 24px;
        }
        QPushButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #7C6CF7, stop:0.5 #B86AF7, stop:1 #F472B6);
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