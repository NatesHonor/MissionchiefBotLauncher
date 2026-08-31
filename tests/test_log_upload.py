import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from utils.log_upload import sanitize_log, upload_latest_log


class FakeResponse:
    headers = {}

    def raise_for_status(self):
        return None

    def json(self):
        return {"url": "https://logs.example.test/share/abc"}


class LogUploadTests(unittest.TestCase):
    def test_sanitize_log_redacts_secret_shaped_values(self):
        result = sanitize_log("password = hidden\ntoken: abc123\nstatus: ready")
        self.assertIn("password = [REDACTED]", result)
        self.assertIn("token: [REDACTED]", result)
        self.assertIn("status: ready", result)

    def test_upload_requires_an_explicit_endpoint(self):
        with patch("utils.log_upload._configured_endpoint", return_value=""):
            with self.assertRaisesRegex(RuntimeError, "No log upload endpoint"):
                upload_latest_log()

    def test_upload_returns_the_service_share_url(self):
        with tempfile.TemporaryDirectory() as directory:
            log_path = Path(directory) / "MissionchiefBot_1.log"
            log_path.write_text("status: ready", encoding="utf-8")
            with patch("utils.log_upload.latest_log_path", return_value=log_path), patch(
                "utils.log_upload.requests.post", return_value=FakeResponse()
            ) as post:
                result = upload_latest_log("https://logs.example.test/upload")

        self.assertEqual(result, "https://logs.example.test/share/abc")
        self.assertEqual(post.call_args.kwargs["timeout"], 30)
        uploaded = post.call_args.kwargs["files"]["file"][1].decode("utf-8")
        self.assertEqual(uploaded, "status: ready")


if __name__ == "__main__":
    unittest.main()
