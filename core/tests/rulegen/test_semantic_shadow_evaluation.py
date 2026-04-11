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
    evaluate_shadow_inventory_veto_proxy_against_benchmark_overlap_gold,
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

    def test_evaluate_shadow_inventory_support_score_policy_uses_threshold_parameters(
        self,
    ) -> None:
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
                                    "target": "vista",
                                    "reviewed_trigger_support": False,
                                    "benchmark_target_present": True,
                                    "canonical_pos": "verb",
                                },
                            ],
                        }
                    ],
                }
            ]
        }

        report = evaluate_shadow_inventory_against_benchmark_overlap_gold(
            inventory=inventory,
            benchmark_targets=benchmark_targets,
            policies=("support_score_v1",),
            support_score_min=3.0,
            support_score_max_promoted=1,
        )

        summary = report["policies"]["support_score_v1"]["summary"]
        self.assertEqual(summary["candidate_true_positive_count"], 1)
        self.assertEqual(summary["candidate_false_positive_count"], 0)
        self.assertEqual(summary["gold_trigger_rows_hit"], 1)

    def test_evaluate_shadow_inventory_support_score_policy_accepts_representative_pruning(
        self,
    ) -> None:
        benchmark_targets = (
            BenchmarkShadowTarget(
                target="amigo",
                case_ids=("en-es:amigo",),
                tiers=("hard",),
                reviewed_triggers=("friend",),
            ),
            BenchmarkShadowTarget(
                target="colega",
                case_ids=("en-es:colega",),
                tiers=("hard",),
                reviewed_triggers=("friend",),
            ),
        )
        inventory = {
            "targets": [
                {
                    "target": "amigo",
                    "trigger_entries": [
                        {
                            "trigger": "friend",
                            "active_candidates": [{"canonical_pos": "noun"}],
                            "shadow_candidates": [
                                {
                                    "target": "colega",
                                    "sense_label": "person whose company one enjoys",
                                    "reviewed_trigger_support": True,
                                    "benchmark_target_present": True,
                                    "canonical_pos": "noun",
                                },
                                {
                                    "target": "chochera",
                                    "sense_label": "person whose company one enjoys",
                                    "reviewed_trigger_support": False,
                                    "benchmark_target_present": False,
                                    "canonical_pos": "noun",
                                },
                            ],
                        }
                    ],
                }
            ]
        }

        report = evaluate_shadow_inventory_against_benchmark_overlap_gold(
            inventory=inventory,
            benchmark_targets=benchmark_targets,
            policies=("support_score_v1",),
            support_score_min=1.0,
            support_score_max_promoted=3,
            support_representative_pruning_mode="sense_label_pos_v1",
        )

        summary = report["policies"]["support_score_v1"]["summary"]
        self.assertEqual(summary["candidate_true_positive_count"], 1)
        self.assertEqual(summary["candidate_false_positive_count"], 0)

    def test_evaluate_shadow_inventory_veto_proxy_reports_allow_vs_abstain_outcomes(self) -> None:
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
                                }
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
                            "shadow_candidates": [],
                        }
                    ],
                },
            ]
        }

        report = evaluate_shadow_inventory_veto_proxy_against_benchmark_overlap_gold(
            inventory=inventory,
            benchmark_targets=benchmark_targets,
            policies=("cross_checked_v1", "none", "gold_overlap_oracle"),
        )

        cross_checked = report["policies"]["cross_checked_v1"]["summary"]
        self.assertEqual(cross_checked["ambiguous_trigger_rows"], 2)
        self.assertEqual(cross_checked["true_abstain_count"], 1)
        self.assertEqual(cross_checked["harmful_allow_count"], 1)
        self.assertEqual(cross_checked["true_allow_count"], 1)
        self.assertEqual(cross_checked["false_abstain_count"], 0)
        self.assertAlmostEqual(cross_checked["abstain_recall"], 0.5)
        self.assertAlmostEqual(cross_checked["allow_precision"], 0.5)
        self.assertAlmostEqual(cross_checked["overall_accuracy"], 2 / 3)

        none_summary = report["policies"]["none"]["summary"]
        self.assertEqual(none_summary["harmful_allow_count"], 2)
        self.assertEqual(none_summary["true_allow_count"], 1)
        self.assertEqual(none_summary["false_abstain_count"], 0)
        self.assertAlmostEqual(none_summary["overall_accuracy"], 1 / 3)

        oracle_summary = report["policies"]["gold_overlap_oracle"]["summary"]
        self.assertEqual(oracle_summary["true_abstain_count"], 2)
        self.assertEqual(oracle_summary["harmful_allow_count"], 0)
        self.assertEqual(oracle_summary["true_allow_count"], 1)
        self.assertEqual(oracle_summary["false_abstain_count"], 0)
        self.assertAlmostEqual(oracle_summary["overall_accuracy"], 1.0)

    def test_evaluate_shadow_inventory_veto_proxy_can_emit_full_row_results(self) -> None:
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
                                }
                            ],
                        }
                    ],
                },
                {
                    "target": "baile",
                    "trigger_entries": [
                        {
                            "trigger": "ball",
                            "active_candidates": [{"canonical_pos": "noun"}],
                            "shadow_candidates": [],
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
                                    "reviewed_trigger_support": True,
                                    "benchmark_target_present": True,
                                    "canonical_pos": "noun",
                                }
                            ],
                        }
                    ],
                },
            ]
        }

        report = evaluate_shadow_inventory_veto_proxy_against_benchmark_overlap_gold(
            inventory=inventory,
            benchmark_targets=benchmark_targets,
            policies=("cross_checked_v1",),
            include_row_results=True,
        )

        row_results = report["policies"]["cross_checked_v1"]["row_results"]
        self.assertEqual(len(row_results), 3)
        row_results_by_key = {(row["target"], row["trigger"]): row for row in row_results}
        self.assertEqual(row_results_by_key[("pelota", "ball")]["outcome"], "true_abstain")
        self.assertEqual(
            row_results_by_key[("pelota", "ball")]["feature_vector"]["active_support_mode"],
            "active_candidates",
        )
        self.assertEqual(
            row_results_by_key[("pelota", "ball")]["feature_dimensions"]["feature_inventory_entry"],
            ["present"],
        )
        self.assertEqual(row_results_by_key[("baile", "ball")]["outcome"], "harmful_allow")
        self.assertEqual(
            row_results_by_key[("baile", "ball")]["miss_classification"],
            "candidate_missing",
        )
        self.assertEqual(row_results_by_key[("agua", "water")]["outcome"], "false_abstain")
        self.assertFalse(row_results_by_key[("agua", "water")]["should_abstain"])
        self.assertTrue(row_results_by_key[("agua", "water")]["did_abstain"])

    def test_evaluate_shadow_inventory_veto_proxy_support_score_uses_active_profile_fallback(
        self,
    ) -> None:
        benchmark_targets = (
            BenchmarkShadowTarget(
                target="cargo",
                case_ids=("en-es:cargo",),
                tiers=("hard",),
                reviewed_triggers=("job",),
            ),
            BenchmarkShadowTarget(
                target="trabajo",
                case_ids=("en-es:trabajo",),
                tiers=("hard",),
                reviewed_triggers=("job",),
            ),
        )
        inventory = {
            "targets": [
                {
                    "target": "cargo",
                    "trigger_entries": [
                        {
                            "trigger": "job",
                            "active_candidates": [],
                            "active_profile_fallback": {"canonical_pos": "noun"},
                            "shadow_candidates": [
                                {
                                    "target": "trabajo",
                                    "reviewed_trigger_support": True,
                                    "benchmark_target_present": True,
                                    "canonical_pos": "noun",
                                }
                            ],
                        }
                    ],
                },
                {
                    "target": "trabajo",
                    "trigger_entries": [
                        {
                            "trigger": "job",
                            "active_candidates": [{"canonical_pos": "noun"}],
                            "shadow_candidates": [],
                        }
                    ],
                },
            ]
        }

        report = evaluate_shadow_inventory_veto_proxy_against_benchmark_overlap_gold(
            inventory=inventory,
            benchmark_targets=benchmark_targets,
            policies=("support_score_v1",),
            support_score_min=5.0,
            support_score_max_promoted=1,
        )

        summary = report["policies"]["support_score_v1"]["summary"]
        self.assertEqual(summary["ambiguous_trigger_rows"], 2)
        self.assertEqual(summary["true_abstain_count"], 1)
        self.assertEqual(summary["harmful_allow_count"], 1)
        harmful_rows = report["policies"]["support_score_v1"]["sample_harmful_allow_rows"]
        self.assertEqual([row["target"] for row in harmful_rows], ["trabajo"])

    def test_evaluate_shadow_inventory_veto_proxy_support_score_promotes_seed_supported_bridge(
        self,
    ) -> None:
        benchmark_targets = (
            BenchmarkShadowTarget(
                target="trabajo",
                case_ids=("en-es:trabajo",),
                tiers=("hard",),
                reviewed_triggers=("job",),
            ),
            BenchmarkShadowTarget(
                target="cargo",
                case_ids=("en-es:cargo",),
                tiers=("hard",),
                reviewed_triggers=("job",),
            ),
        )
        inventory = {
            "targets": [
                {
                    "target": "trabajo",
                    "trigger_entries": [
                        {
                            "trigger": "job",
                            "active_candidates": [{"canonical_pos": "noun"}],
                            "shadow_candidates": [
                                {
                                    "target": "cargo",
                                    "reviewed_trigger_support": True,
                                    "benchmark_target_present": True,
                                    "canonical_pos": "noun",
                                    "embedding_bridge_similarity": 0.71,
                                }
                            ],
                        }
                    ],
                },
                {
                    "target": "cargo",
                    "trigger_entries": [
                        {
                            "trigger": "job",
                            "active_candidates": [],
                            "shadow_candidates": [],
                        }
                    ],
                },
            ]
        }

        report = evaluate_shadow_inventory_veto_proxy_against_benchmark_overlap_gold(
            inventory=inventory,
            benchmark_targets=benchmark_targets,
            policies=("support_score_v1",),
            support_score_min=5.0,
            support_score_max_promoted=1,
        )

        summary = report["policies"]["support_score_v1"]["summary"]
        self.assertEqual(summary["ambiguous_trigger_rows"], 2)
        self.assertEqual(summary["true_abstain_count"], 1)
        self.assertEqual(summary["harmful_allow_count"], 1)
        harmful_rows = report["policies"]["support_score_v1"]["sample_harmful_allow_rows"]
        self.assertEqual([row["target"] for row in harmful_rows], ["cargo"])

    def test_evaluate_shadow_inventory_veto_proxy_accumulates_slice_summaries(self) -> None:
        benchmark_targets = (
            BenchmarkShadowTarget(
                target="cargo",
                case_ids=("en-es:cargo",),
                tiers=("hard",),
                reviewed_triggers=("job",),
            ),
            BenchmarkShadowTarget(
                target="trabajo",
                case_ids=("en-es:trabajo",),
                tiers=("smoke",),
                reviewed_triggers=("job",),
            ),
            BenchmarkShadowTarget(
                target="casa",
                case_ids=("en-es:casa",),
                tiers=("smoke",),
                reviewed_triggers=("house",),
            ),
        )
        inventory = {
            "targets": [
                {
                    "target": "cargo",
                    "trigger_entries": [
                        {
                            "trigger": "job",
                            "active_candidates": [{"canonical_pos": "noun"}],
                            "shadow_candidates": [
                                {
                                    "target": "trabajo",
                                    "reviewed_trigger_support": True,
                                    "benchmark_target_present": True,
                                    "canonical_pos": "noun",
                                }
                            ],
                        }
                    ],
                },
                {
                    "target": "trabajo",
                    "trigger_entries": [
                        {
                            "trigger": "job",
                            "active_candidates": [{"canonical_pos": "noun"}],
                            "shadow_candidates": [],
                        }
                    ],
                },
                {
                    "target": "casa",
                    "trigger_entries": [
                        {
                            "trigger": "house",
                            "active_candidates": [{"canonical_pos": "noun"}],
                            "shadow_candidates": [],
                        }
                    ],
                },
            ]
        }

        report = evaluate_shadow_inventory_veto_proxy_against_benchmark_overlap_gold(
            inventory=inventory,
            benchmark_targets=benchmark_targets,
            row_metadata_by_key={
                ("cargo", "job"): {
                    "case_ids": ["en-es:cargo"],
                    "tiers": ["hard"],
                    "slice_tags": ["family:job_role"],
                    "slice_dimensions": {
                        "semantic_family": ["job_role"],
                        "decision": ["ambiguous"],
                        "pos": ["noun"],
                    },
                },
                ("trabajo", "job"): {
                    "case_ids": ["en-es:trabajo"],
                    "tiers": ["smoke"],
                    "slice_tags": ["family:job_role"],
                    "slice_dimensions": {
                        "semantic_family": ["job_role"],
                        "decision": ["ambiguous"],
                        "pos": ["noun"],
                    },
                },
                ("casa", "house"): {
                    "case_ids": ["en-es:casa"],
                    "tiers": ["smoke"],
                    "slice_tags": ["family:house_home"],
                    "slice_dimensions": {
                        "semantic_family": ["house_home"],
                        "decision": ["clear"],
                        "pos": ["noun"],
                    },
                },
            },
            policies=("support_score_v1",),
            support_score_min=5.0,
            support_score_max_promoted=1,
        )

        policy_payload = report["policies"]["support_score_v1"]
        harmful_rows = policy_payload["sample_harmful_allow_rows"]
        self.assertEqual(harmful_rows[0]["case_ids"], ["en-es:trabajo"])
        self.assertEqual(harmful_rows[0]["miss_classification"], "candidate_missing")
        self.assertEqual(harmful_rows[0]["slice_tags"], ["family:job_role"])

        slice_summaries = policy_payload["slice_summaries"]
        job_family = slice_summaries["tag:family:job_role"]
        self.assertEqual(job_family["trigger_rows_total"], 2)
        self.assertEqual(job_family["ambiguous_trigger_rows"], 2)
        self.assertEqual(job_family["true_abstain_count"], 1)
        self.assertEqual(job_family["harmful_allow_count"], 1)
        self.assertAlmostEqual(job_family["abstain_recall"], 0.5)
        self.assertAlmostEqual(job_family["overall_accuracy"], 0.5)

        clear_slice = slice_summaries["dimension:decision:clear"]
        self.assertEqual(clear_slice["clear_trigger_rows"], 1)
        self.assertEqual(clear_slice["true_allow_count"], 1)
        self.assertAlmostEqual(clear_slice["overblocking_rate"], 0.0)
        self.assertAlmostEqual(clear_slice["overall_accuracy"], 1.0)

        tier_slice = slice_summaries["dimension:tier:smoke"]
        self.assertEqual(tier_slice["trigger_rows_total"], 2)
        self.assertEqual(tier_slice["harmful_allow_count"], 1)
        self.assertEqual(tier_slice["true_allow_count"], 1)

        inventory_present_slice = slice_summaries["feature:feature_inventory_entry:present"]
        self.assertEqual(inventory_present_slice["trigger_rows_total"], 3)
        self.assertEqual(inventory_present_slice["harmful_allow_count"], 1)

        candidate_pool_slice = slice_summaries["feature:feature_shadow_candidate_count:one"]
        self.assertEqual(candidate_pool_slice["trigger_rows_total"], 1)
        self.assertEqual(candidate_pool_slice["true_abstain_count"], 1)

    def test_evaluate_shadow_inventory_veto_proxy_classifies_seed_missing_harmful_allow(
        self,
    ) -> None:
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
        inventory = {"targets": [{"target": "pelota", "trigger_entries": []}]}

        report = evaluate_shadow_inventory_veto_proxy_against_benchmark_overlap_gold(
            inventory=inventory,
            benchmark_targets=benchmark_targets,
            policies=("none",),
        )

        harmful_rows = report["policies"]["none"]["sample_harmful_allow_rows"]
        self.assertEqual(len(harmful_rows), 2)
        self.assertEqual(harmful_rows[0]["miss_classification"], "seed_missing")
        self.assertEqual(harmful_rows[1]["miss_classification"], "seed_missing")
