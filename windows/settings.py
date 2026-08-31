from pathlib import Path

from PyQt6.QtCore import QSignalBlocker, Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QFileDialog, QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox, QScrollArea, QTextEdit, QVBoxLayout, QWidget

from handlers.logging import log_exception
from utils.integrity import run_integrity_check
from utils.localization import LANGUAGES, language_setting, set_language, tr
from utils.paths import BOT_FOLDER
from utils.profile import avatar_path, clear_avatar, load_profile, set_avatar, update_profile
from utils.settings_store import get as get_setting, set_values, write_text_atomic
from ui.icons import pixmap
from ui.theme import THEMES, current_theme_name, theme_label, theme_names


class ProfileHandler(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.config_path = BOT_FOLDER / "config.ini"
        self.setObjectName("SettingsScroll")
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        content = QWidget()
        content.setObjectName("SettingsPage")
        outer = QVBoxLayout(content)
        outer.setContentsMargins(26, 24, 26, 24)
        outer.setSpacing(16)

        header = QVBoxLayout()
        self.page_title = QLabel(tr("settings"))
        self.page_title.setObjectName("PageTitle")
        self.page_copy = QLabel(tr("settings_copy"))
        self.page_copy.setObjectName("Hint")
        header.addWidget(self.page_title)
        header.addWidget(self.page_copy)
        outer.addLayout(header)

        profile_card = QFrame()
        profile_card.setObjectName("ProfileCard")
        profile_layout = QVBoxLayout(profile_card)
        profile_layout.setContentsMargins(18, 16, 18, 18)
        profile_heading = QLabel(tr("profile"))
        profile_heading.setObjectName("CardTitle")
        profile_layout.addWidget(profile_heading)
        self.profile_hint = QLabel(tr("profile_hint"))
        self.profile_hint.setObjectName("Hint")
        profile_layout.addWidget(self.profile_hint)

        profile_grid = QGridLayout()
        profile_grid.setHorizontalSpacing(14)
        profile_grid.setVerticalSpacing(9)
        self.avatar_label = QLabel()
        self.avatar_label.setObjectName("SettingsAvatar")
        self.avatar_label.setFixedSize(72, 72)
        self.avatar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        profile_grid.addWidget(self.avatar_label, 0, 0, 3, 1)
        self.name_label = QLabel(tr("display_name"))
        self.name_edit = QLineEdit()
        self.name_edit.setMaxLength(64)
        self.role_label = QLabel(tr("role"))
        self.role_edit = QLineEdit()
        self.role_edit.setMaxLength(64)
        profile_grid.addWidget(self.name_label, 0, 1)
        profile_grid.addWidget(self.name_edit, 0, 2)
        profile_grid.addWidget(self.role_label, 1, 1)
        profile_grid.addWidget(self.role_edit, 1, 2)
        avatar_buttons = QHBoxLayout()
        self.avatar_btn = QPushButton(tr("choose_avatar"))
        self.avatar_btn.setObjectName("SecondaryButton")
        self.avatar_btn.clicked.connect(self.choose_avatar)
        self.remove_avatar_btn = QPushButton(tr("remove_avatar"))
        self.remove_avatar_btn.setObjectName("SecondaryButton")
        self.remove_avatar_btn.clicked.connect(self.remove_avatar)
        avatar_buttons.addWidget(self.avatar_btn)
        avatar_buttons.addWidget(self.remove_avatar_btn)
        profile_grid.addLayout(avatar_buttons, 2, 1, 1, 2)
        profile_layout.addLayout(profile_grid)
        self.save_profile_btn = QPushButton(tr("save_profile"))
        self.save_profile_btn.setObjectName("PrimaryButton")
        self.save_profile_btn.clicked.connect(self.save_profile)
        profile_layout.addWidget(self.save_profile_btn, alignment=Qt.AlignmentFlag.AlignRight)
        outer.addWidget(profile_card)

        appearance_card = QFrame()
        appearance_card.setObjectName("SettingsCard")
        appearance_layout = QGridLayout(appearance_card)
        appearance_layout.setContentsMargins(18, 16, 18, 18)
        self.appearance_title = QLabel(tr("appearance"))
        self.appearance_title.setObjectName("CardTitle")
        appearance_layout.addWidget(self.appearance_title, 0, 0, 1, 2)
        self.theme_label = QLabel(tr("theme"))
        self.theme_combo = QComboBox()
        for name in theme_names():
            self.theme_combo.addItem(theme_label(name), name)
        self.language_label = QLabel(tr("language"))
        self.language_combo = QComboBox()
        for code, label in LANGUAGES.items():
            self.language_combo.addItem(label, code)
        self.theme_combo.currentIndexChanged.connect(self.preview_theme)
        self.language_combo.currentIndexChanged.connect(self.preview_language)
        appearance_layout.addWidget(self.theme_label, 1, 0)
        appearance_layout.addWidget(self.theme_combo, 1, 1)
        appearance_layout.addWidget(self.language_label, 2, 0)
        appearance_layout.addWidget(self.language_combo, 2, 1)
        outer.addWidget(appearance_card)

        config_card = QFrame()
        config_card.setObjectName("SettingsCard")
        config_layout = QVBoxLayout(config_card)
        config_layout.setContentsMargins(18, 16, 18, 18)
        self.config_title = QLabel(tr("bot_configuration"))
        self.config_title.setObjectName("CardTitle")
        self.config_hint = QLabel(tr("edit_config"))
        self.config_hint.setObjectName("Hint")
        config_layout.addWidget(self.config_title)
        config_layout.addWidget(self.config_hint)
        self.config_editor = QTextEdit()
        self.config_editor.setMinimumHeight(180)
        config_layout.addWidget(self.config_editor, 1)
        config_buttons = QHBoxLayout()
        self.repair_btn = QPushButton(tr("repair"))
        self.repair_btn.setObjectName("SecondaryButton")
        self.repair_btn.clicked.connect(self._run_repair)
        self.save_config_btn = QPushButton(tr("save_config"))
        self.save_config_btn.setObjectName("PrimaryButton")
        self.save_config_btn.clicked.connect(self.save_config)
        config_buttons.addWidget(self.repair_btn)
        config_buttons.addStretch()
        config_buttons.addWidget(self.save_config_btn)
        config_layout.addLayout(config_buttons)
        outer.addWidget(config_card, 1)
        self.setWidget(content)

    def refresh(self):
        profile = load_profile()
        self.name_edit.setText(profile["display_name"])
        self.role_edit.setText(profile["role"])
        self._refresh_avatar(profile)
        self._select_data(self.theme_combo, get_setting("theme", "ocean"))
        self._select_data(self.language_combo, language_setting())
        self._load_config()

    @staticmethod
    def _select_data(combo, value):
        index = combo.findData(value)
        if index >= 0:
            blocker = QSignalBlocker(combo)
            combo.setCurrentIndex(index)
            del blocker

    def _refresh_avatar(self, profile=None):
        path = avatar_path(profile or load_profile())
        if path:
            avatar_pixmap = QPixmap(str(path)).scaled(72, 72, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
            self.avatar_label.setPixmap(avatar_pixmap)
            self.avatar_label.setText("")
        else:
            theme = THEMES[current_theme_name(get_setting("theme", "ocean"))]
            self.avatar_label.setPixmap(pixmap("user", 42, theme.cyan))
            self.avatar_label.setText("")

    def _load_config(self):
        if self.config_path.is_file():
            self.config_editor.setPlainText(self.config_path.read_text(encoding="utf-8"))
            self.config_editor.setReadOnly(False)
        else:
            self.config_editor.setPlainText("# Config.ini is not available until setup is complete.")
            self.config_editor.setReadOnly(True)

    def choose_avatar(self):
        filename, _ = QFileDialog.getOpenFileName(self, tr("choose_avatar"), "", "Images (*.png *.jpg *.jpeg *.webp *.bmp *.gif)")
        if not filename:
            return
        try:
            profile = set_avatar(filename)
            self._refresh_avatar(profile)
            self.parent.sidebar.user_card.refresh()
        except Exception as exc:
            self.parent.console_panel.status_bar.set_message(str(exc), "error")

    def remove_avatar(self):
        profile = clear_avatar()
        self._refresh_avatar(profile)
        self.parent.sidebar.user_card.refresh()

    def save_profile(self):
        profile = update_profile(self.name_edit.text(), self.role_edit.text())
        self._refresh_avatar(profile)
        self.parent.sidebar.user_card.refresh()
        self.parent.console_panel.status_bar.set_message(tr("profile_saved"), "success")

    def preview_theme(self):
        if self.parent and self.theme_combo.currentData():
            self.parent.apply_preferences(self.theme_combo.currentData(), None, persist=True)

    def preview_language(self):
        if self.parent and self.language_combo.currentData():
            self.parent.apply_preferences(None, self.language_combo.currentData(), persist=True)

    def refresh_text(self):
        self.page_title.setText(tr("settings"))
        self.page_copy.setText(tr("settings_copy"))
        self.profile_hint.setText(tr("profile_hint"))
        self.name_label.setText(tr("display_name"))
        self.role_label.setText(tr("role"))
        self.avatar_btn.setText(tr("choose_avatar"))
        self.remove_avatar_btn.setText(tr("remove_avatar"))
        self.save_profile_btn.setText(tr("save_profile"))
        self.appearance_title.setText(tr("appearance"))
        self.theme_label.setText(tr("theme"))
        self.language_label.setText(tr("language"))
        self.config_title.setText(tr("bot_configuration"))
        self.config_hint.setText(tr("edit_config"))
        self.repair_btn.setText(tr("repair"))
        self.save_config_btn.setText(tr("save_config"))

    def save_config(self):
        if not self.config_path.is_file():
            self.parent.console_panel.status_bar.set_message(tr("config_missing"), "error")
            return
        try:
            write_text_atomic(self.config_editor.toPlainText(), self.config_path)
            self.parent.console_panel.status_bar.set_message(tr("config_saved"), "success")
        except Exception as exc:
            self.parent.console_panel.status_bar.set_message(f"Save failed: {exc}", "error")

    def _run_repair(self):
        try:
            run_integrity_check()
            self._load_config()
            self.parent.console_panel.status_bar.set_message(tr("repair_complete") if self.config_path.exists() else tr("repair_missing"), "success" if self.config_path.exists() else "error")
        except Exception as exc:
            log_exception("Settings repair failed")
            self.parent.console_panel.status_bar.set_message(f"Repair failed: {exc}", "error")
