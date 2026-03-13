from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from rulegen_reverse_run_matrix import (  # noqa: E402
    RunMatrixRow,
    render_markdown,
)


def _write_json(path: Path, payload: dict) -> None:
    import json

    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


class TestRulegenReverseRunMatrix(unittest.TestCase):
    def test_render_markdown_includes_selected_rows_and_failures(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            baseline_benchmark = root / "baseline.json"
            baseline_triage = root / "baseline_triage.json"
            reverse_benchmark = root / "reverse.json"
            reverse_triage = root / "reverse_triage.json"

            _write_json(
                baseline_benchmark,
                {
                    "pairs": {
                        "en-es": {
                            "best_run": {
                                "config": {
                                    "reverse_check_enabled": False,
                                    "reverse_check_match_bonus": 0.2,
                                    "reverse_check_near_bonus": 0.1,
                                    "reverse_check_near_rank_max": 2,
                                    "reverse_check_far_hit_penalty": 0.0,
                                    "reverse_check_miss_penalty": 0.2,
                                    "max_rules_per_target": None,
                                },
                                "summary": {
                                    "top1_accuracy": 0.8,
                                    "top3_recall": 0.9,
                                    "forbidden_top1_rate": 0.2,
                                    "forbidden_any_rate": 0.1,
                                    "avg_rules_per_target": 1.5,
                                },
                            },
                            "runs": [],
                        }
                    }
                },
            )
            _write_json(
                baseline_triage,
                {
                    "items": [
                        {
                            "case_id": "en-es:madre",
                            "target": "madre",
                            "top1_source": "bed",
                        }
                    ]
                },
            )
            _write_json(
                reverse_benchmark,
                {
                    "pairs": {
                        "en-es": {
                            "best_run": {
                                "config": {
                                    "reverse_check_enabled": True,
                                    "reverse_check_match_bonus": 0.6,
                                    "reverse_check_near_bonus": 0.1,
                                    "reverse_check_near_rank_max": 2,
                                    "reverse_check_far_hit_penalty": 0.05,
                                    "reverse_check_miss_penalty": 0.8,
                                    "max_rules_per_target": 1,
                                },
                                "summary": {
                                    "top1_accuracy": 0.95,
                                    "top3_recall": 0.95,
                                    "forbidden_top1_rate": 0.04,
                                    "forbidden_any_rate": 0.04,
                                    "avg_rules_per_target": 1.0,
                                },
                            },
                            "runs": [
                                {
                                    "config": {
                                        "reverse_check_enabled": True,
                                        "reverse_check_match_bonus": 0.6,
                                        "reverse_check_near_bonus": 0.1,
                                        "reverse_check_near_rank_max": 2,
                                        "reverse_check_far_hit_penalty": 0.05,
                                        "reverse_check_miss_penalty": 0.8,
                                        "max_rules_per_target": 1,
                                    },
                                    "summary": {
                                        "objective_score": 139.0,
                                        "top1_accuracy": 0.95,
                                        "top3_recall": 0.95,
                                        "forbidden_top1_rate": 0.04,
                                        "forbidden_any_rate": 0.04,
                                        "avg_rules_per_target": 1.0,
                                    },
                                },
                                {
                                    "config": {
                                        "reverse_check_enabled": True,
                                        "reverse_check_match_bonus": 0.6,
                                        "reverse_check_near_bonus": 0.1,
                                        "reverse_check_near_rank_max": 2,
                                        "reverse_check_far_hit_penalty": 0.05,
                                        "reverse_check_miss_penalty": 0.8,
                                        "max_rules_per_target": None,
                                    },
                                    "summary": {
                                        "objective_score": 138.25,
                                        "top1_accuracy": 0.95,
                                        "top3_recall": 1.0,
                                        "forbidden_top1_rate": 0.04,
                                        "forbidden_any_rate": 0.04,
                                        "avg_rules_per_target": 1.54,
                                    },
                                },
                            ],
                        }
                    }
                },
            )
            _write_json(
                reverse_triage,
                {
                    "items": [
                        {
                            "case_id": "en-es:cuadro",
                            "target": "cuadro",
                            "top1_source": "bed",
                        }
                    ]
                },
            )

            markdown = render_markdown(
                rows=[
                    RunMatrixRow(
                        label="Canonical Latest",
                        lane="baseline",
                        source="canonical latest",
                        benchmark_json=baseline_benchmark,
                        triage_json=baseline_triage,
                        selector="best",
                    ),
                    RunMatrixRow(
                        label="Reverse Latest",
                        lane="named reverse lane",
                        source="reverse latest",
                        benchmark_json=reverse_benchmark,
                        triage_json=reverse_triage,
                        selector="best",
                    ),
                    RunMatrixRow(
                        label="Reverse Latest (No Cap)",
                        lane="named reverse lane",
                        source="reverse latest",
                        benchmark_json=reverse_benchmark,
                        triage_json=reverse_triage,
                        selector="best_rev_on_no_cap",
                    ),
                ],
                pair="en-es",
            )

        self.assertIn("Reverse Latest (No Cap)", markdown)
        self.assertIn("95.00%", markdown)
        self.assertIn("cuadro:bed", markdown)
        self.assertIn("| 1 |", markdown)
        self.assertIn("| none |", markdown)


if __name__ == "__main__":
    unittest.main()
