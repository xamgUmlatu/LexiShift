from __future__ import annotations

from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = PROJECT_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_browsing_admission_implicit_sample_pack_en_ja import (  # noqa: E402
    build_browsing_store,
    evaluate_scenario,
    normalize_signal_entries,
)


class TestSrsBrowsingAdmissionImplicitSamplePackEnJa(unittest.TestCase):
    def test_signal_entries_are_normalized_for_target_lemma_store(self) -> None:
        entries = normalize_signal_entries(
            [
                {"target_lemma": "料理", "side": "target", "count": "4"},
                {"lemma": "病院", "side": "source", "count": 2, "source_mapping_confidence": 0.5},
                {"target_lemma": "野菜", "side": "unknown", "count": None},
                {"target_lemma": ""},
            ]
        )

        self.assertEqual(
            entries,
            [
                {
                    "target_key": "",
                    "target_lemma": "料理",
                    "target_reading": "",
                    "side": "target",
                    "count": 4.0,
                    "source_mapping_confidence": None,
                    "reading_confidence": 1.0,
                    "observation_source": "",
                },
                {
                    "target_key": "",
                    "target_lemma": "病院",
                    "target_reading": "",
                    "side": "source",
                    "count": 2.0,
                    "source_mapping_confidence": 0.5,
                    "reading_confidence": 1.0,
                    "observation_source": "",
                },
                {
                    "target_key": "",
                    "target_lemma": "野菜",
                    "target_reading": "",
                    "side": "target",
                    "count": 1.0,
                    "source_mapping_confidence": None,
                    "reading_confidence": 1.0,
                    "observation_source": "",
                },
            ],
        )

    def test_browsing_store_keeps_target_and_source_counts_separate(self) -> None:
        store = build_browsing_store(
            pair="en-ja",
            scenario={
                "signals": [
                    {"target_lemma": "料理", "side": "target", "count": 5},
                    {"target_lemma": "料理", "side": "source", "count": 3},
                    {"target_lemma": "料理", "side": "replacement_exposure", "count": 2},
                ]
            },
        )

        aggregate = store.items["料理"]
        self.assertEqual(store.pair, "en-ja")
        self.assertEqual(aggregate.target_hit_count, 5.0)
        self.assertEqual(aggregate.source_hit_count, 3.0)
        self.assertEqual(aggregate.replacement_exposure_count, 2.0)

    def test_browsing_store_uses_reading_aware_key_when_available(self) -> None:
        store = build_browsing_store(
            pair="en-ja",
            scenario={
                "signals": [
                    {
                        "target_lemma": "辛い",
                        "target_reading": "つらい",
                        "side": "target",
                        "count": 4,
                        "reading_confidence": 0.5,
                    }
                ]
            },
        )

        aggregate = store.items["辛い|つらい"]
        self.assertEqual(aggregate.target_lemma, "辛い")
        self.assertEqual(aggregate.target_reading, "つらい")
        self.assertAlmostEqual(aggregate.reading_confidence, 0.5)

    def test_expectation_checks_guard_preview_only_and_blocked_lemma_behavior(self) -> None:
        findings = evaluate_scenario(
            scenario={
                "expectations": {
                    "matching_signals": True,
                    "strong_has_browsing_lane": True,
                    "blocked_lemmas_not_selected": True,
                }
            },
            preview={
                "runtime_srs_mutation": False,
                "applied_to_actual_admission": False,
                "matching_signal_count": 1,
                "simulations": {
                    "off": {"browsing_lane_share": 0.0, "selected_lemmas": ["ある"]},
                    "balanced": {
                        "browsing_lane_share": 0.125,
                        "selected_lemmas": ["野菜", "ある"],
                    },
                    "strong": {
                        "browsing_lane_share": 0.25,
                        "browsing_lane_count": 2,
                        "selected_lemmas": ["野菜", "飲む"],
                    },
                },
            },
            blocked_lemmas={"料理"},
        )

        self.assertTrue(all(row["level"] == "PASS" for row in findings))


if __name__ == "__main__":
    unittest.main()
