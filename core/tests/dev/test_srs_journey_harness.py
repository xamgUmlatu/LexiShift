from __future__ import annotations

from pathlib import Path
import sys
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_journey_harness import build_report  # noqa: E402
from srs_journey_installed_support import installed_pair_resources_available  # noqa: E402


class TestSrsJourneyHarness(unittest.TestCase):
    def test_build_report_surfaces_deterministic_growth_pause_and_publication_warning(self) -> None:
        report = build_report()
        summary = report["summary"]
        findings = report["findings"]
        phases = report["phases"]

        self.assertEqual(summary["status"], "WARN")
        self.assertEqual(report["scenario"]["name"], "en-ja_core_journey_v1")
        self.assertEqual(report["scenario"]["id"], "en-ja_core_journey_v1")
        self.assertEqual(len(phases), 6)
        self.assertEqual(phases[0]["counts"]["admitted"], 3)
        self.assertEqual(phases[2]["counts"]["admitted"], 5)
        self.assertEqual(phases[3]["counts"]["admitted"], 5)
        self.assertEqual(phases[4]["counts"]["admitted"], 7)
        self.assertIn("bootstrap_audit", report["initialize"])
        self.assertEqual(
            report["initialize"]["bootstrap_audit"]["candidates"][0]["lemma"],
            "alpha",
        )
        self.assertTrue(
            any(item.get("code") == "SRS_JOURNEY_HIGH_RETENTION_ADMITS" for item in findings)
        )
        self.assertTrue(
            any(item.get("code") == "SRS_JOURNEY_LOW_RETENTION_PAUSES" for item in findings)
        )
        self.assertTrue(
            any(item.get("code") == "SRS_JOURNEY_RECOVERY_RESUMES" for item in findings)
        )
        self.assertTrue(
            any(item.get("code") == "SRS_JOURNEY_PUBLICATION_SCOPE_OBSERVED" for item in findings)
        )

        fade_phase = phases[-1]
        stable_due = [
            item["lemma"]
            for item in fade_phase["items"]
            if item["cohort"] == "stable" and item["in_due"]
        ]
        difficult_due = [
            item["lemma"]
            for item in fade_phase["items"]
            if item["cohort"] == "difficult" and item["in_due"]
        ]
        self.assertEqual(stable_due, [])
        self.assertEqual(difficult_due, ["gamma"])
        refresh_audit = phases[2]["refresh"]["audit"]
        self.assertEqual(refresh_audit["selected_lemmas"], ["delta", "epsilon"])
        self.assertTrue(any(item["selected"] for item in refresh_audit["candidates"]))
        self.assertIn("confidence", phases[2]["items"][0])
        self.assertIn("word_package", phases[2]["items"][0])

    def test_build_report_surfaces_edge_behavior_events_and_non_authoritative_exposure(
        self,
    ) -> None:
        report = build_report(scenario="en-ja_edge_behaviors_v1")
        summary = report["summary"]
        findings = report["findings"]
        phases = report["phases"]

        self.assertIn(summary["status"], {"PASS", "WARN"})
        self.assertEqual(report["scenario"]["lane"], "deterministic_edge_behaviors")
        self.assertEqual(len(phases), 5)

        duplicate_phase = phases[1]
        self.assertEqual(duplicate_phase["label"], "duplicate_feedback_burst")
        self.assertEqual(duplicate_phase["events_applied"]["counts"]["feedback"], 2)
        self.assertTrue(
            any(item.get("code") == "SRS_JOURNEY_DUPLICATE_FEEDBACK_RECORDED" for item in findings)
        )

        exposure_phase = phases[3]
        self.assertEqual(exposure_phase["label"], "exposure_only_pause_probe")
        self.assertEqual(exposure_phase["events_applied"]["counts"]["exposure"], 6)
        self.assertFalse(exposure_phase["refresh"]["payload"]["applied"])
        self.assertEqual(
            exposure_phase["refresh"]["payload"]["admission_refresh"]["reason_code"],
            "retention_low",
        )
        self.assertTrue(
            any(
                item.get("code") == "SRS_JOURNEY_EXPOSURE_ONLY_NON_AUTHORITATIVE"
                for item in findings
            )
        )

        signal_summary = report["signal_summary"]
        self.assertEqual(signal_summary["event_types"]["feedback"], 10)
        self.assertEqual(signal_summary["event_types"]["exposure"], 6)

    def test_build_report_surfaces_real_publication_lane(self) -> None:
        report = build_report(scenario="en-ja_real_publication_v1")
        findings = report["findings"]
        phases = report["phases"]

        self.assertIn(report["summary"]["status"], {"PASS", "WARN"})
        self.assertEqual(report["scenario"]["lane"], "real_publication_journey")
        self.assertEqual(len(phases), 6)
        self.assertTrue(
            any(item.get("code") == "SRS_JOURNEY_REAL_PUBLICATION_ACTIVE" for item in findings)
        )
        self.assertTrue(
            any(
                item.get("code") == "SRS_JOURNEY_REAL_PUBLICATION_COMPLETE_FOR_DUE"
                and item.get("level") == "PASS"
                for item in findings
            )
        )
        self.assertTrue(
            any(
                item.get("code") == "SRS_JOURNEY_REAL_WORD_PACKAGES_COMPLETE"
                and item.get("level") == "PASS"
                for item in findings
            )
        )
        first_phase_sources = phases[0]["runtime"]["ruleset_sources_preview"]
        self.assertTrue(first_phase_sources)
        self.assertTrue(
            all(not str(source).startswith("journey_src_") for source in first_phase_sources)
        )
        self.assertTrue(phases[0]["runtime"]["ruleset_source_target_pairs"])
        self.assertEqual(phases[2]["relationships"]["due_not_published"], [])
        self.assertEqual(
            phases[2]["runtime"]["diagnostics"]["store_items_with_word_package_for_pair"],
            phases[2]["counts"]["admitted"],
        )
        self.assertEqual(
            phases[2]["refresh"]["audit"]["selected_lemmas"],
            ["delta", "epsilon"],
        )

    def test_build_report_supports_en_es_core_lane(self) -> None:
        report = build_report(scenario="en-es_core_journey_v1")
        phases = report["phases"]

        self.assertEqual(report["summary"]["status"], "WARN")
        self.assertEqual(report["scenario"]["pair"], "en-es")
        self.assertEqual(report["scenario"]["cohorts"]["stable"], ["casa", "libro"])
        self.assertEqual(report["initialize"]["bootstrap_audit"]["candidates"][0]["lemma"], "casa")
        self.assertEqual(phases[2]["refresh"]["audit"]["selected_lemmas"], ["madre", "campo"])
        difficult_due = [
            item["lemma"]
            for item in phases[-1]["items"]
            if item["cohort"] == "difficult" and item["in_due"]
        ]
        self.assertEqual(difficult_due, ["hora"])

    def test_build_report_supports_en_es_profile_preference_lane(self) -> None:
        report = build_report(scenario="en-es_profile_preference_journey_v1")
        findings = report["findings"]
        phases = report["phases"]

        self.assertEqual(report["summary"]["status"], "WARN")
        self.assertEqual(report["scenario"]["pair"], "en-es")
        self.assertEqual(report["scenario"]["lane"], "profile_preference_journey")
        self.assertEqual(report["scenario"]["strategy"], "profile_bootstrap")
        self.assertEqual(
            report["scenario"]["profile_context"],
            {"topic_weights": {"family": 1.0}},
        )
        self.assertEqual(
            report["initialize"]["bootstrap_diagnostics"]["selection_strategy"],
            "profile_bootstrap",
        )
        self.assertEqual(
            report["initialize"]["bootstrap_diagnostics"]["selection_policy"],
            "reserved_topic_lane",
        )
        self.assertEqual(
            report["initialize"]["bootstrap_diagnostics"]["selected_preview"][:3],
            ["casa", "madre", "libro"],
        )
        self.assertEqual(
            report["initialize"]["bootstrap_diagnostics"]["initial_active_preview"],
            ["madre", "casa", "libro"],
        )
        self.assertEqual(
            report["scenario"]["candidate_universe"][3]["topics"],
            ["family", "people"],
        )

        self.assertEqual(phases[0]["counts"]["admitted"], 3)
        self.assertEqual(phases[2]["refresh"]["audit"]["selected_lemmas"], ["hora", "campo"])
        self.assertEqual(
            phases[3]["refresh"]["payload"]["admission_refresh"]["reason_code"],
            "retention_low",
        )
        self.assertEqual(phases[4]["refresh"]["audit"]["selected_lemmas"], ["ventana", "mesa"])
        self.assertTrue(
            any(item.get("code") == "SRS_JOURNEY_HIGH_RETENTION_ADMITS" for item in findings)
        )
        self.assertTrue(
            any(item.get("code") == "SRS_JOURNEY_LOW_RETENTION_PAUSES" for item in findings)
        )
        self.assertTrue(
            any(item.get("code") == "SRS_JOURNEY_RECOVERY_RESUMES" for item in findings)
        )

    def test_build_report_supports_en_es_real_publication_lane(self) -> None:
        report = build_report(scenario="en-es_real_publication_v1")
        findings = report["findings"]
        phases = report["phases"]

        self.assertIn(report["summary"]["status"], {"PASS", "WARN"})
        self.assertEqual(report["scenario"]["pair"], "en-es")
        self.assertTrue(
            any(item.get("code") == "SRS_JOURNEY_REAL_PUBLICATION_ACTIVE" for item in findings)
        )
        self.assertTrue(
            any(
                item.get("code") == "SRS_JOURNEY_REAL_PUBLICATION_COMPLETE_FOR_DUE"
                and item.get("level") == "PASS"
                for item in findings
            )
        )
        self.assertTrue(
            any(
                item.get("code") == "SRS_JOURNEY_REAL_WORD_PACKAGES_COMPLETE"
                and item.get("level") == "PASS"
                for item in findings
            )
        )
        self.assertEqual(phases[2]["relationships"]["due_not_published"], [])
        self.assertEqual(phases[2]["refresh"]["audit"]["selected_lemmas"], ["madre", "campo"])
        self.assertEqual(
            phases[2]["runtime"]["diagnostics"]["store_items_with_word_package_for_pair"],
            phases[2]["counts"]["admitted"],
        )

    @unittest.skipUnless(
        installed_pair_resources_available("en-ja"),
        "requires installed en-ja language/frequency packs",
    )
    def test_build_report_supports_en_ja_installed_resource_lane(self) -> None:
        report = build_report(scenario="en-ja_installed_data_journey_v1")
        phases = report["phases"]

        self.assertEqual(report["scenario"]["resource_mode"], "installed")
        self.assertEqual(report["scenario"]["pair"], "en-ja")
        self.assertEqual(report["scenario"]["cohorts"]["stable"], ["事", "物"])
        self.assertEqual(
            report["initialize"]["bootstrap_diagnostics"]["initial_active_preview"],
            ["事", "物", "時"],
        )
        self.assertEqual(phases[2]["refresh"]["audit"]["selected_lemmas"], ["人", "無い"])
        self.assertIn(report["summary"]["status"], {"PASS", "WARN"})

    @unittest.skipUnless(
        installed_pair_resources_available("en-es"),
        "requires installed en-es language/frequency packs",
    )
    def test_build_report_supports_en_es_installed_resource_lane(self) -> None:
        report = build_report(scenario="en-es_installed_data_journey_v1")
        phases = report["phases"]

        self.assertEqual(report["scenario"]["resource_mode"], "installed")
        self.assertEqual(report["scenario"]["pair"], "en-es")
        self.assertEqual(report["scenario"]["cohorts"]["stable"], ["siglo", "millón"])
        self.assertEqual(
            report["initialize"]["bootstrap_diagnostics"]["initial_active_preview"],
            ["siglo", "millón", "hora"],
        )
        self.assertEqual(phases[2]["refresh"]["audit"]["selected_lemmas"], ["música", "principio"])
        self.assertIn(report["summary"]["status"], {"PASS", "WARN"})


if __name__ == "__main__":
    unittest.main()
