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

from semantic_veto_llm_data_priority_scan_en_es import (  # noqa: E402
    FORBIDDEN_RANKING_FIELDS,
    build_llm_data_priority_scan_report,
    render_llm_data_priority_scan_markdown,
)


class SemanticVetoLlmDataPriorityScanTests(unittest.TestCase):
    def test_priority_scan_uses_programmatic_features_and_separates_labels(self) -> None:
        report = build_llm_data_priority_scan_report(
            difficulty_payload=_difficulty_payload(),
            top_n=2,
            generated_at="2026-05-06T00:00:00Z",
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["decision"], "llm_data_priority_scan_established")
        self.assertTrue(report["e2e_checks"]["forbidden_fields_absent_from_programmatic_features"])
        self.assertTrue(report["e2e_checks"]["validation_shadow_kept_separate"])
        self.assertEqual(report["summary"]["candidate_pair_count"], 3)

        top_row = report["top_priority_rows"][0]
        self.assertEqual(top_row["trigger"], "help")
        self.assertIn("generate_phrase_rows", top_row["priority_reasons"])
        self.assertGreater(top_row["recommended_llm_packet"]["phrase_rows"], 0)
        self.assertGreater(top_row["validation_shadow"]["observed_failure_count"], 0)
        self.assertTrue(set(top_row["programmatic_features"]).isdisjoint(FORBIDDEN_RANKING_FIELDS))

        markdown = render_llm_data_priority_scan_markdown(report)
        self.assertIn("LLM Data Priority Scan", markdown)
        self.assertIn("Feature Guardrails", markdown)
        self.assertIn("Recommended LLM Packets", markdown)

    def test_gold_and_product_outcomes_do_not_change_priority_scores(self) -> None:
        payload = {
            "pair": "en-es",
            "decision": "difficulty_stratification_ready",
            "case_traces": [
                _row(
                    case_id="case:a:001",
                    trigger="alpha",
                    target="alfa",
                    product_outcome="positive_allow",
                ),
                _row(
                    case_id="case:b:001",
                    trigger="beta",
                    target="beta",
                    product_outcome="negative_allow",
                ),
            ],
        }

        report = build_llm_data_priority_scan_report(
            difficulty_payload=payload,
            top_n=2,
            generated_at="2026-05-06T00:00:00Z",
        )

        by_trigger = {row["trigger"]: row for row in report["priority_rows"]}
        self.assertEqual(
            by_trigger["alpha"]["scored_context_llm_data_need"],
            by_trigger["beta"]["scored_context_llm_data_need"],
        )
        self.assertEqual(
            by_trigger["alpha"]["static_llm_data_need"],
            by_trigger["beta"]["static_llm_data_need"],
        )
        self.assertEqual(by_trigger["alpha"]["validation_shadow"]["observed_failure_count"], 0)
        self.assertEqual(by_trigger["beta"]["validation_shadow"]["observed_failure_count"], 1)


def _difficulty_payload() -> dict[str, object]:
    return {
        "pair": "en-es",
        "decision": "difficulty_stratification_ready",
        "case_traces": [
            _row(
                case_id="case:help:001",
                trigger="help",
                target="ayuda",
                sentence="Help, I dropped the glass.",
                source_rank=180.0,
                target_rank=600.0,
                wordnet_sense_count=16,
                wordnet_pos_count=3,
                translation_candidate_count=12,
                active_evidence_count=1,
                shadow_evidence_count=1,
                phrase_control_evidence_count=0,
                active_score=0.03,
                shadow_score=0.025,
                phrase_score=0.04,
                product_outcome="negative_allow",
            ),
            _row(
                case_id="case:help:002",
                trigger="help",
                target="ayuda",
                sentence="I need help with this box.",
                source_rank=180.0,
                target_rank=600.0,
                wordnet_sense_count=16,
                wordnet_pos_count=3,
                translation_candidate_count=12,
                active_evidence_count=1,
                shadow_evidence_count=1,
                phrase_control_evidence_count=0,
                active_score=0.02,
                shadow_score=0.03,
                phrase_score=0.025,
                product_outcome="positive_abstain",
            ),
            _row(
                case_id="case:plant:001",
                trigger="plant",
                target="planta",
                sentence="The plant needs water.",
                source_rank=4200.0,
                target_rank=None,
                wordnet_sense_count=7,
                wordnet_pos_count=2,
                translation_candidate_count=4,
                active_evidence_count=4,
                shadow_evidence_count=4,
                phrase_control_evidence_count=4,
                active_score=0.42,
                shadow_score=0.12,
                phrase_score=0.02,
                product_outcome="positive_allow",
            ),
            _row(
                case_id="case:yes:001",
                trigger="yes",
                target="sí",
                sentence="Yes, that was the right answer.",
                source_rank=90.0,
                target_rank=80.0,
                wordnet_sense_count=1,
                wordnet_pos_count=1,
                translation_candidate_count=2,
                active_evidence_count=4,
                shadow_evidence_count=0,
                phrase_control_evidence_count=0,
                active_score=0.15,
                shadow_score=0.01,
                phrase_score=0.14,
                product_outcome="negative_allow",
            ),
        ],
    }


def _row(
    *,
    case_id: str,
    trigger: str,
    target: str,
    sentence: str = "A neutral sentence.",
    source_rank: float | None = 100.0,
    target_rank: float | None = 100.0,
    wordnet_sense_count: int = 10,
    wordnet_pos_count: int = 2,
    translation_candidate_count: int = 8,
    active_evidence_count: int = 1,
    shadow_evidence_count: int = 1,
    phrase_control_evidence_count: int = 1,
    active_score: float = 0.03,
    shadow_score: float = 0.02,
    phrase_score: float = 0.01,
    product_outcome: str = "positive_allow",
) -> dict[str, object]:
    return {
        "case_id": case_id,
        "family_id": f"family:{trigger}:{target}",
        "lane_type": "representative",
        "source_id": "unit",
        "trigger": trigger,
        "target_lemma": target,
        "sentence": sentence,
        "source_trigger_rank_en": source_rank,
        "target_lemma_rank_es": target_rank,
        "wordnet_sense_count": wordnet_sense_count,
        "wordnet_pos_count": wordnet_pos_count,
        "translation_candidate_count": translation_candidate_count,
        "active_evidence_count": active_evidence_count,
        "shadow_evidence_count": shadow_evidence_count,
        "phrase_control_evidence_count": phrase_control_evidence_count,
        "admitted_shadow_count": shadow_evidence_count,
        "active_score": active_score,
        "strongest_shadow_score": shadow_score,
        "phrase_control_score": phrase_score,
        "gold_decision": "replace",
        "gold_winner_type": "active",
        "manual_case_type": "positive_active",
        "predicted_decision": "replace",
        "product_outcome": product_outcome,
        "error_type": product_outcome,
    }


if __name__ == "__main__":
    unittest.main()
