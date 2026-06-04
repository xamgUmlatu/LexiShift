from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest


CORE_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = CORE_ROOT.parent
SCRIPTS_ROOT = REPO_ROOT / "scripts" / "testing"
for candidate in (str(SCRIPTS_ROOT),):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from semantic_routing_sentence_veto_support import load_sentence_veto_dataset  # noqa: E402
from semantic_veto_deferred_mapping_review_fix_en_es import (  # noqa: E402
    DEFAULT_DATASET_ID,
    build_deferred_mapping_review_fix_report,
    render_deferred_mapping_review_fix_markdown,
)


class SemanticVetoDeferredMappingReviewFixTests(unittest.TestCase):
    def test_builds_fixed_packet_without_trusting_rows(self) -> None:
        report, dataset = build_deferred_mapping_review_fix_report(
            audit_payload={
                "decision": "deferred_mapping_audit_complete",
                "mapping_rows": [
                    {
                        "mapping_id": "bar->cercar",
                        "audit_status": "salvageable_with_corrected_active_sense",
                    },
                    {
                        "mapping_id": "offset->distancia",
                        "audit_status": "salvageable_with_corrected_active_sense",
                    },
                    {
                        "mapping_id": "demand->deducción",
                        "audit_status": "reject_mapping_source_target_mismatch",
                    },
                ],
            },
            generated_at="2026-05-07T00:00:00Z",
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(
            report["decision"],
            "deferred_mapping_review_fix_ready_for_user_review",
        )
        self.assertEqual(dataset["dataset_id"], DEFAULT_DATASET_ID)
        self.assertEqual(report["summary"]["fixed_family_count"], 3)
        self.assertEqual(report["summary"]["fixed_case_count"], 15)
        self.assertEqual(report["summary"]["trusted_case_count"], 0)
        self.assertEqual(
            report["summary"]["case_type_counts"],
            {"phrase_no_winner": 3, "positive_active": 6, "shadow_negative": 6},
        )
        self.assertTrue(all(report["e2e_checks"].values()))

        family_ids = {family["family_id"] for family in dataset["families"]}
        self.assertIn("en-es:full-family-deferred-review-fix:bar:cercar", family_ids)
        self.assertIn("en-es:full-family-deferred-review-fix:offset:distancia", family_ids)
        self.assertIn("en-es:full-family-deferred-review-fix:crack:grieta", family_ids)
        self.assertFalse(any(family["trigger"] == "demand" for family in dataset["families"]))

        rows = {
            (family["trigger"], family["active"]["target_lemma"]): family
            for family in dataset["families"]
        }
        crack_metadata = rows[("crack", "grieta")]["repair_metadata"]
        self.assertEqual(crack_metadata["replaces_rejected_mapping"], "demand->deducción")
        self.assertIn("zipf_4_to_5_common", crack_metadata["source_cell_id"])

        with tempfile.TemporaryDirectory() as tmpdir:
            dataset_path = Path(tmpdir) / "dataset.json"
            dataset_path.write_text(
                json.dumps(dataset, ensure_ascii=False),
                encoding="utf-8",
            )
            loaded = load_sentence_veto_dataset(dataset_path)

        self.assertEqual(len(loaded["families"]), 3)
        markdown = render_deferred_mapping_review_fix_markdown(report)
        self.assertIn("Rows are agent-reviewed and repaired", markdown)
        self.assertIn("demand->deducción", markdown)

    def test_missing_audit_status_blocks_report(self) -> None:
        report, _dataset = build_deferred_mapping_review_fix_report(
            audit_payload={
                "decision": "deferred_mapping_audit_complete",
                "mapping_rows": [
                    {
                        "mapping_id": "bar->cercar",
                        "audit_status": "salvageable_with_corrected_active_sense",
                    }
                ],
            },
            generated_at="2026-05-07T00:00:00Z",
        )

        self.assertEqual(report["status"], "review")
        self.assertFalse(report["e2e_checks"]["salvageable_audit_rows_repaired"])
        self.assertFalse(report["e2e_checks"]["rejected_mapping_not_repaired_as_same_pair"])


if __name__ == "__main__":
    unittest.main()
