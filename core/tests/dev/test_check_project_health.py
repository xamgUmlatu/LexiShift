from __future__ import annotations

from pathlib import Path
import json
import subprocess
import tempfile
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_PATH = REPO_ROOT / "scripts" / "dev" / "check_project_health.js"


class TestCheckProjectHealth(unittest.TestCase):
    def _run_check(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["node", str(SCRIPT_PATH), *args],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

    def _write_current_baseline(self, baseline_path: Path) -> dict[str, object]:
        result = self._run_check(
            "--advisory",
            "--warning-limit",
            "0",
            "--write-baseline",
            str(baseline_path),
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        return json.loads(baseline_path.read_text(encoding="utf-8"))

    @staticmethod
    def _pick_warning_entry(baseline: dict[str, object]) -> tuple[str, dict[str, object]]:
        files = dict(baseline["files"])
        for file_path, record in files.items():
            if record.get("warning_metrics"):
                return str(file_path), dict(record)
        raise AssertionError("Expected at least one warning record in baseline snapshot")

    def test_fail_on_new_warnings_detects_missing_baseline_warning_metric(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            baseline_path = Path(tmpdir) / "baseline.json"
            baseline = self._write_current_baseline(baseline_path)
            file_path, record = self._pick_warning_entry(baseline)
            record["warning_metrics"] = []
            baseline["files"][file_path] = record
            baseline_path.write_text(json.dumps(baseline, indent=2) + "\n", encoding="utf-8")

            result = self._run_check(
                "--baseline-json",
                str(baseline_path),
                "--fail-on-new-warnings",
                "--warning-limit",
                "0",
            )

        self.assertNotEqual(result.returncode, 0)
        combined_output = f"{result.stdout}\n{result.stderr}"
        self.assertIn("New warnings vs baseline", combined_output)

    def test_fail_on_warning_regressions_detects_worsened_warning_metric(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            baseline_path = Path(tmpdir) / "baseline.json"
            baseline = self._write_current_baseline(baseline_path)
            file_path, record = self._pick_warning_entry(baseline)
            metric = str(record["warning_metrics"][0])
            metrics = dict(record["metrics"])
            metrics[metric] = max(0, int(metrics[metric]) - 1)
            record["metrics"] = metrics
            baseline["files"][file_path] = record
            baseline_path.write_text(json.dumps(baseline, indent=2) + "\n", encoding="utf-8")

            result = self._run_check(
                "--baseline-json",
                str(baseline_path),
                "--fail-on-warning-regressions",
                "--warning-limit",
                "0",
            )

        self.assertNotEqual(result.returncode, 0)
        combined_output = f"{result.stdout}\n{result.stderr}"
        self.assertIn("Warning regressions vs baseline", combined_output)


if __name__ == "__main__":
    unittest.main()
