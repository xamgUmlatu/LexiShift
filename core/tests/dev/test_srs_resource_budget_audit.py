from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_resource_budget_audit import build_report, render_markdown  # noqa: E402


class TestSrsResourceBudgetAudit(unittest.TestCase):
    def test_reports_static_budgets_and_cache_policy_gap(self) -> None:
        report = build_report(
            data_root=Path("/tmp/lexishift-unit-missing"),
            pair="en-es",
            profile_id="default",
            generated_at="2026-05-27T00:00:00+00:00",
        )

        rows = {(row["surface"], row["budget"]): row for row in report["code_budget_rows"]}
        self.assertEqual(rows[("helper_srs_settings", "max_active_items")]["cap"], 40)
        self.assertEqual(rows[("runtime_page_budget", "max_replacements_per_page")]["cap"], 20)
        self.assertEqual(rows[("extension_exposure_log", "max_entries")]["cap"], 2000)
        self.assertEqual(
            rows[("helper_browsing_signal_ingest", "max_items_per_store")]["cap"], 5000
        )

        self.assertIn("cache_budget_policy_missing", report["summary"]["finding_codes"])
        self.assertFalse(report["scope"]["data_root_exists"])

    def test_reports_helper_artifacts_and_stale_active_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data_root = Path(tmp)
            profile_dir = data_root / "srs" / "profiles" / "default"
            profile_dir.mkdir(parents=True)
            _write_json(
                profile_dir / "srs_store.json",
                {
                    "version": 2,
                    "items": [
                        {
                            "item_id": "en-es:armadillo",
                            "lemma": "armadillo",
                            "language_pair": "en-es",
                            "source_type": "frequency_list",
                            "admitted_at": "2026-05-18T00:00:00Z",
                            "exposures": 0,
                            "srs_history": [],
                        },
                        {
                            "item_id": "en-es:perro",
                            "lemma": "perro",
                            "language_pair": "en-es",
                            "source_type": "frequency_list",
                            "exposures": 3,
                            "srs_history": [{"ts": "2026-05-27T00:00:00Z", "rating": "good"}],
                        },
                    ],
                },
            )
            _write_json(
                profile_dir / "srs_inventory.json",
                {
                    "version": 1,
                    "pairs": {
                        "en-es": {
                            "active_item_ids": ["en-es:armadillo", "en-es:perro"],
                        }
                    },
                },
            )
            _write_json(
                profile_dir / "srs_ruleset_en-es.json",
                {
                    "rules": [
                        {
                            "source_phrase": "armadillo",
                            "replacement": "armadillo",
                            "enabled": True,
                        },
                        {"source_phrase": "dog", "replacement": "perro", "enabled": True},
                    ]
                },
            )
            _write_json(
                profile_dir / "srs_signal_queue.json",
                {
                    "version": 1,
                    "events": [
                        {
                            "event_type": "feedback",
                            "pair": "en-es",
                            "lemma": "perro",
                            "source_type": "extension",
                            "rating": "good",
                        }
                    ],
                },
            )

            report = build_report(
                data_root=data_root,
                pair="en-es",
                profile_id="default",
                generated_at="2026-05-27T00:00:00+00:00",
            )

        self.assertTrue(report["scope"]["data_root_exists"])
        self.assertEqual(report["helper_artifacts"]["active_item_count"], 2)
        self.assertEqual(report["helper_artifacts"]["stale_active_count"], 1)
        self.assertEqual(report["helper_artifacts"]["stale_unseen_active_count"], 1)
        self.assertEqual(
            report["helper_artifacts"]["stale_active_preview"][0]["admitted_age_days"], 9
        )
        self.assertEqual(
            report["helper_artifacts"]["stale_active_preview"][0]["lemma"],
            "armadillo",
        )
        self.assertIn("encounter_starvation_candidates", report["summary"]["finding_codes"])

        markdown = render_markdown(report)
        self.assertIn("Encounter-Starvation Preview", markdown)
        self.assertIn("Stale unseen active items: `1` over `7` days", markdown)
        self.assertIn("armadillo", markdown)


def _write_json(path: Path, payload: object) -> None:
    import json

    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
