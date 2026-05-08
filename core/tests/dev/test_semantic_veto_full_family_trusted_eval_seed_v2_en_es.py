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
    build_deferred_mapping_review_fix_report,
)
from semantic_veto_full_family_repair_pilot_en_es import build_repaired_pilot_report  # noqa: E402
from semantic_veto_full_family_trusted_eval_seed_en_es import (  # noqa: E402
    APPROVAL_ID as REPAIRED_PILOT_APPROVAL_ID,
    build_trusted_eval_seed_report,
)
from semantic_veto_full_family_trusted_eval_seed_v2_en_es import (  # noqa: E402
    DEFERRED_FIX_APPROVAL_ID,
    DEFAULT_DATASET_ID,
    build_trusted_eval_seed_v2_report,
    render_trusted_eval_seed_v2_markdown,
)


class SemanticVetoFullFamilyTrustedEvalSeedV2Tests(unittest.TestCase):
    def test_combines_original_trusted_seed_with_approved_deferred_fix(self) -> None:
        _, repaired = build_repaired_pilot_report(generated_at="2026-05-07T00:00:00Z")
        _, trusted_seed = build_trusted_eval_seed_report(
            repaired_payload=repaired,
            generated_at="2026-05-07T00:00:00Z",
        )
        _, deferred_fix = build_deferred_mapping_review_fix_report(
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

        report, dataset = build_trusted_eval_seed_v2_report(
            trusted_seed_payload=trusted_seed,
            deferred_fix_payload=deferred_fix,
            generated_at="2026-05-07T00:00:00Z",
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(
            report["decision"],
            "full_family_trusted_eval_seed_v2_ready_for_scoring",
        )
        self.assertEqual(dataset["dataset_id"], DEFAULT_DATASET_ID)
        self.assertEqual(report["summary"]["trusted_family_count"], 10)
        self.assertEqual(report["summary"]["trusted_case_count"], 42)
        self.assertEqual(report["summary"]["newly_approved_family_count"], 3)
        self.assertEqual(report["summary"]["newly_approved_case_count"], 15)
        self.assertEqual(
            report["summary"]["case_type_counts"],
            {"phrase_no_winner": 10, "positive_active": 20, "shadow_negative": 12},
        )
        self.assertEqual(
            report["summary"]["approval_case_counts"][REPAIRED_PILOT_APPROVAL_ID],
            27,
        )
        self.assertEqual(
            report["summary"]["approval_case_counts"][DEFERRED_FIX_APPROVAL_ID],
            15,
        )
        self.assertTrue(all(report["e2e_checks"].values()))

        family_ids = {family["family_id"] for family in dataset["families"]}
        self.assertIn("en-es:full-family-deferred-review-fix:bar:cercar", family_ids)
        self.assertIn("en-es:full-family-deferred-review-fix:offset:distancia", family_ids)
        self.assertIn("en-es:full-family-deferred-review-fix:crack:grieta", family_ids)
        self.assertFalse(any(family["trigger"] == "demand" for family in dataset["families"]))

        cases = [case for family in dataset["families"] for case in family["cases"]]
        self.assertTrue(all(case["human_review_status"] == "approved_by_user" for case in cases))
        self.assertTrue(all(case["row_quality_status"] == "trusted" for case in cases))
        self.assertTrue(
            all(case["slice_dimensions"]["dataset_lane"] == [DEFAULT_DATASET_ID] for case in cases)
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            dataset_path = Path(tmpdir) / "dataset.json"
            dataset_path.write_text(json.dumps(dataset, ensure_ascii=False), encoding="utf-8")
            loaded = load_sentence_veto_dataset(dataset_path)

        self.assertEqual(len(loaded["families"]), 10)
        markdown = render_trusted_eval_seed_v2_markdown(report)
        self.assertIn("Trusted Eval Seed v2", markdown)
        self.assertIn("two explicit approval ids", markdown)
        self.assertIn("demand->deducción", markdown)


if __name__ == "__main__":
    unittest.main()
