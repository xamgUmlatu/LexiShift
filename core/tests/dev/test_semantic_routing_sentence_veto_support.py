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

from semantic_routing_sentence_veto_support import (  # noqa: E402
    build_sentence_veto_report,
)


class SemanticRoutingSentenceVetoSupportTests(unittest.TestCase):
    def test_gloss_primary_with_phrase_guard_has_one_false_abstain(self) -> None:
        report = build_sentence_veto_report(
            dataset_path=REPO_ROOT
            / "docs"
            / "test_inputs"
            / "semantic_routing_cases"
            / "en_es_sentence_veto_v2.json",
            scorer_id="sentence_transformer_cosine",
            context_view="masked_sentence",
            evidence_view="gloss_text",
            min_active_score=0.0,
            min_margin=0.0,
            phrase_control_mode="noun_family_frame_guard",
            active_rescue_mode="off",
        )
        summary = report["summary"]
        self.assertEqual(summary["harmful_replace_count"], 0)
        self.assertEqual(summary["false_abstain_count"], 1)
        self.assertEqual(summary["active_rescue_applied_count"], 0)

    def test_sense_label_near_tie_active_rescue_closes_remaining_gap(self) -> None:
        report = build_sentence_veto_report(
            dataset_path=REPO_ROOT
            / "docs"
            / "test_inputs"
            / "semantic_routing_cases"
            / "en_es_sentence_veto_v2.json",
            scorer_id="sentence_transformer_cosine",
            context_view="masked_sentence",
            evidence_view="gloss_text",
            min_active_score=0.0,
            min_margin=0.0,
            phrase_control_mode="noun_family_frame_guard",
            active_rescue_mode="sense_label_near_tie_active_rescue",
        )
        summary = report["summary"]
        self.assertEqual(summary["harmful_replace_count"], 0)
        self.assertEqual(summary["false_abstain_count"], 0)
        self.assertEqual(summary["active_rescue_applied_count"], 1)
        self.assertEqual(summary["active_rescue_correct_replace_count"], 1)
        self.assertEqual(summary["active_rescue_harmful_replace_count"], 0)
        rescued = [row for row in report["row_results"] if bool(row.get("active_rescue_applied"))]
        self.assertEqual([row["case_id"] for row in rescued], ["en-es:sentence-veto:plant:002"])


if __name__ == "__main__":
    unittest.main()
