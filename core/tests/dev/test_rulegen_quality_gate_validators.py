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
    validate_dataset_contract,
    validate_delta_budgets,
    validate_pos_guardrails,
    validate_quality_floors,
    validate_saturation,
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

    def test_validate_dataset_contract_pair_scope_ignores_other_pair_minima(self) -> None:
        findings = []
        validate_dataset_contract(
            dataset_payload={
                "cases": [
                    {
                        "case_id": "en-de:Haus",
                        "pair": "en-de",
                        "target": "Haus",
                        "expected_any": ["house"],
                        "expected_top1_any": ["house"],
                        "forbidden_top1": [],
                        "forbidden_any": [],
                        "tier": "smoke",
                    }
                ]
            },
            policy_payload={
                "dataset_contract": {
                    "required_case_fields": [
                        "case_id",
                        "pair",
                        "target",
                        "expected_any",
                        "expected_top1_any",
                        "forbidden_top1",
                        "forbidden_any",
                        "tier",
                    ],
                    "allowed_tiers": ["smoke", "hard"],
                    "min_cases_per_pair": {"en-es": 2, "en-de": 1},
                    "min_hard_cases_per_pair": {"en-es": 1, "en-de": 0},
                }
            },
            findings=findings,
            pair_scope="en-de",
        )

        self.assertEqual(
            [finding.code for finding in findings],
            [
                "DATASET_REQUIRED_FIELDS",
                "DATASET_TIER_VALUES",
                "DATASET_MIN_CASES",
                "DATASET_MIN_HARD_CASES",
            ],
        )
        self.assertTrue(all(finding.level == "PASS" for finding in findings))

    def test_validate_saturation_reports_repeated_metric_vectors(self) -> None:
        findings = []
        validate_saturation(
            benchmark_payload={
                "pairs": {
                    "en-es": {
                        "runs": [
                            {
                                "summary": {
                                    "objective_score": 1.0,
                                    "top1_accuracy": 0.8,
                                    "top3_recall": 0.9,
                                    "forbidden_top1_rate": 0.1,
                                    "forbidden_any_rate": 0.1,
                                    "avg_rules_per_target": 1.0,
                                }
                            },
                            {
                                "summary": {
                                    "objective_score": 1.0,
                                    "top1_accuracy": 0.8,
                                    "top3_recall": 0.9,
                                    "forbidden_top1_rate": 0.1,
                                    "forbidden_any_rate": 0.1,
                                    "avg_rules_per_target": 1.0,
                                }
                            },
                        ]
                    }
                }
            },
            policy_payload={
                "saturation": {
                    "warn_if_top_metric_vector_share_gte": 0.75,
                    "fail_if_top_metric_vector_share_gt": 1.1,
                    "warn_if_unique_metric_vectors_lt": 2,
                }
            },
            findings=findings,
            strict_saturation=False,
        )

        self.assertEqual(
            [finding.code for finding in findings],
            [
                "SATURATION_TOP_VECTOR_WARN",
                "SATURATION_UNIQUE_VECTOR_WARN",
            ],
        )
        self.assertTrue(all(finding.level == "WARN" for finding in findings))

    def test_validate_saturation_single_run_pair_scope_is_non_strict_warning(self) -> None:
        findings = []
        validate_saturation(
            benchmark_payload={
                "pairs": {
                    "en-ja": {
                        "runs": [
                            {
                                "summary": {
                                    "objective_score": 1.0,
                                    "top1_accuracy": 0.9,
                                    "top3_recall": 1.0,
                                    "forbidden_top1_rate": 0.0,
                                    "forbidden_any_rate": 0.0,
                                    "avg_rules_per_target": 2.0,
                                }
                            }
                        ]
                    },
                    "en-es": {
                        "runs": [
                            {
                                "summary": {
                                    "objective_score": 1.0,
                                    "top1_accuracy": 1.0,
                                    "top3_recall": 1.0,
                                    "forbidden_top1_rate": 0.0,
                                    "forbidden_any_rate": 0.0,
                                    "avg_rules_per_target": 1.0,
                                }
                            },
                            {
                                "summary": {
                                    "objective_score": 1.0,
                                    "top1_accuracy": 1.0,
                                    "top3_recall": 1.0,
                                    "forbidden_top1_rate": 0.0,
                                    "forbidden_any_rate": 0.0,
                                    "avg_rules_per_target": 1.0,
                                }
                            },
                        ]
                    },
                }
            },
            policy_payload={
                "saturation": {
                    "warn_if_top_metric_vector_share_gte": 0.75,
                    "fail_if_top_metric_vector_share_gt": 0.9,
                    "warn_if_unique_metric_vectors_lt": 2,
                }
            },
            findings=findings,
            strict_saturation=False,
            pair_scope="en-ja",
        )

        self.assertEqual([finding.code for finding in findings], ["SATURATION_SINGLE_RUN_WARN"])
        self.assertEqual(findings[0].level, "WARN")

    def test_validate_pos_guardrails_reports_matching_probe_and_inventory(self) -> None:
        findings = []
        validate_pos_guardrails(
            pos_probe_payload={
                "pair_reports": {
                    "en-es": {
                        "bucket_mismatch_rate": 0.0,
                    }
                }
            },
            pos_inventory_payload={
                "rows": [
                    {
                        "filename": "freq-es-cde.sqlite",
                        "unknown_pos_inventory_size": 0,
                    }
                ]
            },
            baseline_payload={
                "pos_pair_mismatch_rate": {"en-es": 0.0},
                "pos_unknown_counts": {"freq-es-cde.sqlite": 0},
            },
            policy_payload={
                "pos_guardrails": {
                    "max_bucket_mismatch_rate_by_pair": {"en-es": 0.01},
                    "max_bucket_mismatch_rate_increase": 0.0,
                    "default_unknown_pos_growth_budget": 0,
                }
            },
            findings=findings,
        )

        self.assertEqual(
            [finding.code for finding in findings],
            [
                "POS_MISMATCH_RATE_OK",
                "POS_UNKNOWN_GROWTH_OK",
            ],
        )
        self.assertTrue(all(finding.level == "PASS" for finding in findings))
