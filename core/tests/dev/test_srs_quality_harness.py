from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_quality_harness import build_report, prepare_report_for_publication  # noqa: E402


class TestSrsQualityHarness(unittest.TestCase):
    def test_build_report_for_en_ja_verifies_due_aware_runtime_gate(self) -> None:
        report = build_report(pairs=("en-ja",), include_feedback=True)
        summary = report["summary"]
        findings = report["findings"]
        self.assertEqual(summary["fail_count"], 0)
        self.assertEqual(summary["warn_count"], 0)
        self.assertTrue(
            any(item.get("code") == "SRS_DUE_AWARE_RUNTIME_GATE_VERIFIED" for item in findings)
        )
        self.assertTrue(
            any(item.get("code") == "SRS_FEEDBACK_SNAPSHOTS_CAPTURED" for item in findings)
        )
        self.assertTrue(
            any(item.get("code") == "SRS_ENCOUNTER_WATCH_SUMMARY_VERIFIED" for item in findings)
        )
        encounter_summary = report["encounter_watch_scenario"]["dashboard_summary"]
        self.assertEqual(encounter_summary["active_stale_zero_exposure_zero_feedback"], 2)
        self.assertEqual(encounter_summary["active_without_enabled_rules"], 1)
        phases = report["feedback_cycle_scenario"]["phases"]
        phase_1 = phases[0]
        phase_2 = phases[1]
        phase_3 = phases[2]
        self.assertIn("before_refresh", phase_1)
        self.assertIn("after_refresh", phase_1)
        self.assertEqual(phase_1["feedback_delta"]["reviewed_lemmas"], ["alpha"])
        self.assertIn("alpha", phase_1["feedback_delta"]["scheduler_changed_lemmas"])
        self.assertEqual(
            sorted(phase_1["selected_lemmas"]),
            sorted(phase_1["refresh_delta"]["added_lemmas"]),
        )
        self.assertEqual(phase_2["selected_lemmas"], [])
        self.assertEqual(phase_2["refresh_delta"]["total_items_delta"], 0)
        self.assertEqual(
            sorted(phase_3["selected_lemmas"]),
            sorted(phase_3["refresh_delta"]["added_lemmas"]),
        )

    def test_build_report_supports_en_es_bootstrap_scenario(self) -> None:
        report = build_report(pairs=("en-es",), include_feedback=False)

        self.assertEqual(report["summary"]["fail_count"], 0)
        self.assertEqual(report["summary"]["warn_count"], 0)
        self.assertEqual(report["supported_pairs"], ["en-es"])
        self.assertEqual(report["unsupported_pairs"], [])
        scenario = report["pair_bootstrap_scenarios"][0]
        self.assertEqual(scenario["pair"], "en-es")
        self.assertEqual(scenario["runtime_due_active_count"], scenario["due_count"])
        self.assertTrue(
            any(
                item.get("code") == "SRS_BROWSING_PREVIEW_SIGNAL_VISIBLE"
                for item in scenario["findings"]
            )
        )

    def test_prepare_report_for_publication_normalizes_transient_fields(self) -> None:
        temp_root = Path(tempfile.gettempdir())
        temp_store_path = (
            temp_root / "tmpabc123" / "srs" / "profiles" / "default" / "srs_store.json"
        )
        temp_inventory_path = (
            temp_root / "tmpabc123" / "srs" / "profiles" / "default" / "srs_inventory.json"
        )
        report = {
            "generated_at": "2026-04-21T10:20:30.123456+00:00",
            "summary": {"status": "PASS", "pass_count": 1, "warn_count": 0, "fail_count": 0},
            "pair_bootstrap_scenarios": [
                {
                    "pair": "en-ja",
                    "init": {
                        "store_path": str(temp_store_path),
                        "inventory": {
                            "path": str(temp_inventory_path),
                            "updated_at": "2026-04-21T10:20:31+00:00",
                        },
                    },
                    "diagnostics": {
                        "snapshot_generation_id": "en-ja:default:565aa5a91f159fcb",
                        "publication_manifest_generation_id": "en-ja:default:565aa5a91f159fcb",
                        "frequency_pack_id": "freq-ja-bccwj",
                    },
                }
            ],
            "findings": [
                {
                    "level": "PASS",
                    "code": "OK",
                    "details": (
                        f'path="{temp_store_path}" '
                        "generated=2026-04-21T10:20:31+00:00 id=en-ja:default:565aa5a91f159fcb"
                    ),
                }
            ],
        }

        published = prepare_report_for_publication(report)

        self.assertEqual(published["generated_at"], "<generated_at>")
        self.assertEqual(
            published["artifact_normalization"],
            {
                "mode": "stable_latest_v1",
                "generated_at": "<generated_at>",
                "timestamps": "<timestamp>",
                "temp_root": "<temp_root>",
                "generation_ids": "<generated>",
            },
        )
        scenario = published["pair_bootstrap_scenarios"][0]
        self.assertEqual(
            scenario["init"]["store_path"],
            "<temp_root>/srs/profiles/default/srs_store.json",
        )
        self.assertEqual(
            scenario["init"]["inventory"]["path"],
            "<temp_root>/srs/profiles/default/srs_inventory.json",
        )
        self.assertEqual(scenario["init"]["inventory"]["updated_at"], "<timestamp>")
        self.assertEqual(
            scenario["diagnostics"]["snapshot_generation_id"],
            "en-ja:default:<generated>",
        )
        self.assertEqual(
            scenario["diagnostics"]["publication_manifest_generation_id"],
            "en-ja:default:<generated>",
        )
        self.assertEqual(scenario["diagnostics"]["frequency_pack_id"], "freq-ja-bccwj")
        self.assertIn(
            "<temp_root>/srs/profiles/default/srs_store.json", published["findings"][0]["details"]
        )
        self.assertIn("generated=<timestamp>", published["findings"][0]["details"])
        self.assertIn("id=en-ja:default:<generated>", published["findings"][0]["details"])
        self.assertEqual(
            report["pair_bootstrap_scenarios"][0]["diagnostics"]["snapshot_generation_id"],
            "en-ja:default:565aa5a91f159fcb",
        )


if __name__ == "__main__":
    unittest.main()
