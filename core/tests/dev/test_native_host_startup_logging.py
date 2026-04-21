from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[3]
HOST_SCRIPT = PROJECT_ROOT / "scripts" / "helper" / "lexishift_native_host.py"


class TestNativeHostStartupLogging(unittest.TestCase):
    def test_startup_import_failures_write_deterministic_log(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            isolated_host = root / "scripts" / "helper" / "lexishift_native_host.py"
            isolated_host.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(HOST_SCRIPT, isolated_host)

            data_root = root / "data"
            env = {
                "HOME": str(root),
                "LEXISHIFT_DATA_DIR": str(data_root),
                "PATH": os.environ.get("PATH", ""),
                "PYTHONPATH": "",
            }
            result = subprocess.run(
                [sys.executable, str(isolated_host)],
                check=False,
                capture_output=True,
                text=True,
                cwd=root,
                env=env,
            )

            self.assertNotEqual(result.returncode, 0)
            log_path = data_root / "logs" / "native_host.log"
            self.assertTrue(log_path.exists())
            log_text = log_path.read_text(encoding="utf-8")
            self.assertIn("stage=startup_import", log_text)
            self.assertIn("ModuleNotFoundError", log_text)
            self.assertIn("lexishift_core", log_text)


if __name__ == "__main__":
    unittest.main()
