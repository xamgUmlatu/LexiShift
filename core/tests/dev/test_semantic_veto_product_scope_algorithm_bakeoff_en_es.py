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

from semantic_veto_product_scope_algorithm_bakeoff_en_es import (  # noqa: E402
    build_product_scope_algorithm_bakeoff_report,
    render_product_scope_algorithm_bakeoff_markdown,
)
from semantic_veto_product_scope_filter_en_es import (  # noqa: E402
    DIAGNOSTIC_LABEL_PRESERVATION,
    PRODUCT_SCOPE_BROWSER_SOFT_ASSIST,
    classify_semantic_veto_product_scope,
    filter_sentence_veto_dataset_for_product_scope,
)


class SemanticVetoProductScopeAlgorithmBakeoffTests(unittest.TestCase):
    def test_product_scope_filter_excludes_internal_project_code_labels(self) -> None:
        filtered, summary = filter_sentence_veto_dataset_for_product_scope(_dataset())

        self.assertEqual(summary["scope_id"], PRODUCT_SCOPE_BROWSER_SOFT_ASSIST)
        self.assertEqual(summary["original_case_count"], 3)
        self.assertEqual(summary["retained_case_count"], 2)
        self.assertEqual(summary["excluded_case_count"], 1)
        self.assertEqual(
            summary["excluded_scope_counts"][DIAGNOSTIC_LABEL_PRESERVATION],
            1,
        )
        retained_ids = [
            case["case_id"] for family in filtered["families"] for case in family["cases"]
        ]
        self.assertEqual(retained_ids, ["positive", "real-negative"])

        label_scope = classify_semantic_veto_product_scope(
            {"sentence": "The dashboard listed Change as an internal project code."}
        )
        self.assertFalse(label_scope["include_in_product_scope"])

    def test_bakeoff_sweeps_thresholds_phrase_and_rescue_on_product_scope_rows(self) -> None:
        _filtered, scope_summary = filter_sentence_veto_dataset_for_product_scope(_dataset())
        report = build_product_scope_algorithm_bakeoff_report(
            policy_payload=_policy(),
            trace_sources=[_trace_source()],
            product_scope_summary=scope_summary,
            min_active_scores=(0.05,),
            min_margins=(0.0,),
            phrase_control_modes=("off", "noun_family_frame_guard"),
            active_rescue_modes=("off", "sense_label_near_tie_active_rescue"),
            generated_at="2026-05-09T00:00:00Z",
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["decision"], "product_scope_algorithm_candidate_found")
        self.assertEqual(report["e2e_checks"]["diagnostic_label_rows_excluded"], 1)
        self.assertEqual(report["summary"]["candidate_row_count"], 4)
        best = report["summary"]["best_product_rank_row"]
        self.assertEqual(best["phrase_control_mode"], "noun_family_frame_guard")
        self.assertEqual(best["active_rescue_mode"], "sense_label_near_tie_active_rescue")
        self.assertEqual(best["positive_allow_rate"], 1.0)
        self.assertEqual(best["negative_abstain_rate"], 1.0)
        self.assertEqual(best["active_rescue_applied_count"], 1)
        self.assertEqual(best["phrase_preemption_applied_count"], 1)

        markdown = render_product_scope_algorithm_bakeoff_markdown(report)
        self.assertIn("Product-Scope Algorithm Bakeoff", markdown)
        self.assertIn("Diagnostic label rows excluded", markdown)


def _dataset() -> dict[str, object]:
    return {
        "schema_version": 1,
        "pair": "en-es",
        "dataset_id": "unit",
        "families": [
            {
                "family_id": "family",
                "trigger": "change",
                "active": {"sense_id": "active"},
                "cases": [
                    {
                        "case_id": "positive",
                        "sentence": "I need to change the schedule.",
                        "source_phrase": "change",
                        "gold_winner": "active",
                        "gold_decision": "replace",
                    },
                    {
                        "case_id": "diagnostic-label",
                        "sentence": "The dashboard listed Change as an internal project code.",
                        "source_phrase": "change",
                        "gold_winner": "none",
                        "gold_decision": "abstain",
                    },
                    {
                        "case_id": "real-negative",
                        "sentence": "The cashier handed me change.",
                        "source_phrase": "change",
                        "gold_winner": "none",
                        "gold_decision": "abstain",
                    },
                ],
            }
        ],
    }


def _policy() -> dict[str, object]:
    return {
        "schema_version": 1,
        "pair": "en-es",
        "acceptance": {
            "positive_allow_rate_min": 0.8,
            "negative_abstain_rate_min": 0.5,
            "utility_must_beat_lexical_baseline": True,
        },
        "utility_weights": {
            "positive_allow": 1.0,
            "positive_abstain": -0.4,
            "negative_abstain": 0.8,
            "negative_allow": -0.6,
        },
    }


def _trace_source() -> dict[str, object]:
    return {
        "source_id": "tfidf_fixture",
        "scorer_id": "tfidf_cosine",
        "context_view": "masked_sentence",
        "evidence_view": "all_evidence_text",
        "backup_evidence_view": "sense_label",
        "primary_report": {
            "config": {
                "scorer_id": "tfidf_cosine",
                "context_view": "masked_sentence",
                "evidence_view": "all_evidence_text",
            },
            "row_results": [
                _row("positive", "replace", active=0.06, shadow=0.02),
                _row("rescue-positive", "replace", active=0.04, shadow=0.03),
                _row("real-negative", "abstain", active=0.08, shadow=0.01, phrase=True),
                _row(
                    "diagnostic-label",
                    "abstain",
                    active=0.20,
                    shadow=0.0,
                    sentence="The dashboard listed Change as an internal project code.",
                ),
            ],
        },
        "backup_report": {
            "config": {
                "scorer_id": "tfidf_cosine",
                "context_view": "masked_sentence",
                "evidence_view": "sense_label",
            },
            "row_results": [
                _row("positive", "replace", active=0.06, shadow=0.02),
                _row("rescue-positive", "replace", active=0.70, shadow=0.10),
                _row("real-negative", "abstain", active=0.08, shadow=0.01, phrase=True),
                _row(
                    "diagnostic-label",
                    "abstain",
                    active=0.20,
                    shadow=0.0,
                    sentence="The dashboard listed Change as an internal project code.",
                ),
            ],
        },
    }


def _row(
    case_id: str,
    gold: str,
    *,
    active: float,
    shadow: float,
    phrase: bool = False,
    sentence: str | None = None,
) -> dict[str, object]:
    return {
        "case_id": case_id,
        "family_id": "family",
        "trigger": "change",
        "sentence": sentence or f"Fixture sentence for {case_id}.",
        "gold_decision": gold,
        "active_score": active,
        "strongest_shadow_score": shadow,
        "phrase_preemption_hit": phrase,
    }


if __name__ == "__main__":
    unittest.main()
