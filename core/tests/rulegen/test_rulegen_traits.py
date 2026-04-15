from __future__ import annotations

import unittest

from lexishift_core.rulegen.traits import (
    build_family_name_by_marker_id,
    build_rulegen_result_shape_trait_summary,
    build_rulegen_router_trait_summary,
)


class RulegenTraitsTest(unittest.TestCase):
    def test_build_rulegen_router_trait_summary_uses_candidate_rows(self) -> None:
        candidate_table = type(
            "_CandidateTable",
            (),
            {
                "candidate_ids": (10, 11, 12),
                "definition_bucket_ids": (0, 0, 1),
                "phrase_flags": (False, True, False),
                "variant_flags": (False, True, False),
                "reverse_check_supported_flags": (True, True, False),
                "reverse_check_hit_flags": (True, False, False),
                "interjection_shadowed_flags": (False, False, True),
                "current_sense_positions": (1, 2, 3),
                "target_pos_canonicals": ("noun", "noun", "verb"),
                "family_marker_id_rows": ((1,), (1, 2), ()),
            },
        )()

        summary = build_rulegen_router_trait_summary(
            target="batería",
            candidate_table=candidate_table,
            candidate_row_ids=(0, 1, 2),
            family_name_by_marker_id={1: "music", 2: "mechanics_tools"},
        )

        self.assertEqual(summary.target_length, len("batería"))
        self.assertEqual(summary.target_token_count, 1)
        self.assertEqual(summary.candidate_row_count, 3)
        self.assertEqual(summary.candidate_definition_bucket_count, 2)
        self.assertEqual(summary.candidate_phrase_count, 1)
        self.assertEqual(summary.candidate_variant_count, 1)
        self.assertEqual(summary.candidate_reverse_supported_count, 2)
        self.assertEqual(summary.candidate_reverse_hit_count, 1)
        self.assertEqual(summary.candidate_interjection_shadow_count, 1)
        self.assertEqual(summary.candidate_late_sense_count, 2)
        self.assertEqual(summary.candidate_target_pos_canonicals, ("noun", "verb"))
        self.assertEqual(summary.candidate_family_names, ("mechanics_tools", "music"))

    def test_build_rulegen_result_shape_trait_summary_counts_selected_sources(self) -> None:
        summary = build_rulegen_result_shape_trait_summary(
            all_sources=("battery", "drum kit", "set"),
            top1_source="drum kit",
            variant_rule_count=1,
            top1_is_variant=False,
        )

        self.assertEqual(summary.selected_source_count, 3)
        self.assertEqual(summary.selected_multiword_count, 1)
        self.assertEqual(summary.top1_source_token_count, 2)
        self.assertTrue(summary.top1_multiword)
        self.assertEqual(summary.variant_rule_count, 1)
        self.assertFalse(summary.top1_is_variant)

    def test_build_family_name_by_marker_id_filters_blank_names(self) -> None:
        summary = build_family_name_by_marker_id(
            {
                "music": 1,
                "": 2,
                "mechanics_tools": 3,
            }
        )

        self.assertEqual(summary, {1: "music", 3: "mechanics_tools"})


if __name__ == "__main__":
    unittest.main()
