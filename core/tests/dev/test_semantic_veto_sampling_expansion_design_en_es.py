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

from semantic_veto_sampling_expansion_design_en_es import (  # noqa: E402
    build_sampling_expansion_design_report,
    render_sampling_expansion_markdown,
)


class SemanticVetoSamplingExpansionDesignTests(unittest.TestCase):
    def test_sampling_design_separates_representative_stratified_targeted_and_locked(
        self,
    ) -> None:
        report = build_sampling_expansion_design_report(
            manifest=_manifest(),
            curve_payload=_curve_payload(),
            policy_payload=_policy(),
            generated_at="2026-05-05T00:00:00Z",
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["decision"], "sampling_expansion_design_established")
        self.assertEqual(report["summary"]["curve_queue_rows_read"], 3)
        self.assertEqual(report["summary"]["curve_queue_priority_counts"]["P0"], 2)
        self.assertGreater(report["summary"]["locked_eval_share"], 0.3)

        representative = next(
            row
            for row in report["lane_reports"]
            if row["lane_id"] == "representative_random_product_lane"
        )
        self.assertTrue(representative["is_representative"])
        self.assertTrue(representative["can_support_promotion_metric"])
        self.assertEqual(representative["manual_discovery_rows"], 0)
        self.assertEqual(representative["llm_discovery_rows"], 0)
        self.assertEqual(representative["locked_eval_rows"], 12)

        stratified = next(
            row
            for row in report["lane_reports"]
            if row["lane_id"] == "stratified_difficulty_surface_lane"
        )
        self.assertFalse(stratified["is_representative"])
        self.assertEqual(len(report["stratified_cells"]), 8)
        self.assertEqual(stratified["manual_discovery_rows"], 8)
        self.assertEqual(stratified["llm_discovery_rows"], 8)
        self.assertEqual(stratified["locked_eval_rows"], 8)

        targeted = next(
            row
            for row in report["lane_reports"]
            if row["lane_id"] == "targeted_curve_mechanism_lane"
        )
        self.assertEqual(targeted["manual_discovery_rows"], 7)
        self.assertEqual(targeted["llm_discovery_rows"], 25)
        self.assertEqual(targeted["locked_eval_rows"], 13)
        self.assertEqual(len(report["targeted_curve_cells"]), 2)
        self.assertTrue(all(row["priority"] == "P0" for row in report["targeted_curve_cells"]))

        markdown = render_sampling_expansion_markdown(report)
        self.assertIn("Sampling Expansion Design", markdown)
        self.assertIn("Lane Budgets", markdown)
        self.assertIn("Bias Controls", markdown)

    def test_missing_random_seed_is_review(self) -> None:
        manifest = _manifest()
        manifest["random_seed"] = ""
        report = build_sampling_expansion_design_report(
            manifest=manifest,
            curve_payload=_curve_payload(),
            policy_payload=_policy(),
            generated_at="2026-05-05T00:00:00Z",
        )

        self.assertEqual(report["status"], "review")
        self.assertIn("manifest_missing_random_seed", report["summary"]["issues"])


def _manifest() -> dict[str, object]:
    return {
        "schema_version": 1,
        "random_seed": "test_seed",
        "global_rules": [
            "Keep representative, stratified, targeted, control, discovery, and locked rows separate."
        ],
        "split_policy": {
            "method": "stable_hash_row_id",
            "representative_random_policy": "locked_eval_only_for_product_estimation",
        },
        "lanes": [
            {
                "lane_id": "representative_random_product_lane",
                "lane_type": "representative_random",
                "purpose": "Estimate product quality.",
                "claim_supported": "product_quality_estimate",
                "sampling_frame": "Normal app candidates.",
                "selection_method": "Seeded random.",
                "manual_discovery_rows": 0,
                "llm_discovery_rows": 0,
                "locked_eval_rows": 12,
                "bias_controls": ["do_not_condition_on_current_failure_status"],
            },
            {
                "lane_id": "stratified_difficulty_surface_lane",
                "lane_type": "stratified_balanced",
                "purpose": "Draw curves.",
                "claim_supported": "curve_shape_estimation",
                "sampling_frame": "Pre-outcome metadata.",
                "selection_method": "Balanced random.",
                "case_types": ["positive_active", "phrase_no_winner"],
                "source_rank_bins": ["1-500", "missing"],
                "polysemy_bands": ["low", "high"],
                "rows_per_cell": {
                    "manual_discovery_rows": 1,
                    "llm_discovery_rows": 1,
                    "locked_eval_rows": 1,
                },
                "bias_controls": ["balanced_quota_not_failure_weighted"],
            },
            {
                "lane_id": "targeted_curve_mechanism_lane",
                "lane_type": "targeted_curve_expansion",
                "purpose": "Test mechanisms.",
                "claim_supported": "mechanism_validation",
                "sampling_frame": "Curve queue.",
                "selection_method": "P0 only.",
                "priority_scope": ["P0"],
                "bias_controls": ["targeted_rows_cannot_estimate_real_world_frequency"],
            },
            {
                "lane_id": "negative_and_leakage_control_lane",
                "lane_type": "negative_control",
                "purpose": "Detect leakage.",
                "claim_supported": "sanity_check",
                "sampling_frame": "Control rows.",
                "selection_method": "Fixed quota.",
                "manual_discovery_rows": 2,
                "llm_discovery_rows": 2,
                "locked_eval_rows": 2,
                "bias_controls": ["control_failures_block_promotion_claims"],
            },
        ],
        "stage_plan": [
            {
                "stage_id": "stage_0_design_freeze",
                "entry_condition": "Inputs exist.",
                "exit_condition": "Design generated.",
            }
        ],
    }


def _curve_payload() -> dict[str, object]:
    return {
        "pair": "en-es",
        "decision": "curve_guided_expansion_plan_established",
        "expansion_queue": [
            _queue_row("P0", "phrase_no_winner", 4, 16, 8),
            _queue_row("P0", "positive_active", 3, 9, 5),
            _queue_row("P1", "shadow_negative", 2, 6, 3),
        ],
    }


def _queue_row(
    priority: str,
    case_type: str,
    manual: int,
    llm: int,
    locked: int,
) -> dict[str, object]:
    return {
        "priority": priority,
        "manual_case_type": case_type,
        "heuristic_group": "core_high_polysemy",
        "scorer_id": "tfidf_cosine",
        "source_rank_bin": "1-500",
        "polysemy_band": "high",
        "expansion_score": 0.8,
        "manual_discovery_rows": manual,
        "llm_discovery_rows": llm,
        "locked_eval_rows": locked,
        "reasons": ["strong_surface_curve_signal"],
        "triggers": ["help"],
    }


def _policy() -> dict[str, object]:
    return {
        "pair": "en-es",
        "policy_id": "test_policy",
        "acceptance": {
            "positive_allow_rate_min": 0.8,
            "negative_abstain_rate_min": 0.5,
            "representative_lane_required_for_promotion": True,
        },
    }


if __name__ == "__main__":
    unittest.main()
