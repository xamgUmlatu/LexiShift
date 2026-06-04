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

from semantic_veto_trusted_seed_v2_band_performance_en_es import (  # noqa: E402
    build_trusted_seed_v2_band_performance_report,
    render_trusted_seed_v2_band_performance_markdown,
)


class SemanticVetoTrustedSeedV2BandPerformanceTests(unittest.TestCase):
    def test_reports_band_metrics_and_prior_deltas(self) -> None:
        tfidf = _score_report(
            scorer_id="tfidf_cosine",
            rows=[
                _row("c1", "break", "replace", "replace", "active", "positive_active"),
                _row("c2", "break", "abstain", "abstain", "shadow", "shadow_negative"),
                _row("c3", "bar", "replace", "abstain", "active", "positive_active"),
                _row("c4", "bar", "abstain", "abstain", "none", "phrase_no_winner"),
            ],
        )
        st = _score_report(
            scorer_id="sentence_transformer_cosine",
            rows=[
                _row("c1", "break", "replace", "replace", "active", "positive_active"),
                _row("c2", "break", "abstain", "abstain", "shadow", "shadow_negative"),
                _row("c3", "bar", "replace", "replace", "active", "positive_active"),
                _row("c4", "bar", "abstain", "replace", "none", "phrase_no_winner"),
            ],
        )
        report = build_trusted_seed_v2_band_performance_report(
            score_sources=[
                {"source_id": "tfidf_cosine", "report": tfidf},
                {"source_id": "sentence_transformer_cosine", "report": st},
            ],
            prior_surface={
                "methodology": {"row_scope": "agent_draft"},
                "summary": {
                    "review_state": "agent_draft_human_review_pending",
                    "overall_by_scorer": [
                        {
                            "scorer_id": "tfidf_cosine",
                            "cases": 20,
                            "decision_accuracy": 0.8,
                            "positive_allow_rate": 0.6,
                            "shadow_negative_abstain_rate": 1.0,
                            "phrase_no_winner_abstain_rate": 1.0,
                            "harmful_replace_count": 0,
                            "false_abstain_count": 4,
                        }
                    ],
                },
                "breakdowns": {"scorer_x_source_band": []},
            },
            generated_at="2026-05-07T00:00:00Z",
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["summary"]["unique_case_count"], 4)
        self.assertEqual(
            report["summary"]["case_type_counts"],
            {"phrase_no_winner": 1, "positive_active": 2, "shadow_negative": 1},
        )
        by_scorer = {row["scorer_id"]: row for row in report["summary"]["overall_by_scorer"]}
        self.assertEqual(by_scorer["tfidf_cosine"]["harmful_replace_count"], 0)
        self.assertEqual(by_scorer["tfidf_cosine"]["false_abstain_count"], 1)
        self.assertEqual(by_scorer["sentence_transformer_cosine"]["harmful_replace_count"], 1)
        self.assertEqual(by_scorer["sentence_transformer_cosine"]["false_abstain_count"], 0)

        source_band_rows = {
            (row["scorer_id"], row["source_zipf_band_en"]): row
            for row in report["breakdowns"]["scorer_x_source_band"]
        }
        self.assertEqual(
            source_band_rows[("tfidf_cosine", "zipf_5_plus_very_common")]["positive_allow_rate"],
            1.0,
        )
        self.assertEqual(
            source_band_rows[("tfidf_cosine", "zipf_4_to_5_common")]["positive_allow_rate"],
            0.0,
        )
        deltas = report["prior_comparison"]["overall_deltas"]
        self.assertEqual(deltas[0]["scorer_id"], "tfidf_cosine")
        self.assertAlmostEqual(deltas[0]["decision_accuracy_delta"], -0.05)

        markdown = render_trusted_seed_v2_band_performance_markdown(report)
        self.assertIn("Trusted Seed v2 Band Performance", markdown)
        self.assertIn("Prior Draft Comparison", markdown)

    def test_missing_rows_blocks_report(self) -> None:
        report = build_trusted_seed_v2_band_performance_report(
            score_sources=[
                {"source_id": "tfidf_cosine", "report": _score_report("tfidf_cosine", [])}
            ],
            generated_at="2026-05-07T00:00:00Z",
        )

        self.assertEqual(report["status"], "review")
        self.assertIn("no_rows_for_score_source:tfidf_cosine", report["summary"]["issues"])


def _score_report(scorer_id: str, rows: list[dict[str, object]]) -> dict[str, object]:
    return {
        "pair": "en-es",
        "dataset_id": "en_es_full_family_trusted_eval_seed_v2",
        "status": "ok",
        "config": {"scorer_id": scorer_id},
        "summary": {},
        "row_results": rows,
    }


def _row(
    case_id: str,
    trigger: str,
    gold_decision: str,
    predicted_decision: str,
    gold_winner_type: str,
    manual_case_type: str,
) -> dict[str, object]:
    source_band = "zipf_5_plus_very_common" if trigger == "break" else "zipf_4_to_5_common"
    return {
        "case_id": case_id,
        "family_id": f"fam:{trigger}",
        "trigger": trigger,
        "gold_decision": gold_decision,
        "predicted_decision": predicted_decision,
        "gold_winner_type": gold_winner_type,
        "predicted_winner_type": gold_winner_type,
        "slice_dimensions": {
            "approval_id": ["approval-a"],
            "manual_case_type": [manual_case_type],
            "source_zipf_band_en": [source_band],
            "target_zipf_band_es": ["zipf_3_to_4_mid"],
            "polysemy_band": ["high_10_plus"],
            "pos_shape": ["cross_pos_polysemy"],
            "trusted_seed_v2_status": ["unit"],
            "family_repair_status": ["unit"],
            "no_winner_subtype": [
                "metalinguistic_token"
                if manual_case_type == "phrase_no_winner"
                else "not_applicable"
            ],
            "context_source": ["unit"],
        },
    }


if __name__ == "__main__":
    unittest.main()
