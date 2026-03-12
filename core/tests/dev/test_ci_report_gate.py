from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "scripts" / "dev" / "ci_report_gate.py"


class TestCiReportGate(unittest.TestCase):
    def _write_json(self, path: Path, payload: dict[str, object]) -> None:
        path.write_text(json.dumps(payload), encoding="utf-8")

    def test_passes_when_all_reports_are_green(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            check_json = root / "check.json"
            build_json = root / "build.json"
            parity_json = root / "parity.json"
            gate_json = root / "gate.json"
            self._write_json(check_json, {"overall_exit_code": 0})
            self._write_json(build_json, {"overall_exit_code": 0})
            self._write_json(parity_json, {"status": "PASS"})
            self._write_json(gate_json, {"summary": {"status": "PASS", "should_fail": False}})

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--check-json",
                    str(check_json),
                    "--build-json",
                    str(build_json),
                    "--windows-parity-json",
                    str(parity_json),
                    "--rulegen-gate-json",
                    str(gate_json),
                ],
                check=False,
                capture_output=True,
                text=True,
            )

        self.assertEqual(result.returncode, 0)
        self.assertIn("[PASS] check_report overall_exit_code=0", result.stdout)
        self.assertIn("[PASS] build_report overall_exit_code=0", result.stdout)
        self.assertIn("[PASS] windows_parity status=PASS", result.stdout)
        self.assertIn("[PASS] rulegen_quality status=PASS should_fail=False", result.stdout)

    def test_fails_when_any_report_is_red(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            check_json = root / "check.json"
            build_json = root / "build.json"
            self._write_json(check_json, {"overall_exit_code": 1})
            self._write_json(build_json, {"overall_exit_code": 0})

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--check-json",
                    str(check_json),
                    "--build-json",
                    str(build_json),
                ],
                check=False,
                capture_output=True,
                text=True,
            )

        self.assertEqual(result.returncode, 1)
        self.assertIn("[FAIL] check_report overall_exit_code=1", result.stdout)
        self.assertIn("[PASS] build_report overall_exit_code=0", result.stdout)


if __name__ == "__main__":
    unittest.main()
