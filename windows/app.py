import configparser

from PyQt6.QtCore import QTimer, QUrl, Qt
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import QApplication, QFrame, QHBoxLayout, QLabel, QMainWindow, QPushButton, QScrollArea, QSplitter, QStackedWidget, QVBoxLayout, QWidget
from PyQt6.QtWebEngineWidgets import QWebEngineView

from handlers.logging import log_exception
from handlers.updates import check_updates
from logic.region import ensure_region_selected
from ui.console_panel import ConsolePanel
from ui.icons import icon, icon_size
from ui.theme import current_theme_name, stylesheet
from ui.theme import THEMES
from utils import state
from utils.localization import tr
from utils.paths import LAUNCHER_CONFIG
from utils.regions import get_region_url, get_selected_region
from utils.settings_store import get as get_setting, set_values
from widgets.title_bar import TitleBar
from windows.settings import ProfileHandler
from windows.sidebar import Sidebar


class MissionChiefBotApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setObjectName("MissionHelperWindow")
        self.is_running = False
        self.update_declined_this_session = False
        self._current_page = "dashboard"
        self.setWindowTitle(tr("app_name"))
        self.setMinimumSize(980, 680)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet(stylesheet(current_theme_name(get_setting("theme", "ocean"))))
        self._set_geometry()
        self._build_ui()
        QTimer.singleShot(0, self.startup_sequence)

    def startup_sequence(self):
        check_updates(self)
        ensure_region_selected(self)
        self.set_region(get_selected_region())
        self._setup_updates()

    def _set_geometry(self):
        screen = self.screen().availableGeometry()
        width = min(max(int(screen.width() * 0.70), 980), max(screen.width() - 24, 1))
        height = min(max(int(screen.height() * 0.78), 680), max(screen.height() - 24, 1))
        self.setGeometry(
            screen.x() + (screen.width() - width) // 2,
            screen.y() + (screen.height() - height) // 2,
            width,
            height,
        )

    def _build_ui(self):
        root = QFrame()
        root.setObjectName("Root")
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        self.title_bar = TitleBar(self)
        root_layout.addWidget(self.title_bar)

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setObjectName("PageStack")
        self.dashboard_page = self._build_dashboard()
        self.profile_handler = ProfileHandler(self)
        self.stacked_widget.addWidget(self.dashboard_page)
        self.stacked_widget.addWidget(self.profile_handler)
        self.sidebar = Sidebar(self, self.stacked_widget)
        body.addWidget(self.sidebar)
        body.addWidget(self.stacked_widget, 1)
        root_layout.addLayout(body, 1)

        self.footer = QLabel(f"  {tr('app_name')}  •  {tr('profile_hint')}")
        self.footer.setObjectName("FooterLabel")
        self.footer.setFixedHeight(28)
        root_layout.addWidget(self.footer)
        self.setCentralWidget(root)

    def _build_dashboard(self):
        scroll = QScrollArea()
        scroll.setObjectName("DashboardScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        page = QWidget()
        page.setObjectName("DashboardPage")
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(24, 22, 24, 20)
        page_layout.setSpacing(14)

        hero = QFrame()
        hero.setObjectName("HeroCard")
        hero.setMinimumHeight(142)
        hero_layout = QHBoxLayout(hero)
        hero_layout.setContentsMargins(22, 18, 22, 18)
        hero_layout.setSpacing(18)
        hero_text = QVBoxLayout()
        self.hero_eyebrow = QLabel(tr("hero_eyebrow"))
        self.hero_eyebrow.setObjectName("Eyebrow")
        self.hero_title = QLabel(tr("hero_title"))
        self.hero_title.setObjectName("HeroTitle")
        self.hero_copy = QLabel(tr("hero_copy"))
        self.hero_copy.setObjectName("HeroCopy")
        self.hero_copy.setWordWrap(True)
        hero_text.addWidget(self.hero_eyebrow)
        hero_text.addWidget(self.hero_title)
        hero_text.addWidget(self.hero_copy)
        hero_layout.addLayout(hero_text, 1)
        stats = QHBoxLayout()
        stats.setSpacing(24)
        self.status_stat = self._stat_block(tr("idle"), tr("status"))
        self.region_stat = self._stat_block(get_selected_region() or tr("region"), tr("region"))
        self.version_stat = self._stat_block(self._version(), tr("version"))
        stats.addLayout(self.status_stat[0])
        stats.addLayout(self.region_stat[0])
        stats.addLayout(self.version_stat[0])
        hero_layout.addLayout(stats)
        page_layout.addWidget(hero)

        self.console_panel = ConsolePanel(self)
        self.console_panel.setMinimumHeight(360)
        page_layout.addWidget(self.console_panel)

        web_card = QFrame()
        web_card.setObjectName("WebCard")
        web_card.setMinimumHeight(640)
        web_layout = QVBoxLayout(web_card)
        web_layout.setContentsMargins(16, 14, 16, 16)
        web_layout.setSpacing(10)
        web_header = QHBoxLayout()
        self.web_title = QLabel(tr("mission_control"))
        self.web_title.setObjectName("CardTitle")
        self.web_region = QLabel(get_selected_region() or tr("region"))
        self.web_region.setObjectName("Hint")
        web_header.addWidget(self.web_title)
        web_header.addWidget(self.web_region)
        web_header.addStretch()
        self.open_site_btn = QPushButton()
        self.open_site_btn.setObjectName("IconButton")
        self.open_site_btn.setIconSize(icon_size(18))
        self._set_site_icon()
        self.open_site_btn.setToolTip(tr("open_workspace"))
        self.open_site_btn.clicked.connect(lambda: self.web_view.setUrl(QUrl(get_region_url(get_selected_region()))))
        web_header.addWidget(self.open_site_btn)
        web_layout.addLayout(web_header)
        self.web_view = QWebEngineView()
        self.web_view.setObjectName("MissionChiefView")
        self.web_view.setMinimumHeight(540)
        self.web_view.setUrl(QUrl(get_region_url(get_selected_region())))
        web_layout.addWidget(self.web_view, 1)
        page_layout.addWidget(web_card)
        page_layout.addStretch(1)
        scroll.setWidget(page)
        return scroll

    @staticmethod
    def _stat_block(value, label):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        value_label = QLabel(str(value))
        value_label.setObjectName("StatValue")
        value_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        label_label = QLabel(label)
        label_label.setObjectName("StatLabel")
        label_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(value_label)
        layout.addWidget(label_label)
        return layout, value_label, label_label

    def _version(self):
        config = configparser.ConfigParser()
        config.read(LAUNCHER_CONFIG, encoding="utf-8")
        return config.get("Launcher", "version", fallback="0.0.0")

    def set_running(self, running):
        self.is_running = bool(running)
        self.status_stat[1].setText(tr("running") if self.is_running else tr("idle"))
        self.console_panel.refresh_text()
        if hasattr(self, "sidebar"):
            self.sidebar.sync_run_button()

    def _set_site_icon(self):
        theme = THEMES[current_theme_name(get_setting("theme", "ocean"))]
        self.open_site_btn.setIcon(icon("external", theme.cyan, 20))

    def set_region(self, region_name):
        region = region_name if region_name else get_selected_region()
        self.web_view.setUrl(QUrl(get_region_url(region)))
        self.web_region.setText(region or tr("region"))
        self.region_stat[1].setText(region or tr("region"))

    def apply_preferences(self, theme_name=None, language=None, persist=True):
        if theme_name:
            theme_name = current_theme_name(theme_name)
            if persist:
                set_values({"theme": theme_name})
        if language:
            from utils.localization import set_language
            if persist:
                set_language(language)
        self.setStyleSheet(stylesheet(current_theme_name(get_setting("theme", "ocean"))))
        self.refresh_text()

    def refresh_text(self):
        self.title_bar.refresh_text()
        self.sidebar.refresh_text()
        self.console_panel.refresh_text()
        self.profile_handler.refresh_text()
        self.footer.setText(f"  {tr('app_name')}  •  {tr('profile_hint')}")
        self.hero_eyebrow.setText(tr("hero_eyebrow"))
        self.hero_title.setText(tr("hero_title"))
        self.hero_copy.setText(tr("hero_copy"))
        self.open_site_btn.setToolTip(tr("open_workspace"))
        self._set_site_icon()
        self.web_title.setText(tr("mission_control"))
        self.status_stat[2].setText(tr("status"))
        self.region_stat[2].setText(tr("region"))
        self.version_stat[2].setText(tr("version"))
        self.status_stat[1].setText(tr("running") if self.is_running else tr("idle"))

    def _setup_updates(self):
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(lambda: check_updates(self))
        self.update_timer.start(15 * 60 * 1000)

    def closeEvent(self, event: QCloseEvent):
        if state.get_active_processes():
            state.request_stop()
            state.stop_all(timeout=3)
            state.force_kill_all()
        event.accept()
