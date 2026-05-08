from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest


CORE_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = CORE_ROOT.parent
SCRIPTS_ROOT = REPO_ROOT / "scripts" / "testing"
for candidate in (str(CORE_ROOT), str(SCRIPTS_ROOT)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from semantic_veto_sampling_stage1_representative_scoring_en_es import (  # noqa: E402
    build_stage1_representative_scoring_report,
    build_stage1_representative_sentence_veto_dataset,
    render_stage1_representative_scoring_markdown,
)


class SemanticVetoStage1RepresentativeScoringTests(unittest.TestCase):
    def test_builds_scoreable_dataset_from_frame_without_score_leakage(self) -> None:
        dataset, summary = build_stage1_representative_sentence_veto_dataset(
            base_dataset=_base_dataset(),
            representative_frame=_representative_frame(),
            generated_at="2026-05-06T00:00:00Z",
        )

        self.assertEqual(summary["status"], "ok")
        self.assertEqual(summary["case_count"], 2)
        self.assertEqual(summary["family_count"], 1)
        self.assertEqual(
            summary["context_source_counts"]["agent_curated_corpus_like_app_candidate_contexts"],
            1,
        )
        self.assertEqual(
            summary["review_state_counts"]["agent_draft_human_review_pending"],
            1,
        )

        family = dataset["families"][0]
        self.assertEqual(family["family_id"], "fam:bank")
        self.assertEqual(len(family["cases"]), 2)
        gap_case = family["cases"][1]
        self.assertEqual(gap_case["case_id"], "gap:bank:001")
        self.assertEqual(gap_case["gold_winner"], "sense:bank:financial")
        self.assertIn(
            "agent_curated_corpus_like_app_candidate_contexts",
            gap_case["slice_dimensions"]["context_source"],
        )
        leaked_fields = {
            "predicted_decision",
            "product_outcome",
            "error_type",
            "active_score",
            "strongest_shadow_score",
            "phrase_control_score",
        }
        for case in family["cases"]:
            self.assertTrue(leaked_fields.isdisjoint(case))

    def test_scores_dataset_with_current_config_and_preserves_context_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            dataset_path = Path(tmpdir) / "stage1_representative.json"
            dataset, summary = build_stage1_representative_sentence_veto_dataset(
                base_dataset=_base_dataset(),
                representative_frame=_representative_frame(),
                dataset_out_path=dataset_path,
                generated_at="2026-05-06T00:00:00Z",
            )
            dataset_path.write_text(__import__("json").dumps(dataset), encoding="utf-8")

            report = build_stage1_representative_scoring_report(
                dataset_summary=summary,
                dataset_path=dataset_path,
                source_config_report=_source_config_report(),
                generated_at="2026-05-06T00:00:00Z",
            )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["decision"], "stage1_representative_current_policy_scored")
        self.assertEqual(report["summary"]["cases_total"], 2)
        self.assertEqual(report["summary"]["dataset_case_count"], 2)
        self.assertEqual(len(report["row_results"]), 2)
        by_case = {row["case_id"]: row for row in report["row_results"]}
        self.assertEqual(
            by_case["gap:bank:001"]["context_source"],
            "agent_curated_corpus_like_app_candidate_contexts",
        )

        markdown = render_stage1_representative_scoring_markdown(report)
        self.assertIn("Stage 1 Representative Scoring", markdown)
        self.assertIn("Current-Policy Score", markdown)


def _base_dataset() -> dict[str, object]:
    return {
        "schema_version": 1,
        "pair": "en-es",
        "dataset_id": "unit_base",
        "families": [
            {
                "family_id": "fam:bank",
                "trigger": "bank",
                "active": {
                    "sense_id": "sense:bank:financial",
                    "target_lemma": "banco",
                    "canonical_pos": "noun",
                    "evidence_views": {
                        "sense_label": "financial bank",
                        "gloss_text": "institution that holds money",
                        "all_evidence_text": "financial bank | institution that holds money",
                    },
                },
                "shadows": [
                    {
                        "sense_id": "sense:bank:river",
                        "target_lemma": "orilla",
                        "canonical_pos": "noun",
                        "evidence_views": {
                            "sense_label": "river bank",
                            "gloss_text": "side of a river",
                            "all_evidence_text": "river bank | side of a river",
                        },
                    }
                ],
                "cases": [
                    {
                        "case_id": "base:bank:001",
                        "sentence": "The bank approved the loan.",
                        "source_phrase": "bank",
                        "gold_winner": "sense:bank:financial",
                        "gold_decision": "replace",
                        "slice_tags": ["clear_active"],
                        "slice_dimensions": {"winner_type": ["active"]},
                    }
                ],
            }
        ],
    }


def _representative_frame() -> dict[str, object]:
    return {
        "schema_version": 1,
        "pair": "en-es",
        "frame_id": "unit_frame",
        "summary": {"frame_fingerprint": "unit-fingerprint"},
        "rows": [
            {
                "frame_row_id": "frame:001",
                "source_case_id": "base:bank:001",
                "family_id": "fam:bank",
                "trigger": "bank",
                "sentence": "The bank approved the loan.",
                "gold_decision": "replace",
                "gold_winner_type": "active",
                "target_lemma": "banco",
                "context_source": "existing_sentence_veto_v10_representative_proxy",
                "source_id": "unit_source",
                "selected_for_locked_eval": True,
                "slice_tags": ["clear_active"],
            },
            {
                "frame_row_id": "frame:002",
                "source_case_id": "gap:bank:001",
                "family_id": "fam:bank",
                "trigger": "bank",
                "sentence": "The bank froze the card.",
                "gold_decision": "replace",
                "gold_winner": "sense:bank:financial",
                "gold_winner_type": "active",
                "target_lemma": "banco",
                "context_source": "agent_curated_corpus_like_app_candidate_contexts",
                "source_id": "corpus_sampled_app_candidate_contexts",
                "review_state": "agent_draft_human_review_pending",
                "selected_for_locked_eval": True,
                "slice_tags": ["representative_gap_primary", "clear_active"],
            },
        ],
    }


def _source_config_report() -> dict[str, object]:
    return {
        "config": {
            "scorer_id": "token_jaccard",
            "context_view": "raw_sentence",
            "evidence_view": "all_evidence_text",
            "min_active_score": 0.0,
            "min_margin": -1.0,
            "phrase_control_mode": "off",
            "active_rescue_mode": "off",
            "window_tokens": 4,
            "mask_token": "___",
        }
    }


if __name__ == "__main__":
    unittest.main()
