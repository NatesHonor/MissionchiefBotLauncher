import tempfile
import unittest
from pathlib import Path

from utils.install import _effective_requirements_file


class InstallTests(unittest.TestCase):
    def test_python_314_uses_compatible_playwright_constraint(self):
        with tempfile.TemporaryDirectory() as directory:
            requirements = Path(directory) / "requirements.txt"
            requirements.write_text("playwright~=1.48.0\nart~=6.3\n", encoding="utf-8")

            # Avoid invoking a real interpreter: the compatibility decision is
            # based on the target venv version and is isolated behind this helper.
            import utils.install as install
            original = install._python_version
            original_python = install._get_python_path
            try:
                install._python_version = lambda path: (3, 14)
                install._get_python_path = lambda name: Path(directory) / "python.exe"
                rewritten = _effective_requirements_file(requirements, "test")
            finally:
                install._python_version = original
                install._get_python_path = original_python

            self.assertIn("playwright>=1.62,<1.63", rewritten.read_text(encoding="utf-8"))
            self.assertIn("art~=6.3", rewritten.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
