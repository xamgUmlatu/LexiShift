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

from semantic_veto_sampling_stage1_materialization_en_es import (  # noqa: E402
    build_sampling_stage1_materialization_report,
    render_sampling_stage1_markdown,
)


class SemanticVetoSamplingStage1MaterializationTests(unittest.TestCase):
    def test_stage1_materializes_p0_packet_and_representative_frame_without_score_leakage(
        self,
    ) -> None:
        report, dataset, frame = build_sampling_stage1_materialization_report(
            sampling_design_payload=_sampling_design(),
            curve_plan_payload=_curve_plan(),
            difficulty_payload=_difficulty_payload(),
            generated_at="2026-05-05T00:00:00Z",
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(
            report["decision"],
            "sampling_stage1_materialized_with_representative_shortfall",
        )
        self.assertEqual(report["summary"]["target_locked_eval_rows"], 3)
        self.assertEqual(report["summary"]["available_representative_rows"], 2)
        self.assertEqual(report["summary"]["remaining_representative_rows_needed"], 1)
        self.assertEqual(report["summary"]["p0_curve_cell_count"], 2)
        self.assertEqual(report["summary"]["p0_manual_case_count"], 8)

        self.assertEqual(dataset["dataset_id"], "en_es_sampling_stage1_p0_manual_v1")
        self.assertEqual(dataset["manual_review_state"], "agent_draft_human_review_pending")
        self.assertEqual(len(dataset["families"]), 2)
        self.assertTrue(
            all(
                "agent_draft_human_review_pending"
                in case["slice_dimensions"]["manual_review_state"]
                for family in dataset["families"]
                for case in family["cases"]
            )
        )

        frame_rows = frame["rows"]
        self.assertEqual(len(frame_rows), 2)
        self.assertTrue(all(row["selection_used_scoring_fields"] is False for row in frame_rows))
        self.assertTrue(all(row["split"] == "locked_eval" for row in frame_rows))
        leaked_fields = {
            "predicted_decision",
            "product_outcome",
            "error_type",
            "active_score",
            "strongest_shadow_score",
            "phrase_control_score",
        }
        for row in frame_rows:
            self.assertTrue(leaked_fields.isdisjoint(row))

        markdown = render_sampling_stage1_markdown(report)
        self.assertIn("Semantic Veto Sampling Stage 1 Materialization", markdown)
        self.assertIn("Representative Frame", markdown)
        self.assertIn("P0 Manual Rows", markdown)

    def test_unknown_p0_trigger_is_review_not_silent_drop(self) -> None:
        curve_plan = _curve_plan()
        curve_plan["expansion_queue"].append(
            _queue_row(
                trigger="unknown",
                scorer_id="tfidf_cosine",
                manual_case_type="phrase_no_winner",
            )
        )
        report, dataset, _frame = build_sampling_stage1_materialization_report(
            sampling_design_payload=_sampling_design(),
            curve_plan_payload=curve_plan,
            difficulty_payload=_difficulty_payload(),
            generated_at="2026-05-05T00:00:00Z",
        )

        self.assertEqual(report["status"], "review")
        self.assertIn(
            "missing_p0_trigger_specs:unknown",
            report["summary"]["issues"],
        )
        self.assertEqual(dataset["dataset_id"], "en_es_sampling_stage1_p0_manual_v1")

    def test_representative_gap_rows_fill_shortfall_without_score_fields(self) -> None:
        report, _dataset, frame = build_sampling_stage1_materialization_report(
            sampling_design_payload=_sampling_design(),
            curve_plan_payload=_curve_plan(),
            difficulty_payload=_difficulty_payload(),
            representative_gap_payload=_representative_gap_payload(),
            generated_at="2026-05-05T00:00:00Z",
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["decision"], "sampling_stage1_materialized")
        self.assertEqual(report["summary"]["target_locked_eval_rows"], 3)
        self.assertEqual(report["summary"]["available_representative_rows"], 3)
        self.assertEqual(report["summary"]["base_representative_rows"], 2)
        self.assertEqual(report["summary"]["representative_gap_rows_added"], 1)
        self.assertEqual(report["summary"]["remaining_representative_rows_needed"], 0)
        self.assertEqual(
            report["summary"]["context_source_counts"][
                "agent_curated_corpus_like_app_candidate_contexts"
            ],
            1,
        )

        gap_rows = [
            row
            for row in frame["rows"]
            if row["context_source"] == "agent_curated_corpus_like_app_candidate_contexts"
        ]
        self.assertEqual(len(gap_rows), 1)
        self.assertEqual(gap_rows[0]["review_state"], "agent_draft_human_review_pending")
        self.assertTrue(gap_rows[0]["counts_toward_primary_representative_target"])
        leaked_fields = {
            "predicted_decision",
            "product_outcome",
            "error_type",
            "active_score",
            "strongest_shadow_score",
            "phrase_control_score",
        }
        self.assertTrue(leaked_fields.isdisjoint(gap_rows[0]))

    def test_filled_representative_gap_rows_are_not_counted_as_base_rows(self) -> None:
        difficulty_payload = _difficulty_payload()
        difficulty_payload["case_traces"].append(
            {
                "case_id": "case:filled-gap:001",
                "family_id": "family:gap",
                "lane_id": "representative_random_product_lane",
                "lane_type": "representative",
                "source_id": "corpus_sampled_app_candidate_contexts",
                "suite_id": "representative_gap_primary_v1",
                "context_source": "agent_curated_corpus_like_app_candidate_contexts",
                "review_state": "agent_draft_human_review_pending",
                "trigger": "change",
                "target_lemma": "cambio",
                "sentence": "The cashier gave me the wrong change.",
                "gold_decision": "abstain",
                "gold_winner_type": "shadow",
                "predicted_decision": "abstain",
                "product_outcome": "true_abstain",
                "active_score": 0.1,
                "strongest_shadow_score": 0.5,
            }
        )

        report, _dataset, frame = build_sampling_stage1_materialization_report(
            sampling_design_payload=_sampling_design(),
            curve_plan_payload=_curve_plan(),
            difficulty_payload=difficulty_payload,
            representative_gap_payload=_representative_gap_payload(),
            generated_at="2026-05-05T00:00:00Z",
        )

        self.assertEqual(report["summary"]["base_representative_rows"], 2)
        self.assertEqual(report["summary"]["representative_gap_rows_added"], 1)
        self.assertEqual(report["summary"]["available_representative_rows"], 3)
        self.assertEqual(len(frame["rows"]), 3)


def _sampling_design() -> dict[str, object]:
    return {
        "decision": "sampling_expansion_design_established",
        "methodology": {"random_seed": "unit_test_seed"},
        "lane_reports": [
            {
                "lane_id": "representative_random_product_lane",
                "lane_type": "representative_random",
                "locked_eval_rows": 3,
            },
            {
                "lane_id": "targeted_curve_mechanism_lane",
                "lane_type": "targeted_curve_expansion",
            },
        ],
    }


def _curve_plan() -> dict[str, object]:
    return {
        "pair": "en-es",
        "decision": "curve_guided_expansion_plan_established",
        "expansion_queue": [
            _queue_row(
                trigger="help",
                scorer_id="tfidf_cosine",
                manual_case_type="phrase_no_winner",
            ),
            _queue_row(
                trigger="particular",
                scorer_id="sentence_transformer_cosine",
                manual_case_type="phrase_no_winner",
            ),
            _queue_row(
                trigger="help",
                scorer_id="tfidf_cosine",
                manual_case_type="shadow_negative",
                priority="P1",
            ),
        ],
    }


def _queue_row(
    *,
    trigger: str,
    scorer_id: str,
    manual_case_type: str,
    priority: str = "P0",
) -> dict[str, object]:
    return {
        "priority": priority,
        "cell_id": f"cell:{trigger}:{scorer_id}:{manual_case_type}",
        "cell_split": "discovery",
        "manual_case_type": manual_case_type,
        "heuristic_group": "core_high_polysemy",
        "scorer_id": scorer_id,
        "source_rank_bin": "1-500",
        "polysemy_band": "high_10_plus",
        "shadow_contract": "limited",
        "manual_discovery_rows": 4,
        "llm_discovery_rows": 16,
        "locked_eval_rows": 8,
        "triggers": [trigger],
    }


def _difficulty_payload() -> dict[str, object]:
    return {
        "pair": "en-es",
        "decision": "difficulty_stratification_ready",
        "case_traces": [
            {
                "case_id": "case:ball:001",
                "family_id": "family:ball",
                "lane_id": "sentence_veto_v10_representative_proxy",
                "lane_type": "representative",
                "source_id": "sentence_veto_v10_current_policy",
                "suite_id": "sentence_veto_v10",
                "trigger": "ball",
                "target_lemma": "pelota",
                "sentence": "The goalkeeper punched the ball away.",
                "gold_decision": "replace",
                "gold_winner_type": "active",
                "source_trigger_rank_bin_en": "missing",
                "target_lemma_rank_bin_es": "missing",
                "metadata_gap_flags": ["missing_source_trigger_rank_en"],
                "slice_tags": ["clear_active"],
                "predicted_decision": "abstain",
                "product_outcome": "positive_abstain",
                "active_score": 0.0,
                "strongest_shadow_score": 0.0,
            },
            {
                "case_id": "case:plant:001",
                "family_id": "family:plant",
                "lane_id": "sentence_veto_v10_representative_proxy",
                "lane_type": "representative",
                "source_id": "sentence_veto_v10_current_policy",
                "suite_id": "sentence_veto_v10",
                "trigger": "plant",
                "target_lemma": "planta",
                "sentence": "The plant needs more light.",
                "gold_decision": "replace",
                "gold_winner_type": "active",
                "source_trigger_rank_bin_en": "1001-5000",
                "target_lemma_rank_bin_es": "1001-5000",
                "metadata_gap_flags": [],
                "slice_tags": ["clear_active"],
                "predicted_decision": "replace",
                "product_outcome": "positive_allow",
                "active_score": 0.2,
                "strongest_shadow_score": 0.0,
            },
            {
                "case_id": "case:stress:001",
                "lane_type": "stress",
                "trigger": "help",
                "target_lemma": "ayuda",
                "sentence": "I cannot help laughing.",
            },
        ],
    }


def _representative_gap_payload() -> dict[str, object]:
    return {
        "dataset_id": "unit_gap_rows",
        "source_id": "corpus_sampled_app_candidate_contexts",
        "source_class": "primary_corpus_proxy",
        "context_source": "agent_curated_corpus_like_app_candidate_contexts",
        "review_state": "agent_draft_human_review_pending",
        "counts_toward_primary_representative_target": True,
        "rows": [
            {
                "row_id": "gap:ball:001",
                "slot_id": "gap-slot:001",
                "family_id": "family:ball",
                "trigger": "ball",
                "target_lemma": "pelota",
                "sentence": "A fan caught the foul ball.",
                "gold_decision": "replace",
                "gold_winner": "active:ball",
                "gold_winner_type": "active",
                "slice_tags": ["representative_gap_primary"],
                "predicted_decision": "replace",
                "active_score": 0.9,
            }
        ],
    }


if __name__ == "__main__":
    unittest.main()
