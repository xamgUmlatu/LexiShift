from __future__ import annotations

from pathlib import Path
import sys
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_ROOT = PROJECT_ROOT / "scripts" / "testing"
for candidate in (str(PROJECT_ROOT), str(SCRIPT_ROOT)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from semantic_shadow_experiment_compare_support import (  # noqa: E402
    build_candidate_feature_bucket_risk_report,
)


class TestSemanticShadowExperimentCompareSupport(unittest.TestCase):
    def test_build_candidate_feature_bucket_risk_report_surfaces_upstream_error_buckets(
        self,
    ) -> None:
        candidate_result = {
            "veto_summary": {
                "harmful_allow_rate": 0.4,
                "overblocking_rate": 0.1,
            },
            "veto_row_results": [
                {
                    "target": "a",
                    "trigger": "x",
                    "should_abstain": True,
                    "outcome": "harmful_allow",
                    "miss_classification": "seed_missing",
                    "feature_dimensions": {
                        "feature_inventory_entry": ["missing"],
                        "feature_promoted_target_count": ["none"],
                    },
                },
                {
                    "target": "b",
                    "trigger": "x",
                    "should_abstain": True,
                    "outcome": "harmful_allow",
                    "miss_classification": "candidate_missing",
                    "feature_dimensions": {
                        "feature_inventory_entry": ["missing"],
                        "feature_promoted_target_count": ["none"],
                    },
                },
                {
                    "target": "c",
                    "trigger": "x",
                    "should_abstain": True,
                    "outcome": "true_abstain",
                    "feature_dimensions": {
                        "feature_inventory_entry": ["missing"],
                        "feature_promoted_target_count": ["one"],
                    },
                },
                {
                    "target": "d",
                    "trigger": "y",
                    "should_abstain": False,
                    "outcome": "false_abstain",
                    "feature_dimensions": {
                        "feature_candidate_source_family_signature": [
                            "forward_index+reverse_lookup"
                        ],
                    },
                },
                {
                    "target": "e",
                    "trigger": "y",
                    "should_abstain": False,
                    "outcome": "true_allow",
                    "feature_dimensions": {
                        "feature_candidate_source_family_signature": [
                            "forward_index+reverse_lookup"
                        ],
                    },
                },
                {
                    "target": "f",
                    "trigger": "y",
                    "should_abstain": False,
                    "outcome": "true_allow",
                    "feature_dimensions": {
                        "feature_candidate_source_family_signature": [
                            "forward_index+reverse_lookup"
                        ],
                    },
                },
            ],
        }
        row_comparison = {
            "persistent_harmful_allow_rows": [
                {"target": "a", "trigger": "x"},
                {"target": "b", "trigger": "x"},
            ],
            "persistent_false_abstain_rows": [
                {"target": "d", "trigger": "y"},
            ],
        }

        report = build_candidate_feature_bucket_risk_report(
            candidate_result=candidate_result,
            row_comparison=row_comparison,
        )

        harmful_allow_rows = report["harmful_allow_bucket_rows"]
        self.assertEqual(
            harmful_allow_rows[0]["slice_key"], "feature:feature_inventory_entry:missing"
        )
        self.assertEqual(harmful_allow_rows[0]["harmful_allow_count"], 2)
        self.assertEqual(harmful_allow_rows[0]["persistent_harmful_allow_count"], 2)
        self.assertEqual(
            harmful_allow_rows[0]["harmful_allow_miss_counts"],
            {
                "seed_missing": 1,
                "candidate_missing": 1,
                "promotion_miss": 0,
            },
        )
        self.assertEqual(report["excluded_feature_dimensions"], ["feature_promoted_target_count"])
        self.assertNotIn(
            "feature:feature_promoted_target_count:none",
            {row["slice_key"] for row in harmful_allow_rows},
        )

        false_abstain_rows = report["false_abstain_bucket_rows"]
        self.assertEqual(
            false_abstain_rows[0]["slice_key"],
            "feature:feature_candidate_source_family_signature:forward_index+reverse_lookup",
        )
        self.assertEqual(false_abstain_rows[0]["false_abstain_count"], 1)
        self.assertEqual(false_abstain_rows[0]["persistent_false_abstain_count"], 1)
