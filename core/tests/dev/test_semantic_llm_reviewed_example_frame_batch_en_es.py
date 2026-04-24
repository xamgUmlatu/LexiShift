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

from semantic_llm_example_frame_contract_en_es import (  # noqa: E402
    build_example_frame_contract_report,
)
from semantic_llm_reviewed_example_frame_batch_en_es import (  # noqa: E402
    build_reviewed_example_frame_bundle,
)


class SemanticLlmReviewedExampleFrameBatchTests(unittest.TestCase):
    def test_reviewed_example_frame_batch_is_contract_complete(self) -> None:
        queue_payload, dataset_payload = _sample_inputs()
        bundle = build_reviewed_example_frame_bundle(
            queue_payload=queue_payload,
            dataset_payload=dataset_payload,
            run_id="test",
            generated_at="2026-04-25T12:00:00Z",
        )

        normalized = bundle["normalized_batch"]
        self.assertEqual(normalized["row_count"], 3)
        relation_types = {row["relation_type"] for row in normalized["rows"]}
        self.assertEqual(
            relation_types,
            {"anchor_cue", "shadow_candidate", "phrase_control_example"},
        )

        contract_report = build_example_frame_contract_report(
            normalized,
            generated_at="2026-04-25T12:00:00Z",
        )
        self.assertEqual(contract_report["status"], "ok")
        self.assertTrue(contract_report["summary"]["contract_complete"])


def _sample_inputs() -> tuple[dict[str, object], dict[str, object]]:
    family = {
        "family_id": "fam:check",
        "trigger": "check",
        "active": {
            "sense_id": "fam:check:active",
            "target_lemma": "cheque",
            "canonical_pos": "noun",
            "evidence_views": {"all_evidence_text": "bank check"},
        },
        "shadows": [
            {
                "sense_id": "fam:check:shadow",
                "target_lemma": "revisar",
                "canonical_pos": "verb",
                "evidence_views": {"all_evidence_text": "inspect"},
            }
        ],
        "cases": [
            {
                "case_id": "check:001",
                "sentence": "The check was signed and deposited yesterday.",
                "source_phrase": "check",
                "gold_winner": "fam:check:active",
                "gold_decision": "replace",
                "slice_tags": ["clear_active"],
            },
            {
                "case_id": "check:002",
                "sentence": "They will check the records carefully tonight.",
                "source_phrase": "check",
                "gold_winner": "fam:check:shadow",
                "gold_decision": "abstain",
                "slice_tags": ["clear_shadow"],
            },
            {
                "case_id": "check:003",
                "sentence": "Please check in at the front desk.",
                "source_phrase": "check",
                "gold_winner": "none",
                "gold_decision": "abstain",
                "slice_tags": ["phrase_control"],
            },
        ],
    }
    return (
        {"queue_id": "test", "families": [{"family_id": "fam:check", "trigger": "check"}]},
        {
            "schema_version": 1,
            "pair": "en-es",
            "dataset_id": "test_dataset",
            "families": [family],
        },
    )


if __name__ == "__main__":
    unittest.main()
