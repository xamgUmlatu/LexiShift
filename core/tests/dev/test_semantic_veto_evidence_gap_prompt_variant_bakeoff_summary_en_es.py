from __future__ import annotations

from pathlib import Path
import sys
import unittest


CORE_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = CORE_ROOT.parent
SCRIPTS_ROOT = REPO_ROOT / "scripts" / "testing"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from semantic_veto_evidence_gap_prompt_variant_bakeoff_summary_en_es import (  # noqa: E402
    build_prompt_variant_bakeoff_summary_report,
    render_prompt_variant_bakeoff_summary_markdown,
)


class SemanticVetoEvidenceGapPromptVariantBakeoffSummaryTests(unittest.TestCase):
    def test_summarizes_generation_admission_and_primary_postprocess_view(self) -> None:
        generation_payloads = {
            variant_id: _generation_payload(variant_id, input_tokens=1000, output_tokens=500)
            for variant_id in _variants()
        }
        admission_payloads = {
            variant_id: _admission_payload(rejected_item_count=0) for variant_id in _variants()
        }
        admission_payloads["v6_pos_diversity"] = _admission_payload(rejected_item_count=1)
        postprocess_payloads = {
            "v5_refresh_control": _postprocess_payload(0.73, harmful=0, false_abstains=24),
            "v6_pos_only": _postprocess_payload(0.68, harmful=2, false_abstains=27),
            "v6_diversity_only": _postprocess_payload(0.67, harmful=2, false_abstains=28),
            "v6_pos_diversity": _postprocess_payload(0.68, harmful=1, false_abstains=28),
        }

        report = build_prompt_variant_bakeoff_summary_report(
            generation_payloads=generation_payloads,
            admission_payloads=admission_payloads,
            postprocess_payloads=postprocess_payloads,
            generated_at="2026-05-09T00:00:00Z",
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["summary"]["variant_count"], 4)
        self.assertEqual(report["summary"]["best_primary_variant_id"], "v5_refresh_control")
        self.assertEqual(report["summary"]["issue_count"], 1)
        self.assertEqual(report["summary"]["issues"][0]["severity"], "warn")

        v5 = next(row for row in report["variants"] if row["variant_id"] == "v5_refresh_control")
        self.assertEqual(v5["primary_view"]["view_id"], "no_high_eval_overlap_sentence_only")
        self.assertGreater(v5["estimated_cost_usd"], 0)

        markdown = render_prompt_variant_bakeoff_summary_markdown(report)
        self.assertIn("Prompt Variant Bakeoff", markdown)
        self.assertIn("v5_refresh_control", markdown)
        self.assertIn("v6_pos_diversity", markdown)


def _variants() -> tuple[str, ...]:
    return (
        "v5_refresh_control",
        "v6_pos_only",
        "v6_diversity_only",
        "v6_pos_diversity",
    )


def _generation_payload(
    variant_id: str, *, input_tokens: int, output_tokens: int
) -> dict[str, object]:
    return {
        "status": "ok",
        "prompt_id": f"prompt:{variant_id}",
        "summary": {
            "selected_request_count": 24,
            "accepted_response_count": 24,
            "accepted_generated_item_count": 48,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
        },
    }


def _admission_payload(*, rejected_item_count: int) -> dict[str, object]:
    return {
        "status": "ok" if rejected_item_count == 0 else "review",
        "summary": {
            "admitted_item_count": 48 - rejected_item_count,
            "coverage_shortfall_count": rejected_item_count,
            "rejected_item_count": rejected_item_count,
        },
    }


def _postprocess_payload(
    accuracy: float, *, harmful: int, false_abstains: int
) -> dict[str, object]:
    primary = {
        "view_id": "no_high_eval_overlap_sentence_only",
        "item_count": 46,
        "generated_active_only": {
            "decision_accuracy": accuracy,
            "replace_recall": 0.5,
            "harmful_replace_count": harmful,
            "false_abstain_count": false_abstains,
        },
        "case_change_counts": {
            "fixed": 21,
            "regressed": harmful,
        },
    }
    return {
        "status": "ok",
        "summary": {
            "active_item_count": 48,
            "family_count": 24,
            "high_eval_overlap_count": 2,
            "medium_eval_overlap_count": 5,
            "pos_weak_count": 1,
            "definition_like_count": 0,
            "target_lemma_in_note_count": 0,
            "model_source_pos_frame_count": 48,
            "model_topic_frame_count": 48,
            "high_shadow_confusable_count": 0,
        },
        "view_scores": [
            {
                "view_id": "sentence_only_all",
                "item_count": 48,
                "generated_active_only": {
                    "decision_accuracy": accuracy,
                    "replace_recall": 0.5,
                    "harmful_replace_count": harmful,
                    "false_abstain_count": false_abstains,
                },
                "case_change_counts": {"fixed": 21, "regressed": harmful},
            },
            primary,
        ],
    }


if __name__ == "__main__":
    unittest.main()
