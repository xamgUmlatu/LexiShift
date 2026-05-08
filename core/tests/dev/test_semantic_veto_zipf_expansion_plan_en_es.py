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

from semantic_veto_zipf_expansion_plan_en_es import (  # noqa: E402
    build_zipf_expansion_plan_report,
    render_zipf_expansion_plan_markdown,
)


class SemanticVetoZipfExpansionPlanTests(unittest.TestCase):
    def test_prioritizes_false_abstain_and_missing_control_bands(self) -> None:
        report = build_zipf_expansion_plan_report(
            representative_band_payload={
                "pair": "en-es",
                "decision": "representative_band_performance_established",
                "breakdowns": {
                    "source_zipf_frequency_en": [
                        _band(
                            "zipf_5_plus_very_common",
                            cases=68,
                            triggers=11,
                            positives=30,
                            negatives=38,
                            false_abstains=26,
                            positive_allow_rate=0.1333,
                        ),
                        _band(
                            "zipf_4_to_5_common",
                            cases=52,
                            triggers=8,
                            positives=23,
                            negatives=29,
                            false_abstains=14,
                            positive_allow_rate=0.3913,
                        ),
                    ]
                },
                "trigger_risk_summary": [
                    {
                        "scope_id": "bank",
                        "source_zipf_band": "zipf_5_plus_very_common",
                    },
                    {
                        "scope_id": "plant",
                        "source_zipf_band": "zipf_4_to_5_common",
                    },
                ],
            },
            difficulty_payload={
                "pair": "en-es",
                "decision": "difficulty_stratification_baseline_established",
                "source_zipf_breakdowns_en": [
                    _band(
                        "zipf_5_plus_very_common",
                        cases=131,
                        triggers=16,
                        positives=59,
                        negatives=72,
                        false_abstains=30,
                        positive_allow_rate=0.4915,
                    )
                ],
            },
            generated_at="2026-05-06T00:00:00Z",
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["summary"]["planned_zipf_band_count"], 4)
        self.assertEqual(report["summary"]["represented_zipf_band_count"], 2)
        self.assertGreaterEqual(report["summary"]["p0_band_count"], 1)

        by_band = {row["zipf_band"]: row for row in report["expansion_rows"]}
        self.assertEqual(by_band["zipf_5_plus_very_common"]["priority"], "P0")
        self.assertEqual(
            by_band["zipf_5_plus_very_common"]["reason"],
            "very_common_positive_false_abstain_mass",
        )
        self.assertEqual(by_band["zipf_3_to_4_mid"]["representative_case_count"], 0)
        self.assertEqual(
            by_band["zipf_3_to_4_mid"]["reason"],
            "missing_representative_control_band",
        )

        markdown = render_zipf_expansion_plan_markdown(report)
        self.assertIn("Zipf Expansion Plan", markdown)
        self.assertIn("very-common band", markdown)


def _band(
    scope_id: str,
    *,
    cases: int,
    triggers: int,
    positives: int,
    negatives: int,
    false_abstains: int,
    positive_allow_rate: float,
) -> dict[str, object]:
    return {
        "scope_id": scope_id,
        "case_count": cases,
        "trigger_count": triggers,
        "positive_case_count": positives,
        "negative_case_count": negatives,
        "positive_abstain_count": false_abstains,
        "positive_allow_rate": positive_allow_rate,
        "negative_abstain_rate": 1.0,
    }


if __name__ == "__main__":
    unittest.main()
