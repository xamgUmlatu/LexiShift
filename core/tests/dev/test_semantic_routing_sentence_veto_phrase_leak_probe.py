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
    build_sentence_veto_phrase_leak_probe_report,
)


class SemanticRoutingSentenceVetoPhraseLeakProbeTests(unittest.TestCase):
    def test_active_only_phrase_guard_cleans_play_leak_without_losing_rescue_rows(self) -> None:
        report = build_sentence_veto_phrase_leak_probe_report(
            dataset_path=REPO_ROOT
            / "docs"
            / "test_inputs"
            / "semantic_routing_cases"
            / "en_es_sentence_veto_v10.json",
        )
        hard_entries = {
            str(entry.get("config_id") or "").strip(): entry
            for entry in report.get("hard_row_entries", [])
            if isinstance(entry, dict)
        }
        current_hard = hard_entries["current_default"]
        active_only_hard = hard_entries["active_only_phrase_guard"]
        self.assertEqual(int(current_hard["summary"]["harmful_replace_count"]), 1)
        self.assertEqual(int(active_only_hard["summary"]["harmful_replace_count"]), 0)
        self.assertEqual(int(current_hard["summary"]["false_abstain_count"]), 9)
        self.assertEqual(int(active_only_hard["summary"]["false_abstain_count"]), 9)
        self.assertEqual(
            current_hard["active_rescue_case_ids"],
            active_only_hard["active_rescue_case_ids"],
        )

        hard_delta = report["hard_row_delta"]
        self.assertEqual(
            hard_delta["changed_decision_case_ids"],
            ["en-es:sentence-veto:play:005"],
        )
        self.assertIn(
            "en-es:sentence-veto:play:004",
            set(hard_delta["new_phrase_preemption_case_ids"]),
        )
        self.assertIn(
            "en-es:sentence-veto:drink:005",
            set(hard_delta["new_phrase_preemption_case_ids"]),
        )
        self.assertIn(
            "en-es:sentence-veto:park:005",
            set(hard_delta["new_phrase_preemption_case_ids"]),
        )
        self.assertIn(
            "en-es:sentence-veto:order:005",
            set(hard_delta["new_phrase_preemption_case_ids"]),
        )
        self.assertIn(
            "en-es:sentence-veto:trip:005",
            set(hard_delta["new_phrase_preemption_case_ids"]),
        )
        self.assertIn(
            "en-es:sentence-veto:report:005",
            set(hard_delta["new_phrase_preemption_case_ids"]),
        )

        overlay_entries = {
            str(entry.get("config_id") or "").strip(): entry
            for entry in report.get("overlay_entries", [])
            if isinstance(entry, dict)
        }
        current_overlay = overlay_entries["current_overlay"]
        active_only_overlay = overlay_entries["active_only_overlay"]
        self.assertEqual(int(current_overlay["summary"]["harmful_replace_count"]), 1)
        self.assertEqual(int(active_only_overlay["summary"]["harmful_replace_count"]), 0)
        self.assertEqual(int(current_overlay["summary"]["false_abstain_count"]), 6)
        self.assertEqual(int(active_only_overlay["summary"]["false_abstain_count"]), 6)
        self.assertEqual(
            current_overlay["active_rescue_case_ids"],
            active_only_overlay["active_rescue_case_ids"],
        )

        overlay_delta = report["overlay_delta"]
        self.assertEqual(
            overlay_delta["changed_decision_case_ids"],
            ["en-es:sentence-veto:play:005"],
        )


if __name__ == "__main__":
    unittest.main()
