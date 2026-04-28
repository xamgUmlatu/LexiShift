from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

CORE_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = CORE_ROOT.parent
SCRIPTS_ROOT = REPO_ROOT / "scripts" / "testing"
for candidate in (str(CORE_ROOT), str(SCRIPTS_ROOT)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from semantic_source_row_alignment_audit_en_es import (  # noqa: E402
    build_source_row_alignment_report,
    render_source_row_alignment_markdown,
)


class SemanticSourceRowAlignmentAuditTests(unittest.TestCase):
    def test_audit_distinguishes_trigger_frames_from_short_glosses(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            batch_path = Path(tmpdir) / "batch.json"
            batch_path.write_text(json.dumps(_tiny_batch()), encoding="utf-8")

            report = build_source_row_alignment_report(batch_paths=[batch_path])

        summary = report["summary"]
        self.assertEqual(summary["row_count"], 3)
        self.assertEqual(summary["trigger_present_row_count"], 2)
        self.assertEqual(summary["selector_ready_row_count"], 2)
        self.assertEqual(summary["two_sided_frame_row_count"], 2)

        family = report["family_rows"][0]
        self.assertEqual(family["family_id"], "en-es:sentence-veto:ball:pelota")
        self.assertEqual(family["active_selector_ready_count"], 1)
        self.assertEqual(family["shadow_selector_ready_count"], 1)
        self.assertTrue(family["ready_for_dynamic_selection"])

        sample_by_id = {row["row_id"]: row for row in report["sample_rows"]}
        self.assertTrue(sample_by_id["active-frame"]["selector_ready"])
        self.assertFalse(sample_by_id["shadow-gloss"]["selector_ready"])

        markdown = render_source_row_alignment_markdown(report)
        self.assertIn("Source Row Alignment Audit", markdown)
        self.assertIn("active-frame", markdown)


def _tiny_batch() -> dict[str, object]:
    return {
        "schema_version": 1,
        "row_count": 3,
        "rows": [
            {
                "row_id": "active-frame",
                "source_family": "fixture",
                "source_id": "fixture",
                "source_type": "test",
                "relation_type": "anchor_cue",
                "trigger": "ball",
                "normalized_trigger": "ball",
                "evidence_text": "The child kicked the ball across the yard.",
                "metadata": {
                    "family_id": "en-es:sentence-veto:ball:pelota",
                    "candidate_sense_id": "en-es:sentence-veto:ball:pelota:active",
                },
            },
            {
                "row_id": "shadow-frame",
                "source_family": "fixture",
                "source_id": "fixture",
                "source_type": "test",
                "relation_type": "shadow_candidate",
                "trigger": "ball",
                "normalized_trigger": "ball",
                "evidence_text": "They attended a ball at the palace.",
                "metadata": {
                    "family_id": "en-es:sentence-veto:ball:pelota",
                    "candidate_sense_id": "en-es:sentence-veto:ball:baile:shadow",
                },
            },
            {
                "row_id": "shadow-gloss",
                "source_family": "fixture",
                "source_id": "fixture",
                "source_type": "test",
                "relation_type": "shadow_candidate",
                "trigger": "ball",
                "normalized_trigger": "ball",
                "evidence_text": "formal dance",
                "metadata": {
                    "family_id": "en-es:sentence-veto:ball:pelota",
                    "candidate_sense_id": "en-es:sentence-veto:ball:baile:shadow",
                },
            },
        ],
    }


if __name__ == "__main__":
    unittest.main()
