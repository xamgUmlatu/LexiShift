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
    build_sentence_veto_weak_active_probe_report,
)


class SemanticRoutingSentenceVetoWeakActiveProbeTests(unittest.TestCase):
    def test_probe_falls_back_to_bounded_overlay_when_zero_harm_option_disappears(self) -> None:
        report = build_sentence_veto_weak_active_probe_report(
            dataset_path=REPO_ROOT
            / "docs"
            / "test_inputs"
            / "semantic_routing_cases"
            / "en_es_sentence_veto_v10.json",
        )
        self.assertFalse(bool(report["zero_harmful_overlay_available"]))
        self.assertEqual(str(report["best_zero_harmful_overlay_config_id"]), "")
        self.assertEqual(str(report["selected_overlay_config_id"]), "overlay:p=-0.05:b=0.02")
        self.assertEqual(str(report["selected_overlay_label"]), "Best bounded rescue overlay")

        config_entries = {
            str(entry.get("config_id") or "").strip(): entry
            for entry in report.get("configurations", [])
            if isinstance(entry, dict)
        }
        current_default = config_entries["current_default"]
        current_default_focus = {
            row["case_id"]: row
            for row in current_default.get("focus_cases", [])
            if isinstance(row, dict)
        }
        self.assertEqual(
            current_default_focus["en-es:sentence-veto:park:001"]["predicted_decision"],
            "abstain",
        )

        self.assertEqual(current_default["label"], "Current default runtime row")
        self.assertEqual(int(current_default["summary"]["harmful_replace_count"]), 1)

        best_overlay = config_entries["overlay:p=-0.05:b=0.02"]
        self.assertEqual(best_overlay["label"], "Best bounded rescue overlay")
        overlay_summary = best_overlay["summary"]
        self.assertEqual(int(overlay_summary["harmful_replace_count"]), 1)
        self.assertEqual(int(overlay_summary["false_abstain_count"]), 6)
        self.assertAlmostEqual(float(overlay_summary["replace_recall"]), 32 / 38)
        overlay_focus = {
            row["case_id"]: row
            for row in best_overlay.get("focus_cases", [])
            if isinstance(row, dict)
        }
        self.assertEqual(
            overlay_focus["en-es:sentence-veto:park:001"]["predicted_decision"],
            "replace",
        )
        self.assertTrue(overlay_focus["en-es:sentence-veto:park:001"]["active_rescue_applied"])
        self.assertEqual(
            overlay_focus["en-es:sentence-veto:drink:002"]["predicted_decision"],
            "replace",
        )
        self.assertTrue(overlay_focus["en-es:sentence-veto:drink:002"]["active_rescue_applied"])
        self.assertEqual(
            overlay_focus["en-es:sentence-veto:play:002"]["predicted_decision"],
            "abstain",
        )
        self.assertEqual(
            overlay_focus["en-es:sentence-veto:check:002"]["predicted_decision"],
            "abstain",
        )
        self.assertEqual(
            overlay_focus["en-es:sentence-veto:order:002"]["predicted_decision"],
            "abstain",
        )
        self.assertEqual(
            overlay_focus["en-es:sentence-veto:trip:002"]["predicted_decision"],
            "abstain",
        )
        self.assertEqual(
            overlay_focus["en-es:sentence-veto:report:001"]["predicted_decision"],
            "abstain",
        )
        self.assertEqual(
            overlay_focus["en-es:sentence-veto:report:002"]["predicted_decision"],
            "abstain",
        )

        raw_sentence_primary = config_entries["raw_sentence_primary"]
        raw_sentence_summary = raw_sentence_primary["summary"]
        self.assertGreater(int(raw_sentence_summary["harmful_replace_count"]), 0)
        masked_sense_label = config_entries["masked_sense_label_primary"]
        self.assertGreater(int(masked_sense_label["summary"]["harmful_replace_count"]), 0)


if __name__ == "__main__":
    unittest.main()
