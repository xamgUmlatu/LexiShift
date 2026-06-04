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
from semantic_veto_full_family_repair_pilot_en_es import build_repaired_pilot_report  # noqa: E402
from semantic_veto_full_family_trusted_eval_seed_en_es import (  # noqa: E402
    APPROVAL_ID,
    DEFAULT_DATASET_ID,
    build_trusted_eval_seed_report,
    render_trusted_eval_seed_markdown,
)


class SemanticVetoFullFamilyTrustedEvalSeedTests(unittest.TestCase):
    def test_promotes_repaired_rows_to_trusted_seed_after_user_approval(self) -> None:
        _, repaired = build_repaired_pilot_report(generated_at="2026-05-07T00:00:00Z")
        report, dataset = build_trusted_eval_seed_report(
            repaired_payload=repaired,
            generated_at="2026-05-07T00:00:00Z",
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(
            report["decision"],
            "full_family_trusted_eval_seed_ready_for_scoring",
        )
        self.assertEqual(dataset["dataset_id"], DEFAULT_DATASET_ID)
        self.assertEqual(report["summary"]["trusted_family_count"], 7)
        self.assertEqual(report["summary"]["trusted_case_count"], 27)
        self.assertEqual(report["summary"]["excluded_family_count"], 3)
        self.assertEqual(report["summary"]["row_quality_status"], "trusted")
        self.assertTrue(all(report["e2e_checks"].values()))

        cases = [case for family in dataset["families"] for case in family["cases"]]
        self.assertTrue(cases)
        self.assertTrue(all(case["human_review_status"] == "approved_by_user" for case in cases))
        self.assertTrue(all(case["row_quality_status"] == "trusted" for case in cases))
        self.assertTrue(all(case["approval_id"] == APPROVAL_ID for case in cases))

        with tempfile.TemporaryDirectory() as tmpdir:
            dataset_path = Path(tmpdir) / "dataset.json"
            dataset_path.write_text(json.dumps(dataset, ensure_ascii=False), encoding="utf-8")
            loaded = load_sentence_veto_dataset(dataset_path)

        self.assertEqual(len(loaded["families"]), 7)
        markdown = render_trusted_eval_seed_markdown(report)
        self.assertIn("Trusted Eval Seed", markdown)
        self.assertIn("User approval applies only to repaired pilot rows", markdown)


if __name__ == "__main__":
    unittest.main()
