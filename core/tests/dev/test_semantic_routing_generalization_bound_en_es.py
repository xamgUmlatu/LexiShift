from __future__ import annotations

from pathlib import Path
import sys
import unittest

CORE_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = CORE_ROOT.parent
SCRIPTS_ROOT = REPO_ROOT / "scripts" / "testing"
for candidate in (str(CORE_ROOT), str(SCRIPTS_ROOT)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from semantic_routing_generalization_bound_en_es import (  # noqa: E402
    FIXED_SHADOW_ACTIVE_ONLY_REFERENCE_CONFIG,
    FIXED_SHADOW_ACTIVE_ONLY_RESCUE_OVERLAY_CONFIG,
    FIXED_SHADOW_CONTROL_CONFIG,
    FIXED_SHADOW_LADDER_CONFIG,
    FIXED_SHADOW_REFERENCE_CONFIG,
    FIXED_SHADOW_RESCUE_OVERLAY_CONFIG,
    resolve_fixed_shadow_ladder_config,
)
from semantic_routing_generalization_bound_reporting import (  # noqa: E402
    render_generalization_bound_markdown,
)
from semantic_routing_sentence_veto_support import (  # noqa: E402
    DEFAULT_SENTENCE_VETO_DATASET,
)


class SemanticRoutingGeneralizationBoundTests(unittest.TestCase):
    def test_default_sentence_veto_dataset_advances_to_v10(self) -> None:
        self.assertTrue(str(DEFAULT_SENTENCE_VETO_DATASET).endswith("en_es_sentence_veto_v10.json"))

    def test_bound_configs_track_current_runtime_control_and_candidate_lanes(self) -> None:
        self.assertEqual(FIXED_SHADOW_CONTROL_CONFIG["label"], "Fixed-shadow runtime control")
        self.assertEqual(
            FIXED_SHADOW_CONTROL_CONFIG["phrase_control_mode"], "noun_family_frame_guard"
        )
        self.assertEqual(
            FIXED_SHADOW_CONTROL_CONFIG["active_rescue_mode"],
            "sense_label_near_tie_active_rescue",
        )
        self.assertEqual(
            FIXED_SHADOW_REFERENCE_CONFIG["label"],
            "Sentence-transformer phrase-guard candidate",
        )
        self.assertEqual(FIXED_SHADOW_REFERENCE_CONFIG["min_margin"], 0.0)
        self.assertEqual(
            FIXED_SHADOW_REFERENCE_CONFIG["phrase_control_mode"],
            "noun_family_frame_guard",
        )
        self.assertEqual(
            FIXED_SHADOW_REFERENCE_CONFIG["active_rescue_mode"],
            "sense_label_near_tie_active_rescue",
        )
        self.assertEqual(
            FIXED_SHADOW_ACTIVE_ONLY_REFERENCE_CONFIG["label"],
            "Sentence-transformer active-sense phrase-guard experiment",
        )
        self.assertEqual(
            FIXED_SHADOW_ACTIVE_ONLY_REFERENCE_CONFIG["phrase_guard_pos_scope"],
            "active_only",
        )
        self.assertTrue(bool(FIXED_SHADOW_ACTIVE_ONLY_REFERENCE_CONFIG["experimental"]))
        self.assertEqual(
            FIXED_SHADOW_LADDER_CONFIG["label"],
            "Sentence-transformer zero-noise soft ladder",
        )
        resolved_ladder_config = resolve_fixed_shadow_ladder_config(
            sentence_dataset=DEFAULT_SENTENCE_VETO_DATASET
        )
        self.assertEqual(resolved_ladder_config["soft_min_active_score"], 0.60)
        self.assertEqual(resolved_ladder_config["soft_min_margin"], 0.0)
        self.assertEqual(resolved_ladder_config["resolved_config_id"], "soft:a=0.60:m=0.00")
        self.assertEqual(
            FIXED_SHADOW_RESCUE_OVERLAY_CONFIG["label"],
            "Sentence-transformer widened-rescue candidate (simulated)",
        )
        self.assertEqual(FIXED_SHADOW_RESCUE_OVERLAY_CONFIG["primary_margin_floor"], -0.05)
        self.assertEqual(FIXED_SHADOW_RESCUE_OVERLAY_CONFIG["backup_margin_floor"], 0.02)
        self.assertEqual(
            FIXED_SHADOW_ACTIVE_ONLY_RESCUE_OVERLAY_CONFIG["label"],
            "Sentence-transformer active-sense phrase-guard overlay (simulated)",
        )
        self.assertEqual(
            FIXED_SHADOW_ACTIVE_ONLY_RESCUE_OVERLAY_CONFIG["phrase_guard_pos_scope"],
            "active_only",
        )
        self.assertTrue(bool(FIXED_SHADOW_ACTIVE_ONLY_RESCUE_OVERLAY_CONFIG["experimental"]))

    def test_markdown_renders_runtime_reference_corridor(self) -> None:
        markdown = render_generalization_bound_markdown(
            {
                "status": "ok",
                "generated_at": "2026-04-23T00:00:00Z",
                "pair": "en-es",
                "methodology": {
                    "bootstrap_kind": "cluster_bootstrap_plus_leave_one_cluster_out",
                    "bootstrap_iterations": 10,
                    "confidence_level": 0.95,
                    "random_seed": 1729,
                },
                "confidence_corridor": {
                    "source_only_source_id": "borrowed_trigger_auto_shadows",
                    "source_only_abstain_recall_conservative_floor": 0.032,
                    "source_only_harmful_allow_conservative_ceiling": 0.968,
                    "fixed_shadow_replace_recall_conservative_floor": 0.214,
                    "fixed_shadow_harmful_replace_conservative_ceiling": 0.0,
                    "fixed_shadow_reference_label": "Sentence-transformer phrase-guard candidate",
                    "fixed_shadow_reference_replace_recall_conservative_floor": 0.75,
                    "fixed_shadow_reference_harmful_replace_conservative_ceiling": 0.071,
                    "fixed_shadow_reference_false_abstain_conservative_ceiling": 0.25,
                    "fixed_shadow_active_only_reference_label": "Sentence-transformer active-sense phrase-guard experiment",
                    "fixed_shadow_active_only_reference_replace_recall_conservative_floor": 0.75,
                    "fixed_shadow_active_only_reference_harmful_replace_conservative_ceiling": 0.0,
                    "fixed_shadow_active_only_reference_false_abstain_conservative_ceiling": 0.25,
                    "fixed_shadow_ladder_label": "Sentence-transformer zero-noise soft ladder",
                    "fixed_shadow_ladder_replace_or_soft_recall_conservative_floor": 0.821,
                    "fixed_shadow_ladder_soft_noise_conservative_ceiling": 0.0,
                    "fixed_shadow_rescue_overlay_label": "Sentence-transformer widened-rescue candidate (simulated)",
                    "fixed_shadow_rescue_overlay_replace_recall_conservative_floor": 0.893,
                    "fixed_shadow_rescue_overlay_harmful_replace_conservative_ceiling": 0.071,
                    "fixed_shadow_rescue_overlay_false_abstain_conservative_ceiling": 0.107,
                    "fixed_shadow_active_only_rescue_overlay_label": "Sentence-transformer active-sense phrase-guard overlay (simulated)",
                    "fixed_shadow_active_only_rescue_overlay_replace_recall_conservative_floor": 0.893,
                    "fixed_shadow_active_only_rescue_overlay_harmful_replace_conservative_ceiling": 0.0,
                    "fixed_shadow_active_only_rescue_overlay_false_abstain_conservative_ceiling": 0.107,
                },
                "fixed_shadow_bounds": [],
                "veto_proxy_bounds": [],
            },
            fixed_shadow_metric_order=(),
            veto_proxy_metric_order=(),
        )
        self.assertIn("Evaluated runtime reference lane", markdown)
        self.assertIn("Sentence-transformer phrase-guard candidate", markdown)
        self.assertIn("Runtime reference replace-recall conservative floor", markdown)
        self.assertIn("Experimental phrase-guard lane", markdown)
        self.assertIn("Sentence-transformer active-sense phrase-guard experiment", markdown)
        self.assertIn("Experimental phrase-guard harmful-replace conservative ceiling", markdown)
        self.assertIn("Evaluated runtime ladder lane", markdown)
        self.assertIn("Sentence-transformer zero-noise soft ladder", markdown)
        self.assertIn("Runtime ladder replace-or-soft recall conservative floor", markdown)
        self.assertIn("Evaluated rescue-overlay lane", markdown)
        self.assertIn("Sentence-transformer widened-rescue candidate (simulated)", markdown)
        self.assertIn("Rescue-overlay replace-recall conservative floor", markdown)
        self.assertIn("Experimental phrase-guard overlay lane", markdown)
        self.assertIn(
            "Sentence-transformer active-sense phrase-guard overlay (simulated)", markdown
        )


if __name__ == "__main__":
    unittest.main()
