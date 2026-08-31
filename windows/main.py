import sys
from PyQt6.QtWidgets import QApplication
from windows.app import MissionChiefBotApp
from ui.theme import current_theme_name, stylesheet
from utils.settings_store import get as get_setting

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(stylesheet(current_theme_name(get_setting("theme", "ocean"))))

    window = MissionChiefBotApp()
    window.show()

    sys.exit(app.exec())
