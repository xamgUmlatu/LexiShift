from __future__ import annotations

import json
from pathlib import Path
import re
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]


def _match(path: Path, pattern: str) -> str:
    text = path.read_text(encoding="utf-8")
    match = re.search(pattern, text, flags=re.MULTILINE)
    if match is None:
        raise AssertionError(f"Version pattern not found in {path}")
    return match.group(1)


class TestReleaseVersionAlignment(unittest.TestCase):
    def test_primary_beta_surfaces_share_one_version(self) -> None:
        manifest = json.loads(
            (REPO_ROOT / "apps" / "chrome-extension" / "manifest.json").read_text(encoding="utf-8")
        )
        expected = str(manifest["version"])
        spec_path = REPO_ROOT / "apps" / "gui" / "packaging" / "pyinstaller.spec"
        native_host_path = REPO_ROOT / "scripts" / "helper" / "lexishift_native_host.py"
        core_status_path = REPO_ROOT / "core" / "lexishift_core" / "helper" / "status.py"
        installer_path = REPO_ROOT / "scripts" / "build" / "installer.py"
        windows_installer_path = REPO_ROOT / "apps" / "gui" / "packaging" / "installer_windows.iss"

        versions = {
            "app": _match(spec_path, r'^APP_VERSION\s*=\s*"([^"]+)"'),
            "app_build": _match(spec_path, r'^APP_BUILD\s*=\s*"([^"]+)"'),
            "native_helper": _match(native_host_path, r'HELPER_VERSION\s*=\s*1,\s*"([^"]+)"'),
            "core_helper": _match(core_status_path, r'helper_version:\s*str\s*=\s*"([^"]+)"'),
            "installer_default": _match(
                installer_path,
                r'--app-version",\s*default="([^"]+)"',
            ),
            "windows_installer": _match(
                windows_installer_path,
                r'#define AppVersion "([^"]+)"',
            ),
        }
        self.assertEqual(set(versions.values()), {expected}, versions)

        numeric = tuple(int(part) for part in expected.split(".")) + (0,)
        numeric = numeric[:4]
        file_version = _match(spec_path, r"^WIN_FILE_VERSION\s*=\s*\(([^)]+)\)")
        product_version = _match(spec_path, r"^WIN_PRODUCT_VERSION\s*=\s*\(([^)]+)\)")
        expected_tuple = ", ".join(str(part) for part in numeric)
        self.assertEqual(file_version, expected_tuple)
        self.assertEqual(product_version, expected_tuple)


if __name__ == "__main__":
    unittest.main()
