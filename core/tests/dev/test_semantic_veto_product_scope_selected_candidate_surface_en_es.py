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

from semantic_veto_product_scope_selected_candidate_surface_en_es import (  # noqa: E402
    build_selected_candidate_surface_report,
    render_selected_candidate_surface_markdown,
    select_candidate_specs,
)


class SemanticVetoProductScopeSelectedCandidateSurfaceTests(unittest.TestCase):
    def test_selects_named_candidates_and_encodes_candidate_id_as_scorer(self) -> None:
        specs = select_candidate_specs(_bakeoff())

        reasons = {spec["selection_reason"] for spec in specs}
        self.assertIn("best_product_rank", reasons)
        self.assertIn("current_v3_like", reasons)
        self.assertIn("tfidf_best_by_scorer", reasons)

        report = build_selected_candidate_surface_report(
            bakeoff_payload=_bakeoff(),
            candidate_reports=[
                {
                    "candidate_id": "best_product_rank_st",
                    "selection_reason": "best_product_rank",
                    "candidate": _candidate("sentence_transformer_cosine"),
                    "report": {"row_results": [_row("positive", "replace", "replace")]},
                },
                {
                    "candidate_id": "tfidf_best",
                    "selection_reason": "tfidf_best_by_scorer",
                    "candidate": _candidate("tfidf_cosine"),
                    "report": {"row_results": [_row("negative", "abstain", "replace")]},
                },
            ],
            generated_at="2026-05-09T00:00:00Z",
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["summary"]["candidate_count"], 2)
        self.assertEqual(report["summary"]["row_result_count"], 2)
        by_case = {row["case_id"]: row for row in report["row_results"]}
        self.assertEqual(by_case["positive"]["scorer_id"], "best_product_rank_st")
        self.assertEqual(by_case["negative"]["error_type"], "harmful_replace")

        markdown = render_selected_candidate_surface_markdown(report)
        self.assertIn("Selected Candidate Surface", markdown)
        self.assertIn("best_product_rank_st", markdown)


def _bakeoff() -> dict[str, object]:
    return {
        "pair": "en-es",
        "decision": "product_scope_algorithm_candidate_found",
        "summary": {
            "best_product_rank_row": _candidate("sentence_transformer_cosine", "best"),
            "safest_80pct_positive_row": _candidate("sentence_transformer_cosine", "safe"),
            "high_recall_soft_assist_row": _candidate("tfidf_cosine", "high-recall"),
            "current_policy_like_rows": [_candidate("sentence_transformer_cosine", "current")],
            "best_by_scorer": [_candidate("tfidf_cosine", "tfidf-best")],
        },
    }


def _candidate(scorer_id: str, label: str = "config") -> dict[str, object]:
    return {
        "config_id": f"{scorer_id}:{label}",
        "scorer_id": scorer_id,
        "context_view": "masked_sentence",
        "evidence_view": "all_evidence_text",
        "phrase_control_mode": "noun_family_frame_guard",
        "active_rescue_mode": "off",
        "min_active_score": 0.0,
        "min_margin": 0.0,
    }


def _row(case_id: str, gold: str, predicted: str) -> dict[str, object]:
    return {
        "case_id": case_id,
        "family_id": "family",
        "gold_decision": gold,
        "predicted_decision": predicted,
    }


if __name__ == "__main__":
    unittest.main()
