import configparser

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QDialog, QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget

from utils.localization import tr
from utils.paths import LAUNCHER_CONFIG
from utils.profile import avatar_path, load_profile
from utils.regions import get_selected_region, list_regions, select_region
from utils.settings_store import parse_version
from utils.settings_store import get as get_setting
from ui.icons import icon, icon_size, pixmap
from ui.theme import THEMES, current_theme_name, stylesheet


class RegionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_region = None
        self.setWindowTitle(tr("select_region"))
        self.setFixedSize(460, 560)
        self.setModal(True)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setObjectName("RegionDialog")
        self.setStyleSheet(stylesheet(current_theme_name(get_setting("theme", "ocean"))))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QFrame()
        header.setObjectName("DialogHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 14, 14, 14)
        header_layout.setSpacing(10)
        header_icon = QLabel()
        header_icon.setPixmap(pixmap("globe", 22, self._icon_color()))
        header_layout.addWidget(header_icon)
        dialog_title = QLabel(tr("select_region"))
        dialog_title.setObjectName("DialogTitle")
        header_layout.addWidget(dialog_title)
        header_layout.addStretch()
        close_button = QPushButton()
        close_button.setObjectName("IconButton")
        close_button.setIcon(icon("close", self._icon_color(), 20))
        close_button.setIconSize(icon_size(16))
        close_button.setFixedSize(30, 30)
        close_button.setToolTip(tr("close"))
        close_button.clicked.connect(self.reject)
        header_layout.addWidget(close_button)
        layout.addWidget(header)

        body = QFrame()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(22, 18, 22, 22)
        body_layout.setSpacing(9)
        title = QLabel(tr("choose_region"))
        title.setObjectName("PageTitle")
        body_layout.addWidget(title)
        subtitle = QLabel(tr("region_hint"))
        subtitle.setObjectName("Hint")
        body_layout.addWidget(subtitle)
        body_layout.addSpacing(6)
        scroll = QScrollArea()
        scroll.setObjectName("RegionList")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 8, 0)
        content_layout.setSpacing(8)
        for region in list_regions():
            button = QPushButton(region)
            button.setObjectName("SecondaryButton")
            button.setProperty("current", region == get_selected_region())
            button.setFixedHeight(42)
            button.clicked.connect(lambda checked=False, value=region: self._select(value))
            content_layout.addWidget(button)
        content_layout.addStretch()
        scroll.setWidget(content)
        body_layout.addWidget(scroll, 1)
        layout.addWidget(body, 1)

    def _select(self, region_name):
        self.selected_region = region_name
        self.accept()

    @staticmethod
    def _icon_color():
        return THEMES[current_theme_name(get_setting("theme", "ocean"))].cyan


class UserCard(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ProfileCard")
        self.avatar = QLabel()
        self.avatar.setFixedSize(42, 42)
        self.avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.avatar.setObjectName("Avatar")
        self.name_label = QLabel()
        self.name_label.setObjectName("ProfileName")
        self.role_label = QLabel()
        self.role_label.setObjectName("Muted")
        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(2)
        text_layout.addWidget(self.name_label)
        text_layout.addWidget(self.role_label)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(11)
        layout.addWidget(self.avatar)
        layout.addLayout(text_layout, 1)
        self.refresh()

    def refresh(self):
        profile = load_profile()
        self.name_label.setText(profile["display_name"])
        self.role_label.setText(profile["role"])
        path = avatar_path(profile)
        if path:
            avatar_pixmap = QPixmap(str(path)).scaled(42, 42, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
            self.avatar.setPixmap(avatar_pixmap)
            self.avatar.setText("")
        else:
            self.avatar.setPixmap(pixmap("user", 26, self._icon_color()))
            self.avatar.setText("")

    @staticmethod
    def _icon_color():
        return THEMES[current_theme_name(get_setting("theme", "ocean"))].cyan


class Sidebar(QFrame):
    def __init__(self, parent, stack):
        super().__init__(parent)
        self.parent = parent
        self.stack = stack
        self._active_button = None
        self.setObjectName("Sidebar")
        self.setFixedWidth(238)
        self.current_version = self._read_local_version()
        self.latest_version = self.current_version
        self.update_available = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 16, 14, 16)
        layout.setSpacing(7)
        self.user_card = UserCard()
        self.user_card.setCursor(Qt.CursorShape.PointingHandCursor)
        self.user_card.mousePressEvent = lambda event: self._navigate("settings")
        layout.addWidget(self.user_card)
        layout.addSpacing(18)

        self.navigation_label = self._section_label(tr("navigation"))
        layout.addWidget(self.navigation_label)
        self.dashboard_btn = self._nav_button("dashboard", tr("dashboard"), "dashboard")
        self.region_btn = self._nav_button("globe", self._get_region(), "region")
        self.settings_btn = self._nav_button("settings", tr("settings"), "settings")
        layout.addWidget(self.dashboard_btn)
        layout.addWidget(self.region_btn)
        layout.addWidget(self.settings_btn)
        layout.addSpacing(18)

        self.controls_label = self._section_label(tr("controls"))
        layout.addWidget(self.controls_label)
        self.run_btn = self._nav_button("play", tr("start_bot"), "run")
        layout.addWidget(self.run_btn)
        layout.addStretch(1)

        self.update_card = QFrame()
        self.update_card.setObjectName("UpdateCard")
        update_layout = QVBoxLayout(self.update_card)
        update_layout.setContentsMargins(12, 10, 12, 10)
        self.update_title = QLabel(tr("up_to_date"))
        self.update_title.setObjectName("UpdateTitle")
        self.update_title.setProperty("available", False)
        self.update_version = QLabel(f"{tr('version')} {self.current_version}")
        self.update_version.setObjectName("Muted")
        update_layout.addWidget(self.update_title)
        update_layout.addWidget(self.update_version)
        layout.addWidget(self.update_card)
        self.exit_btn = self._nav_button("logout", tr("exit"), "exit")
        layout.addWidget(self.exit_btn)
        self._set_active(self.dashboard_btn)

    def _section_label(self, text):
        label = QLabel(text.upper())
        label.setObjectName("Eyebrow")
        label.setContentsMargins(4, 4, 4, 4)
        return label

    def _nav_button(self, icon_name, text, action):
        button = QPushButton(text)
        button.setObjectName("NavButton")
        button.setIconSize(icon_size(18))
        button.setProperty("icon_name", icon_name)
        button.setProperty("active", False)
        self._set_button_icon(button)
        if action == "dashboard":
            button.clicked.connect(lambda: self._navigate("dashboard"))
        elif action == "region":
            button.clicked.connect(self.change_region)
        elif action == "settings":
            button.clicked.connect(lambda: self._navigate("settings"))
        elif action == "run":
            button.clicked.connect(self._toggle_bot)
        elif action == "exit":
            button.clicked.connect(self.parent.close)
        return button

    def _read_local_version(self):
        config = configparser.ConfigParser()
        config.read(LAUNCHER_CONFIG, encoding="utf-8")
        return config.get("Launcher", "version", fallback="0.0.0")

    def _get_region(self):
        return get_selected_region() or tr("region")

    def _navigate(self, page):
        if page == "dashboard":
            self._set_active(self.dashboard_btn)
            self.stack.setCurrentIndex(0)
            self.parent.title_bar.set_page(tr("dashboard"))
        elif page == "settings":
            self._set_active(self.settings_btn)
            self.stack.setCurrentIndex(1)
            self.parent.title_bar.set_page(tr("settings"))

    def _set_active(self, button):
        if self._active_button:
            self._active_button.setProperty("active", False)
            self._set_button_icon(self._active_button)
            self._refresh_button(self._active_button)
        button.setProperty("active", True)
        self._set_button_icon(button)
        self._refresh_button(button)
        self._active_button = button

    @staticmethod
    def _refresh_button(button):
        button.style().unpolish(button)
        button.style().polish(button)
        button.update()

    def change_region(self):
        dialog = RegionDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.selected_region:
            select_region(dialog.selected_region)
            self.region_btn.setText(dialog.selected_region)
            self.parent.set_region(dialog.selected_region)
            self.parent.console_panel.status_bar.set_message(f"{tr('region_switched')}: {dialog.selected_region}", "success")

    def _toggle_bot(self):
        self.parent.console_panel.toggle_start_stop()

    def sync_run_button(self):
        running = self.parent.is_running
        self.run_btn.setText(tr("stop_bot" if running else "start_bot"))
        self.run_btn.setProperty("icon_name", "stop" if running else "play")
        self.run_btn.setProperty("active", running)
        self._set_button_icon(self.run_btn)
        self._refresh_button(self.run_btn)

    @staticmethod
    def _set_button_icon(button):
        name = button.property("icon_name") or "dashboard"
        active = button.property("active") is True
        theme = THEMES[current_theme_name(get_setting("theme", "ocean"))]
        button.setIcon(icon(name, theme.cyan if active else theme.muted, 20))

    def apply_update_info(self, remote_version, mandatory=False):
        if not remote_version:
            return
        self.latest_version = remote_version
        self.update_available = parse_version(self.latest_version) > parse_version(self.current_version)
        self.update_title.setText(tr("update_available") if self.update_available else tr("up_to_date"))
        self.update_title.setProperty("available", self.update_available)
        self.update_version.setText(f"{tr('version')} {self.current_version} → {self.latest_version}")
        self._refresh_button(self.update_title)

    def refresh_text(self):
        self.navigation_label.setText(tr("navigation").upper())
        self.controls_label.setText(tr("controls").upper())
        self.dashboard_btn.setText(tr("dashboard"))
        self.region_btn.setText(self._get_region())
        self.settings_btn.setText(tr("settings"))
        self.exit_btn.setText(tr("exit"))
        for button in (self.dashboard_btn, self.region_btn, self.settings_btn, self.exit_btn):
            self._set_button_icon(button)
            self._refresh_button(button)
        self.sync_run_button()
        self.update_title.setText(tr("update_available") if self.update_available else tr("up_to_date"))
        self.update_title.setProperty("available", self.update_available)
        self.update_version.setText(f"{tr('version')} {self.current_version} → {self.latest_version}")
        self._refresh_button(self.update_title)
        self.user_card.refresh()
