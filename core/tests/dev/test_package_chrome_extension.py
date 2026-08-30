from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "build"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from package_chrome_extension import build_package  # noqa: E402


class TestPackageChromeExtension(unittest.TestCase):
    def _write_source(self, root: Path, *, version: str = "0.1.1") -> Path:
        source = root / "extension"
        (source / "nested").mkdir(parents=True)
        (source / "manifest.json").write_text(
            json.dumps({"manifest_version": 3, "version": version}),
            encoding="utf-8",
        )
        (source / "background.js").write_text("const ready = true;\n", encoding="utf-8")
        (source / "nested" / "asset.json").write_text("{}\n", encoding="utf-8")
        (source / "README.md").write_text("developer notes\n", encoding="utf-8")
        return source

    def test_build_package_is_minimal_and_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            source = self._write_source(root)
            first = root / "first.zip"
            second = root / "second.zip"

            first_digest, first_count = build_package(source, first, expected_version="0.1.1")
            second_digest, second_count = build_package(source, second, expected_version="0.1.1")

            self.assertEqual(first_count, 3)
            self.assertEqual(second_count, 3)
            self.assertEqual(first_digest, second_digest)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            with zipfile.ZipFile(first) as archive:
                self.assertEqual(
                    archive.namelist(),
                    ["background.js", "manifest.json", "nested/asset.json"],
                )
                self.assertNotIn("README.md", archive.namelist())
            self.assertTrue(first.with_suffix(".zip.sha256").is_file())

    def test_build_package_rejects_version_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            source = self._write_source(root, version="0.1.0")

            with self.assertRaisesRegex(ValueError, "does not match requested version"):
                build_package(source, root / "extension.zip", expected_version="0.1.1")

    def test_build_package_rejects_source_noise(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            source = self._write_source(root)
            (source / ".DS_Store").write_bytes(b"noise")

            with self.assertRaisesRegex(ValueError, "Package noise"):
                build_package(source, root / "extension.zip")


if __name__ == "__main__":
    unittest.main()
