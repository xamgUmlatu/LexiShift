from __future__ import annotations

from pathlib import Path
import sys
import unittest


CORE_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = CORE_ROOT.parent
SCRIPTS_ROOT = REPO_ROOT / "scripts" / "testing"
for candidate in (str(SCRIPTS_ROOT),):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from semantic_veto_full_family_score_surface_en_es import (  # noqa: E402
    build_full_family_score_surface_report,
    render_full_family_score_surface_markdown,
)


class SemanticVetoFullFamilyScoreSurfaceTests(unittest.TestCase):
    def test_reports_source_band_case_type_metrics_for_each_scorer(self) -> None:
        report = build_full_family_score_surface_report(
            authoring_payload={
                "pair": "en-es",
                "decision": "full_family_manual_packet_ready_for_scoring",
                "summary": {
                    "dataset_family_count": 2,
                    "dataset_case_count": 4,
                    "draft_review_state": "agent_draft_human_review_pending",
                    "source_band_case_counts": {
                        "zipf_3_to_4_mid": 2,
                        "zipf_below_3_rare": 2,
                    },
                    "case_type_counts": {
                        "positive_active": 2,
                        "phrase_no_winner": 2,
                    },
                },
            },
            score_sources=[
                {"source_id": "tfidf_cosine", "report": _score_report("tfidf_cosine")},
                {
                    "source_id": "sentence_transformer_cosine",
                    "report": _score_report("sentence_transformer_cosine"),
                },
            ],
            stage1_reference=_stage1_reference(),
            generated_at="2026-05-06T00:00:00Z",
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["decision"], "full_family_score_surface_established")
        source_rows = report["breakdowns"]["scorer_x_source_band"]
        tfidf_mid = _find(
            source_rows,
            scorer_id="tfidf_cosine",
            source_zipf_band_en="zipf_3_to_4_mid",
        )
        self.assertEqual(tfidf_mid["cases"], 2)
        self.assertEqual(tfidf_mid["positive_allow_rate"], 1.0)
        self.assertEqual(tfidf_mid["phrase_no_winner_abstain_rate"], 1.0)

        st_rare = _find(
            source_rows,
            scorer_id="sentence_transformer_cosine",
            source_zipf_band_en="zipf_below_3_rare",
        )
        self.assertEqual(st_rare["harmful_replace_count"], 1)
        self.assertEqual(st_rare["false_abstain_count"], 1)
        self.assertEqual(
            report["summary"]["stage1_reference"]["comparison_note"],
            "orientation_only_different_dataset_and_policy_modes",
        )

        markdown = render_full_family_score_surface_markdown(report)
        self.assertIn("Full-Family Score Surface", markdown)
        self.assertIn("Source Band", markdown)
        self.assertIn("stage1_representative_reference", markdown)


def _score_report(scorer_id: str) -> dict[str, object]:
    rare_positive_prediction = (
        "abstain" if scorer_id == "sentence_transformer_cosine" else "replace"
    )
    rare_phrase_prediction = "replace" if scorer_id == "sentence_transformer_cosine" else "abstain"
    return {
        "status": "ok",
        "config": {"scorer_id": scorer_id},
        "row_results": [
            _row("mid-positive", "replace", "replace", "positive_active", "zipf_3_to_4_mid"),
            _row("mid-phrase", "abstain", "abstain", "phrase_no_winner", "zipf_3_to_4_mid"),
            _row(
                "rare-positive",
                "replace",
                rare_positive_prediction,
                "positive_active",
                "zipf_below_3_rare",
            ),
            _row(
                "rare-phrase",
                "abstain",
                rare_phrase_prediction,
                "phrase_no_winner",
                "zipf_below_3_rare",
            ),
        ],
    }


def _row(
    case_id: str,
    gold_decision: str,
    predicted_decision: str,
    case_type: str,
    source_band: str,
) -> dict[str, object]:
    return {
        "case_id": case_id,
        "family_id": "family",
        "trigger": "sample",
        "sentence": "sample sentence",
        "gold_decision": gold_decision,
        "predicted_decision": predicted_decision,
        "gold_winner_type": "active" if gold_decision == "replace" else "none",
        "predicted_winner_type": "active" if predicted_decision == "replace" else "",
        "active_score": 0.5,
        "strongest_shadow_score": 0.1,
        "margin": 0.4,
        "slice_dimensions": {
            "manual_case_type": [case_type],
            "source_zipf_band_en": [source_band],
            "target_zipf_band_es": ["zipf_4_to_5_common"],
            "polysemy_band": ["low_1_to_3"],
            "pos_shape": ["single_sense"],
            "shadow_contract": ["not_applicable"],
            "manual_review_state": ["agent_draft_human_review_pending"],
        },
    }


def _stage1_reference() -> dict[str, object]:
    return {
        "decision": "stage1_representative_current_policy_scored",
        "dataset_path": "docs/test_inputs/semantic_routing_cases/en_es_sampling_stage1_representative_v1.json",
        "config": {
            "scorer_id": "tfidf_cosine",
            "phrase_control_mode": "noun_family_frame_guard",
            "active_rescue_mode": "sense_label_near_tie_active_rescue",
        },
        "summary": {
            "cases_total": 120,
            "decision_accuracy": 0.66,
            "replace_recall": 0.25,
            "harmful_replace_rate": 0.0,
            "false_abstain_rate": 0.75,
            "harmful_replace_count": 0,
            "false_abstain_count": 40,
        },
    }


def _find(rows: list[dict[str, object]], **criteria: str) -> dict[str, object]:
    for row in rows:
        if all(row.get(key) == value for key, value in criteria.items()):
            return row
    raise AssertionError(f"missing row {criteria}")


if __name__ == "__main__":
    unittest.main()
