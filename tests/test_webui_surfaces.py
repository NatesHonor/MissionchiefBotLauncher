import unittest

from ui.console_panel import ConsolePanel
from windows.app import MissionChiefBotApp
from windows.settings import ProfileHandler
from windows.sidebar import Sidebar


class WebUiSurfaceTests(unittest.TestCase):
    def test_dashboard_contains_the_core_launcher_surfaces(self):
        self.assertTrue(hasattr(MissionChiefBotApp, "_build_dashboard"))
        self.assertTrue(hasattr(MissionChiefBotApp, "set_running"))
        self.assertTrue(hasattr(MissionChiefBotApp, "apply_preferences"))
        self.assertTrue(hasattr(ConsolePanel, "toggle_start_stop"))
        self.assertTrue(hasattr(ConsolePanel, "_share_log"))

    def test_settings_and_navigation_surfaces_are_available(self):
        self.assertTrue(hasattr(ProfileHandler, "save_profile"))
        self.assertTrue(hasattr(ProfileHandler, "save_config"))
        self.assertTrue(hasattr(Sidebar, "change_region"))
        self.assertTrue(hasattr(Sidebar, "sync_run_button"))


if __name__ == "__main__":
    unittest.main()
