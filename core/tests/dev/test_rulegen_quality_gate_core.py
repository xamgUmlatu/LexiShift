from __future__ import annotations

from pathlib import Path
import sys
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from rulegen_quality_gate_core import dataset_from_payload  # noqa: E402


class TestRulegenQualityGateCore(unittest.TestCase):
    def test_dataset_from_payload_falls_back_to_repo_dataset_directory(self) -> None:
        benchmark_payload = {
            "dataset_path": "/Users/takeyayuki/Documents/projects/LexiShift/docs/test_inputs/rulegen_benchmark_cases.json"
        }

        resolved = dataset_from_payload(
            benchmark_payload,
            None,
            project_root=REPO_ROOT,
        )

        self.assertEqual(
            resolved,
            (REPO_ROOT / "docs" / "test_inputs" / "rulegen_benchmark_cases").resolve(),
        )


if __name__ == "__main__":
    unittest.main()
