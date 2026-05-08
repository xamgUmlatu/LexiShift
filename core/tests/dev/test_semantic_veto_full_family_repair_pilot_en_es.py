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
from semantic_veto_full_family_repair_pilot_en_es import (  # noqa: E402
    DEFAULT_DATASET_ID,
    build_repaired_pilot_report,
    render_repaired_pilot_markdown,
)


class SemanticVetoFullFamilyRepairPilotTests(unittest.TestCase):
    def test_builds_repaired_pilot_without_trusting_rows(self) -> None:
        report, dataset = build_repaired_pilot_report(
            review_payload={
                "artifact_id": "unit_agent_manual_review",
                "review_authority": "codex_agent_recommendation_not_user_approval",
            },
            generated_at="2026-05-07T00:00:00Z",
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(
            report["decision"],
            "full_family_repaired_pilot_ready_for_user_review",
        )
        self.assertEqual(dataset["dataset_id"], DEFAULT_DATASET_ID)
        self.assertEqual(report["summary"]["repaired_family_count"], 7)
        self.assertEqual(report["summary"]["repaired_case_count"], 27)
        self.assertEqual(report["summary"]["trusted_case_count"], 0)
        self.assertEqual(report["summary"]["deferred_family_count"], 3)
        self.assertEqual(
            report["summary"]["case_type_counts"],
            {"phrase_no_winner": 7, "positive_active": 14, "shadow_negative": 6},
        )
        self.assertTrue(all(report["e2e_checks"].values()))

        shadows = [shadow for family in dataset["families"] for shadow in family.get("shadows", ())]
        self.assertTrue(shadows)
        self.assertFalse(
            any(
                "alternate sense" in str(shadow.get("target_lemma") or "").lower()
                for shadow in shadows
            )
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            dataset_path = Path(tmpdir) / "dataset.json"
            dataset_path.write_text(
                json.dumps(dataset, ensure_ascii=False),
                encoding="utf-8",
            )
            loaded = load_sentence_veto_dataset(dataset_path)

        self.assertEqual(len(loaded["families"]), 7)
        markdown = render_repaired_pilot_markdown(report)
        self.assertIn("Rows are semantically repaired", markdown)
        self.assertIn("Deferred Families", markdown)


if __name__ == "__main__":
    unittest.main()
