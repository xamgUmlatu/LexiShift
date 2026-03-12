from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "build"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from validate_app_bundle import _validate_dist  # noqa: E402


class TestValidateAppBundle(unittest.TestCase):
    def test_validate_windows_dist_passes_for_main_and_helper_layout(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            dist = Path(tmpdir) / "dist"
            main_root = dist / "LexiShift"
            helper_root = dist / "LexiShiftHelper"
            host_root = dist / "LexiShiftNativeHost"
            (main_root / "resources" / "helper" / "lexishift_core").mkdir(
                parents=True, exist_ok=True
            )
            (main_root / "resources" / "i18n").mkdir(parents=True, exist_ok=True)
            (main_root / "resources" / "themes").mkdir(parents=True, exist_ok=True)
            (main_root / "resources" / "sample_images").mkdir(parents=True, exist_ok=True)
            (helper_root / "resources" / "i18n").mkdir(parents=True, exist_ok=True)
            host_root.mkdir(parents=True, exist_ok=True)
            (main_root / "LexiShift.exe").write_bytes(b"main")
            (helper_root / "LexiShiftHelper.exe").write_bytes(b"helper")
            (host_root / "lexishift_native_host.exe").write_bytes(b"host")
            (main_root / "resources" / "helper" / "lexishift_native_host.py").write_text(
                "host\n",
                encoding="utf-8",
            )
            (main_root / "resources" / "helper" / "helper_daemon.py").write_text(
                "daemon\n",
                encoding="utf-8",
            )
            (helper_root / "resources" / "ttbn.ico").write_bytes(b"ico")

            result = _validate_dist(dist)

        self.assertEqual(result, 0)


if __name__ == "__main__":
    unittest.main()
