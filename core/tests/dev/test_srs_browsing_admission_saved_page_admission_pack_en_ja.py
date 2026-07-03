from __future__ import annotations

from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = PROJECT_ROOT / "scripts" / "testing"
CORE_ROOT = PROJECT_ROOT / "core"
for path in (SCRIPT_DIR, CORE_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from lexishift_core.srs.browsing_admission import (  # noqa: E402
    BrowsingSignalAggregate,
    BrowsingSignalIngestPolicy,
    BrowsingSignalStore,
)
from srs_browsing_admission_saved_page_admission_hygiene import (  # noqa: E402
    build_signal_hygiene,
    classify_signal_hygiene,
)
from srs_browsing_admission_saved_page_admission_aggregate import (  # noqa: E402
    packet_entry_from_signal,
    store_preview,
)
from srs_browsing_admission_saved_page_admission_pack_en_ja import (  # noqa: E402
    evaluate_scenario,
)


class TestSrsBrowsingAdmissionSavedPageAdmissionPackEnJa(unittest.TestCase):
    def test_expectation_checks_min_matching_count_and_effective_signal_fields(self) -> None:
        findings = evaluate_scenario(
            scenario={
                "expectations": {
                    "min_matching_signal_count": 2,
                    "strong_has_browsing_lane": True,
                }
            },
            preview={
                "runtime_srs_mutation": False,
                "applied_to_actual_admission": False,
                "matching_signal_count": 2,
                "simulations": {
                    "off": {"browsing_lane_share": 0.0},
                    "balanced": {"browsing_lane_share": 0.125},
                    "strong": {
                        "browsing_lane_share": 0.25,
                        "browsing_lane_count": 1,
                        "browsing_signal_rows": [
                            {
                                "lemma": "兎",
                                "browsing_signal": 0.5,
                                "effective_browsing_signal": 0.4,
                            }
                        ],
                    },
                },
            },
            blocked_lemmas=set(),
        )

        self.assertTrue(all(row["level"] == "PASS" for row in findings))
        self.assertIn(
            "MIN_MATCHING_SIGNAL_COUNT",
            {str(row["code"]) for row in findings},
        )
        self.assertIn(
            "EFFECTIVE_SIGNAL_FIELDS_PRESENT",
            {str(row["code"]) for row in findings},
        )

    def test_min_matching_count_failure_is_explicit(self) -> None:
        findings = evaluate_scenario(
            scenario={"expectations": {"min_matching_signal_count": 5}},
            preview={
                "runtime_srs_mutation": False,
                "applied_to_actual_admission": False,
                "matching_signal_count": 1,
                "simulations": {
                    "off": {"browsing_lane_share": 0.0},
                    "balanced": {"browsing_lane_share": 0.0},
                    "strong": {"browsing_lane_share": 0.0, "browsing_lane_count": 0},
                },
            },
            blocked_lemmas=set(),
        )

        self.assertIn(
            {
                "level": "FAIL",
                "code": "MIN_MATCHING_SIGNAL_COUNT",
                "message": (
                    "Saved-page aggregate matched too few real admission candidates (1 < 5)."
                ),
            },
            findings,
        )

    def test_hygiene_rejects_only_obvious_non_standalone_page_surfaces(self) -> None:
        rejected = [
            classify_signal_hygiene({"target_lemma": "ませんでした"}),
            classify_signal_hygiene({"target_lemma": "たいもん"}),
            classify_signal_hygiene({"target_lemma": "というのは"}),
            classify_signal_hygiene({"target_lemma": "注文の多い"}),
        ]
        accepted = [
            classify_signal_hygiene({"target_lemma": "注文", "target_reading": "ちゅうもん"}),
            classify_signal_hygiene({"target_lemma": "クリーム"}),
            classify_signal_hygiene({"target_lemma": "兎", "target_reading": "うさぎ"}),
        ]

        self.assertTrue(all(row["status"] == "rejected" for row in rejected))
        self.assertTrue(all(row["status"] == "accepted" for row in accepted))

    def test_hygiene_summary_keeps_suspect_rows_out_of_reject_count(self) -> None:
        hygiene = build_signal_hygiene(
            [
                {"target_lemma": "注文", "target_reading": "ちゅうもん"},
                {"target_lemma": "ませんでした"},
                {"target_lemma": "ながながしいもの"},
            ]
        )

        self.assertEqual(hygiene["summary"]["input_signal_count"], 3)
        self.assertEqual(hygiene["summary"]["accepted_signal_count"], 1)
        self.assertEqual(hygiene["summary"]["rejected_signal_count"], 1)
        self.assertEqual(hygiene["summary"]["retained_suspect_signal_count"], 1)
        self.assertEqual(hygiene["rejected_target_keys"], ["ませんでした"])
        self.assertEqual(hygiene["retained_suspect_target_keys"], ["ながながしいもの"])

    def test_hygiene_selected_rejected_signal_fails_scenario(self) -> None:
        findings = evaluate_scenario(
            scenario={"expectations": {}},
            preview={
                "runtime_srs_mutation": False,
                "applied_to_actual_admission": False,
                "matching_signal_count": 0,
                "simulations": {
                    "off": {"browsing_lane_share": 0.0},
                    "balanced": {"browsing_lane_share": 0.0},
                    "strong": {"browsing_lane_share": 0.0, "browsing_lane_count": 0},
                },
            },
            blocked_lemmas=set(),
            hygiene_diagnostics={"selected_rejected_signal_count": 1},
        )

        self.assertIn(
            {
                "level": "FAIL",
                "code": "HYGIENE_REJECTED_SIGNAL_SELECTED",
                "message": "Hygiene-rejected saved-page signals were selected: 1.",
            },
            findings,
        )

    def test_packet_entry_preserves_reading_aware_target_key(self) -> None:
        entry = packet_entry_from_signal(
            {
                "target_lemma": "辛い",
                "target_reading": "つらい",
                "target_key": "辛い|つらい",
                "side": "target",
                "count": "3",
                "reading_confidence": "0.5",
                "observation_source": "target_surface",
            }
        )

        self.assertEqual(entry.target_lemma, "辛い")
        self.assertEqual(entry.target_reading, "つらい")
        self.assertEqual(entry.target_key, "辛い|つらい")
        self.assertEqual(entry.count, 3.0)
        self.assertAlmostEqual(entry.reading_confidence, 0.5)

    def test_store_preview_orders_by_raw_value(self) -> None:
        store = BrowsingSignalStore(
            pair="en-ja",
            items={
                "兎|うさぎ": BrowsingSignalAggregate(
                    target_lemma="兎",
                    target_key="兎|うさぎ",
                    target_reading="うさぎ",
                    target_hit_count=1.0,
                    reading_confidence=1.0,
                ),
                "料理店|りょうりてん": BrowsingSignalAggregate(
                    target_lemma="料理店",
                    target_key="料理店|りょうりてん",
                    target_reading="りょうりてん",
                    target_hit_count=5.0,
                    reading_confidence=1.0,
                ),
            },
        )

        rows = store_preview(store, BrowsingSignalIngestPolicy(), limit=2)

        self.assertEqual(rows[0]["target_key"], "料理店|りょうりてん")
        self.assertEqual(rows[1]["target_key"], "兎|うさぎ")
        self.assertGreater(rows[0]["signal_value"], rows[1]["signal_value"])


if __name__ == "__main__":
    unittest.main()
