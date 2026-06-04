from __future__ import annotations

from pathlib import Path
import sys
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from rulegen_benchmark_reporting import _resolve_path_from_report_payload  # noqa: E402


class TestRulegenBenchmarkReporting(unittest.TestCase):
    def test_resolve_path_from_report_payload_falls_back_to_repo_dataset_directory(self) -> None:
        resolved = _resolve_path_from_report_payload(
            "/Users/takeyayuki/Documents/projects/LexiShift/docs/test_inputs/rulegen_benchmark_cases.json",
            project_root=REPO_ROOT,
        )

        self.assertEqual(
            resolved,
            (REPO_ROOT / "docs" / "test_inputs" / "rulegen_benchmark_cases").resolve(),
        )


if __name__ == "__main__":
    unittest.main()
