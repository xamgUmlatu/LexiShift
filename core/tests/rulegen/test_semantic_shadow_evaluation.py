from __future__ import annotations

import os
import sys
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lexishift_core.rulegen.semantic_shadow_evaluation import (  # noqa: E402
    build_benchmark_trigger_overlap_gold,
    evaluate_shadow_inventory_against_benchmark_overlap_gold,
)
from lexishift_core.rulegen.semantic_shadow_inventory import (  # noqa: E402
    BenchmarkShadowTarget,
)


class TestSemanticShadowEvaluation(unittest.TestCase):
    def test_build_benchmark_trigger_overlap_gold_derives_other_targets_for_shared_trigger(
        self,
    ) -> None:
        gold = build_benchmark_trigger_overlap_gold(
            (
                BenchmarkShadowTarget(
                    target="pelota",
                    case_ids=("en-es:pelota",),
                    tiers=("hard",),
                    reviewed_triggers=("ball", "sphere"),
                ),
                BenchmarkShadowTarget(
                    target="baile",
                    case_ids=("en-es:baile",),
                    tiers=("hard",),
                    reviewed_triggers=("ball", "gala"),
                ),
                BenchmarkShadowTarget(
                    target="agua",
                    case_ids=("en-es:agua",),
                    tiers=("smoke",),
                    reviewed_triggers=("water",),
                ),
            )
        )

        self.assertEqual(gold[("pelota", "ball")], ("baile",))
        self.assertEqual(gold[("baile", "ball")], ("pelota",))
        self.assertEqual(gold[("pelota", "sphere")], ())
        self.assertEqual(gold[("agua", "water")], ())

    def test_evaluate_shadow_inventory_scores_auto_policies_against_overlap_gold(self) -> None:
        benchmark_targets = (
            BenchmarkShadowTarget(
                target="pelota",
                case_ids=("en-es:pelota",),
                tiers=("hard",),
                reviewed_triggers=("ball",),
            ),
            BenchmarkShadowTarget(
                target="baile",
                case_ids=("en-es:baile",),
                tiers=("hard",),
                reviewed_triggers=("ball",),
            ),
            BenchmarkShadowTarget(
                target="agua",
                case_ids=("en-es:agua",),
                tiers=("smoke",),
                reviewed_triggers=("water",),
            ),
        )
        inventory = {
            "targets": [
                {
                    "target": "pelota",
                    "trigger_entries": [
                        {
                            "trigger": "ball",
                            "active_candidates": [{"canonical_pos": "noun"}],
                            "shadow_candidates": [
                                {
                                    "target": "baile",
                                    "reviewed_trigger_support": True,
                                    "benchmark_target_present": True,
                                    "canonical_pos": "noun",
                                },
                                {
                                    "target": "bola mala",
                                    "reviewed_trigger_support": False,
                                    "benchmark_target_present": False,
                                    "canonical_pos": "noun",
                                },
                            ],
                        }
                    ],
                },
                {
                    "target": "agua",
                    "trigger_entries": [
                        {
                            "trigger": "water",
                            "active_candidates": [{"canonical_pos": "noun"}],
                            "shadow_candidates": [
                                {
                                    "target": "wata",
                                    "reviewed_trigger_support": False,
                                    "benchmark_target_present": False,
                                    "canonical_pos": "noun",
                                }
                            ],
                        }
                    ],
                },
            ]
        }

        report = evaluate_shadow_inventory_against_benchmark_overlap_gold(
            inventory=inventory,
            benchmark_targets=benchmark_targets,
            policies=("same_pos_lenient_v1", "cross_checked_v1", "none", "gold_overlap_oracle"),
        )

        candidate_pool = report["candidate_pool_summary"]
        self.assertEqual(candidate_pool["trigger_rows_total"], 3)
        self.assertEqual(candidate_pool["trigger_rows_with_inventory_entry"], 2)
        self.assertEqual(candidate_pool["gold_trigger_rows"], 2)
        self.assertEqual(candidate_pool["gold_trigger_rows_with_inventory_entry"], 1)
        self.assertEqual(candidate_pool["gold_trigger_rows_with_mined_overlap"], 1)
        self.assertAlmostEqual(candidate_pool["inventory_entry_coverage_rate"], 2 / 3)

        same_pos = report["policies"]["same_pos_lenient_v1"]["summary"]
        self.assertEqual(same_pos["candidate_true_positive_count"], 1)
        self.assertEqual(same_pos["candidate_false_positive_count"], 2)
        self.assertEqual(same_pos["gold_trigger_rows_hit"], 1)
        self.assertEqual(same_pos["no_gold_trigger_rows_overblocked"], 1)
        self.assertAlmostEqual(same_pos["candidate_precision"], 1 / 3)

        cross_checked = report["policies"]["cross_checked_v1"]["summary"]
        self.assertEqual(cross_checked["candidate_true_positive_count"], 1)
        self.assertEqual(cross_checked["candidate_false_positive_count"], 0)
        self.assertEqual(cross_checked["no_gold_trigger_rows_overblocked"], 0)
        self.assertEqual(cross_checked["gold_trigger_rows_exact_match"], 1)
        self.assertAlmostEqual(cross_checked["candidate_precision"], 1.0)
        self.assertAlmostEqual(cross_checked["gold_trigger_hit_rate"], 0.5)

        none_summary = report["policies"]["none"]["summary"]
        self.assertEqual(none_summary["gold_trigger_rows_underblocked"], 2)
        self.assertEqual(none_summary["candidate_true_positive_count"], 0)

        oracle_summary = report["policies"]["gold_overlap_oracle"]["summary"]
        self.assertEqual(oracle_summary["candidate_true_positive_count"], 2)
        self.assertEqual(oracle_summary["candidate_false_positive_count"], 0)
        self.assertEqual(oracle_summary["gold_trigger_rows_exact_match"], 2)

    def test_evaluate_shadow_inventory_counts_missing_inventory_rows_as_underblocked(self) -> None:
        benchmark_targets = (
            BenchmarkShadowTarget(
                target="pelota",
                case_ids=("en-es:pelota",),
                tiers=("hard",),
                reviewed_triggers=("ball",),
            ),
            BenchmarkShadowTarget(
                target="baile",
                case_ids=("en-es:baile",),
                tiers=("hard",),
                reviewed_triggers=("ball",),
            ),
        )
        inventory = {
            "targets": [
                {
                    "target": "pelota",
                    "trigger_entries": [],
                }
            ]
        }

        report = evaluate_shadow_inventory_against_benchmark_overlap_gold(
            inventory=inventory,
            benchmark_targets=benchmark_targets,
            policies=("cross_checked_v1",),
        )

        candidate_pool = report["candidate_pool_summary"]
        self.assertEqual(candidate_pool["trigger_rows_total"], 2)
        self.assertEqual(candidate_pool["trigger_rows_with_inventory_entry"], 0)
        self.assertEqual(candidate_pool["gold_trigger_rows"], 2)
        self.assertEqual(candidate_pool["gold_trigger_rows_with_inventory_entry"], 0)
        self.assertEqual(candidate_pool["gold_trigger_rows_with_mined_overlap"], 0)

        cross_checked = report["policies"]["cross_checked_v1"]["summary"]
        self.assertEqual(cross_checked["gold_trigger_rows_underblocked"], 2)
        self.assertEqual(cross_checked["gold_trigger_rows_hit"], 0)
