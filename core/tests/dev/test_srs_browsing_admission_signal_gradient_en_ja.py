from __future__ import annotations

from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = PROJECT_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_browsing_admission_signal_gradient_en_ja import (  # noqa: E402
    build_gradient_findings,
    expand_gradient_scenarios,
    format_count_slug,
    is_nondecreasing,
    summarize_gradient_groups,
)


class TestSrsBrowsingAdmissionSignalGradientEnJa(unittest.TestCase):
    def test_expand_gradient_scenarios_builds_zero_and_matching_expectations(self) -> None:
        scenarios = expand_gradient_scenarios(
            {
                "gradient_groups": [
                    {
                        "name": "food",
                        "proficiency": 0.2,
                        "side": "target",
                        "lemmas": ["料理", "野菜"],
                    }
                ]
            },
            default_counts=[0, 1, 2],
            group_filter=[],
        )

        self.assertEqual([row["name"] for row in scenarios], ["food_c0", "food_c1", "food_c2"])
        self.assertEqual(scenarios[0]["signals"], [])
        self.assertEqual(scenarios[0]["expectations"], {"empty_store_preserves_neutral": True})
        self.assertEqual(len(scenarios[1]["signals"]), 2)
        self.assertEqual(scenarios[1]["expectations"], {"matching_signals": True})

    def test_gradient_summary_finds_first_lane_thresholds(self) -> None:
        rows = [
            {
                "group": "food",
                "count": 0.0,
                "side": "target",
                "lemma_count": 2,
                "signal_total": 0.0,
                "strengths": {
                    "balanced": {"browsing_lane_count": 0},
                    "strong": {"browsing_lane_count": 0},
                },
            },
            {
                "group": "food",
                "count": 1.0,
                "side": "target",
                "lemma_count": 2,
                "signal_total": 0.5,
                "strengths": {
                    "balanced": {"browsing_lane_count": 0},
                    "strong": {"browsing_lane_count": 1},
                },
            },
            {
                "group": "food",
                "count": 2.0,
                "side": "target",
                "lemma_count": 2,
                "signal_total": 0.8,
                "strengths": {
                    "balanced": {"browsing_lane_count": 1},
                    "strong": {"browsing_lane_count": 2},
                },
            },
        ]

        [summary] = summarize_gradient_groups(rows)

        self.assertEqual(summary["first_balanced_lane_count"], 2.0)
        self.assertEqual(summary["first_strong_lane_count"], 1.0)
        self.assertEqual(summary["max_balanced_lane_count"], 1)
        self.assertEqual(summary["max_strong_lane_count"], 2)

    def test_findings_detect_monotonicity_and_status(self) -> None:
        findings = build_gradient_findings(
            [{"name": "food_c1", "status": "pass"}],
            [
                {
                    "group": "food",
                    "signal_totals": [0.0, 0.2, 0.4],
                    "balanced_lane_counts": [0, 0, 1],
                    "strong_lane_counts": [0, 1, 2],
                }
            ],
        )

        self.assertTrue(all(row["level"] == "PASS" for row in findings))
        self.assertTrue(is_nondecreasing([0, 1, 1, 2]))
        self.assertFalse(is_nondecreasing([0, 2, 1]))
        self.assertEqual(format_count_slug(0.25), "0p25")


if __name__ == "__main__":
    unittest.main()
