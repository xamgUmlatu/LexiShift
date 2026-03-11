from __future__ import annotations

from pathlib import Path
import sys
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from rulegen_benchmark_summary import render_summary  # noqa: E402


class TestRulegenBenchmarkSummary(unittest.TestCase):
    def test_render_summary_reports_best_runs(self) -> None:
        markdown = render_summary(
            {
                "generated_at": "2026-03-12T00:00:00+00:00",
                "dataset_path": "cases.json",
                "profile_id": "default",
                "sweep": {"configuration_count": 6, "pair_filter": ["en-es", "en-ja"]},
                "pairs": {
                    "en-es": {
                        "case_count": 16,
                        "run_count": 6,
                        "best_run": {
                            "config_label": "rev=on pos=on",
                            "summary": {
                                "objective_score": 85.3,
                                "top1_accuracy": 0.9375,
                                "top3_recall": 1.0,
                                "forbidden_top1_rate": 0.0625,
                                "forbidden_any_rate": 0.0625,
                                "avg_rules_per_target": 1.0,
                            },
                        },
                    }
                },
            }
        )
        self.assertIn("# Rulegen Benchmark", markdown)
        self.assertIn("- Configurations per pair: 6", markdown)
        self.assertIn(
            "| en-es | 16 | 6 | 85.300 | 93.75% | 100.00% | 6.25% | 6.25% | 1.00 | `rev=on pos=on` |",
            markdown,
        )


if __name__ == "__main__":
    unittest.main()
