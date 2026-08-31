from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton

from utils.localization import tr
from utils.settings_store import get as get_setting
from ui.icons import icon, icon_size
from ui.theme import THEMES, current_theme_name


class TitleBar(QFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self._drag_offset = None
        self.setObjectName("TopBar")
        self.setFixedHeight(64)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 10, 14, 10)
        layout.setSpacing(11)

        self.logo = QLabel("MH")
        self.logo.setObjectName("BrandMark")
        self.logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo.setFixedSize(38, 38)
        layout.addWidget(self.logo)

        title_block = QFrame()
        title_block.setStyleSheet("background: transparent; border: 0;")
        title_layout = QHBoxLayout(title_block)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(8)
        self.title = QLabel(tr("app_name"))
        self.title.setObjectName("BrandTitle")
        self.page_label = QLabel(tr("dashboard"))
        self.page_label.setObjectName("Muted")
        title_layout.addWidget(self.title)
        title_layout.addWidget(QLabel("/") , alignment=Qt.AlignmentFlag.AlignVCenter)
        title_layout.addWidget(self.page_label)
        layout.addWidget(title_block)
        layout.addStretch()

        self.connection_label = QLabel(f"●  {tr('connected')}")
        self.connection_label.setObjectName("ConnectionLabel")
        layout.addWidget(self.connection_label)
        layout.addSpacing(12)

        self.minimize_btn = self._make_button("minimize", tr("minimize"), self.parent.showMinimized)
        self.maximize_btn = self._make_button("maximize", tr("maximize"), self._toggle_maximize)
        self.close_btn = self._make_button("close", tr("close"), self.parent.close)
        self.close_btn.setObjectName("CloseButton")
        layout.addWidget(self.minimize_btn)
        layout.addWidget(self.maximize_btn)
        layout.addWidget(self.close_btn)

    def _make_button(self, icon_name, tooltip, callback):
        button = QPushButton()
        button.setObjectName("IconButton")
        button.setFixedSize(30, 30)
        button.setIconSize(icon_size(16))
        button.setToolTip(tooltip)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.clicked.connect(callback)
        button.setProperty("icon_name", icon_name)
        self._set_icon(button, icon_name)
        return button

    @staticmethod
    def _icon_color():
        theme = THEMES[current_theme_name(get_setting("theme", "ocean"))]
        return theme.muted

    def _set_icon(self, button, icon_name):
        button.setIcon(icon(icon_name, self._icon_color(), 20))

    def set_page(self, name):
        self.page_label.setText(name)

    def refresh_text(self):
        self.title.setText(tr("app_name"))
        self.connection_label.setText(f"●  {tr('connected')}")
        self.minimize_btn.setToolTip(tr("minimize"))
        self.maximize_btn.setToolTip(tr("maximize"))
        self.close_btn.setToolTip(tr("close"))
        self._set_icon(self.minimize_btn, "minimize")
        self._set_icon(self.maximize_btn, "maximize")
        self._set_icon(self.close_btn, "close")

    def _toggle_maximize(self):
        if self.parent.isMaximized():
            self.parent.showNormal()
        else:
            self.parent.showMaximized()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_offset = event.globalPosition().toPoint() - self.parent.frameGeometry().topLeft()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_offset and event.buttons() & Qt.MouseButton.LeftButton:
            self.parent.move(event.globalPosition().toPoint() - self._drag_offset)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_offset = None
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._toggle_maximize()
            event.accept()
        else:
            super().mouseDoubleClickEvent(event)
