from __future__ import annotations

import os
import sys
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lexishift_core.rulegen.semantic_shadow_feature_vector import (  # noqa: E402
    build_semantic_shadow_case_feature_vector,
    build_semantic_shadow_feature_dimensions,
)


class TestSemanticShadowFeatureVector(unittest.TestCase):
    def test_build_semantic_shadow_case_feature_vector_uses_runtime_eligible_candidate_signals(
        self,
    ) -> None:
        feature_vector = build_semantic_shadow_case_feature_vector(
            inventory_entry_present=True,
            active_candidates=[{"canonical_pos": "noun"}],
            active_profile_fallback={"canonical_pos": "verb"},
            shadow_candidates=[
                {
                    "target": "trabajo",
                    "canonical_pos": "noun",
                    "candidate_sources": ["reverse_lookup", "forward_index"],
                    "reviewed_trigger_support": True,
                    "benchmark_target_present": True,
                    "target_trigger_family_terms": ["job", "work"],
                    "forward_neighborhood_terms": ["employment", "position"],
                },
                {
                    "target": "cargo",
                    "canonical_pos": "noun",
                    "candidate_sources": ["reverse_lookup"],
                    "semantic_bridge_markers": ["occupation"],
                },
            ],
            promoted_targets=["trabajo"],
        )

        self.assertTrue(feature_vector["inventory_entry_present"])
        self.assertEqual(feature_vector["active_support_mode"], "active_candidates")
        self.assertEqual(feature_vector["active_candidate_count"], 1)
        self.assertEqual(feature_vector["active_pos_values"], ["noun"])
        self.assertEqual(feature_vector["shadow_candidate_count"], 2)
        self.assertEqual(feature_vector["promoted_target_count"], 1)
        self.assertEqual(
            feature_vector["candidate_source_family_histogram"],
            {"forward_index": 1, "reverse_lookup": 2},
        )
        self.assertEqual(feature_vector["candidate_pos_histogram"], {"noun": 2})
        self.assertEqual(feature_vector["reviewed_trigger_support_candidate_count"], 1)
        self.assertEqual(feature_vector["benchmark_target_present_candidate_count"], 1)
        self.assertEqual(feature_vector["same_pos_candidate_count"], 2)
        self.assertEqual(feature_vector["multi_source_candidate_count"], 1)
        self.assertEqual(feature_vector["semantic_bridge_candidate_count"], 1)
        self.assertEqual(feature_vector["trigger_family_candidate_count"], 1)
        self.assertEqual(feature_vector["forward_neighborhood_candidate_count"], 1)

    def test_build_semantic_shadow_feature_dimensions_buckets_case_shape(self) -> None:
        feature_dimensions = build_semantic_shadow_feature_dimensions(
            {
                "inventory_entry_present": False,
                "active_support_mode": "profile_only",
                "active_candidate_count": 0,
                "shadow_candidate_count": 4,
                "promoted_target_count": 2,
                "candidate_source_families": ["forward_index", "reverse_lookup"],
                "candidate_source_family_count": 2,
                "candidate_pos_count": 1,
                "reviewed_trigger_support_candidate_count": 0,
                "benchmark_target_present_candidate_count": 1,
                "same_pos_candidate_count": 2,
                "multi_source_candidate_count": 1,
                "semantic_bridge_candidate_count": 0,
                "trigger_family_candidate_count": 3,
                "forward_neighborhood_candidate_count": 4,
            }
        )

        self.assertEqual(feature_dimensions["feature_inventory_entry"], ["missing"])
        self.assertEqual(feature_dimensions["feature_active_support_mode"], ["profile_only"])
        self.assertEqual(feature_dimensions["feature_shadow_candidate_count"], ["four_plus"])
        self.assertEqual(feature_dimensions["feature_promoted_target_count"], ["two_to_three"])
        self.assertEqual(
            feature_dimensions["feature_candidate_source_family_signature"],
            ["forward_index+reverse_lookup"],
        )
        self.assertEqual(feature_dimensions["feature_same_pos_candidate_count"], ["two_to_three"])
        self.assertEqual(
            feature_dimensions["feature_forward_neighborhood_candidate_count"],
            ["four_plus"],
        )
