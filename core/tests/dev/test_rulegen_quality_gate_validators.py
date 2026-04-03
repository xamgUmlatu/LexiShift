from __future__ import annotations

from pathlib import Path
import sys
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from rulegen_quality_gate_validators import (  # noqa: E402
    validate_benchmark_pairs,
    validate_delta_budgets,
    validate_quality_floors,
)


class TestRulegenQualityGateValidators(unittest.TestCase):
    def test_validate_benchmark_pairs_pair_scope_requires_only_scoped_pair(self) -> None:
        findings = []
        validate_benchmark_pairs(
            benchmark_payload={"pairs": {"en-de": {}}},
            policy_payload={
                "required_benchmark_pairs": ["en-es"],
                "recommended_benchmark_pairs": ["en-ja", "en-de", "es-en"],
            },
            findings=findings,
            pair_scope="en-de",
        )

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].code, "BENCHMARK_SCOPE_PAIR_PRESENT")

    def test_validate_quality_floors_pair_scope_skips_other_pair_missing_warnings(self) -> None:
        findings = []
        validate_quality_floors(
            benchmark_payload={
                "pairs": {
                    "en-de": {
                        "best_run": {
                            "summary": {
                                "top1_accuracy": 0.75,
                                "top3_recall": 1.0,
                                "forbidden_top1_rate": 0.0,
                                "forbidden_any_rate": 0.0,
                                "avg_rules_per_target": 2.38,
                            }
                        }
                    }
                }
            },
            policy_payload={
                "benchmark_quality_floors": {
                    "en-es": {
                        "min_top1_accuracy": 0.95,
                        "min_top3_recall": 0.95,
                    },
                    "en-de": {
                        "min_top1_accuracy": 0.85,
                        "min_top3_recall": 0.90,
                        "max_forbidden_top1_rate": 0.15,
                        "max_forbidden_any_rate": 0.25,
                        "max_avg_rules_per_target": 4.0,
                    },
                }
            },
            findings=findings,
            pair_scope="en-de",
        )

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].code, "QUALITY_FLOOR_BREACH")
        self.assertIn("top1_accuracy=0.7500", findings[0].details or "")

    def test_validate_delta_budgets_pair_scope_uses_scoped_baseline_only(self) -> None:
        findings = []
        validate_delta_budgets(
            benchmark_payload={
                "pairs": {
                    "en-de": {
                        "best_run": {
                            "summary": {
                                "top1_accuracy": 0.75,
                                "top3_recall": 1.0,
                                "forbidden_top1_rate": 0.0,
                                "forbidden_any_rate": 0.0,
                                "avg_rules_per_target": 2.38,
                            }
                        }
                    }
                }
            },
            baseline_payload={
                "benchmark_best_by_pair": {
                    "en-es": {
                        "top1_accuracy": 1.0,
                        "top3_recall": 1.0,
                        "forbidden_top1_rate": 0.0,
                        "forbidden_any_rate": 0.0,
                        "avg_rules_per_target": 1.0,
                    }
                }
            },
            policy_payload={
                "delta_budgets": {
                    "max_top1_accuracy_drop": 0.0,
                    "max_top3_recall_drop": 0.0,
                    "max_forbidden_top1_rate_increase": 0.0,
                    "max_forbidden_any_rate_increase": 0.0,
                    "max_avg_rules_per_target_increase": 0.5,
                }
            },
            findings=findings,
            pair_scope="en-de",
        )

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].code, "DELTA_SCOPE_BASELINE_MISSING")
