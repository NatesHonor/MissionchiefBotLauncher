from PyQt6.QtWidgets import QApplication
from windows.main import MissionChiefBotApp
import sys, os, shutil, configparser

def ensure_launcher_settings():
    exe_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    bundled_ini = os.path.join(exe_dir, "launcher_settings.ini")
    target_ini = os.path.join(os.getcwd(), "launcher_settings.ini")

    bundled = configparser.ConfigParser()
    bundled.read(bundled_ini)

    if not os.path.exists(target_ini):
        shutil.copy(bundled_ini, target_ini)
        return

    existing = configparser.ConfigParser()
    existing.read(target_ini)

    def parse_version(v):
        return tuple(int(x) for x in v.split(".") if x.isdigit())

    bundled_version = bundled.get("Launcher", "version", fallback="0.0.0").strip()
    existing_version = existing.get("Launcher", "version", fallback="0.0.0").strip()

    if parse_version(bundled_version) <= parse_version(existing_version):
        return

    merged = configparser.ConfigParser()

    for section in bundled.sections():
        merged.add_section(section)
        for key, value in bundled.items(section):
            merged.set(section, key, value)

    for section in existing.sections():
        if not merged.has_section(section):
            merged.add_section(section)
        for key, value in existing.items(section):
            if not merged.has_option(section, key) or merged.get(section, key).strip() == "":
                merged.set(section, key, value)

    merged.set("Launcher", "version", bundled_version)

    with open(target_ini, "w") as f:
        merged.write(f)

if __name__ == "__main__":
    ensure_launcher_settings()
    app = QApplication(sys.argv)
    app.setStyleSheet("QWidget { background-color: #101010; }")
    window = MissionChiefBotApp()
    window.show()
    sys.exit(app.exec())