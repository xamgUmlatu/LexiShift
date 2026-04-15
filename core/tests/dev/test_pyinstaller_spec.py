from __future__ import annotations

from pathlib import Path
import re
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
SPEC_PATH = REPO_ROOT / "apps" / "gui" / "packaging" / "pyinstaller.spec"


class TestPyInstallerSpec(unittest.TestCase):
    def test_windows_native_host_excludes_optional_ml_stack(self) -> None:
        spec_text = SPEC_PATH.read_text(encoding="utf-8")

        self.assertIn("HOST_OPTIONAL_EXCLUDES = [", spec_text)
        self.assertIn('"torch"', spec_text)
        self.assertIn('"torchaudio"', spec_text)
        self.assertIn('"torchvision"', spec_text)
        self.assertIn('"tensorboard"', spec_text)
        self.assertIn('"tensorflow"', spec_text)
        self.assertRegex(
            spec_text,
            re.compile(
                r"host_a = Analysis\((?s:.*?)excludes=HOST_OPTIONAL_EXCLUDES,",
            ),
        )


if __name__ == "__main__":
    unittest.main()
