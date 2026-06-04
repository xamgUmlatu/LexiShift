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

from semantic_veto_full_family_representative_sample_en_es import (  # noqa: E402
    build_full_family_representative_sample_report,
    render_full_family_representative_sample_markdown,
)


class SemanticVetoFullFamilyRepresentativeSampleTests(unittest.TestCase):
    def test_freezes_sample_from_full_source_target_pairs(self) -> None:
        report = build_full_family_representative_sample_report(
            bridge_payload={
                "pair": "en-es",
                "decision": "srs_zipf_bridge_established",
                "full_source_target_pairs": [
                    _pair("change", "cambio", "zipf_5_plus_very_common"),
                    _pair("order", "orden", "zipf_5_plus_very_common"),
                    _pair("bark", "ladrar", "zipf_3_to_4_mid"),
                    _pair("abate", "decrecer", "zipf_below_3_rare"),
                    _pair("measured", "medido", "zipf_4_to_5_common"),
                ],
            },
            difficulty_payload={
                "case_traces": [{"trigger": "measured", "product_outcome": "positive_allow"}]
            },
            wordnet_profiles_by_source={
                "change": {"wordnet_sense_count": 12, "wordnet_pos_count": 2},
                "order": {"wordnet_sense_count": 10, "wordnet_pos_count": 2},
                "bark": {"wordnet_sense_count": 5, "wordnet_pos_count": 2},
                "abate": {"wordnet_sense_count": 2, "wordnet_pos_count": 1},
                "measured": {"wordnet_sense_count": 3, "wordnet_pos_count": 1},
            },
            sample_per_cell=1,
            seed="fixture",
            generated_at="2026-05-06T00:00:00Z",
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["summary"]["full_source_target_pair_count"], 5)
        self.assertEqual(report["summary"]["eligible_source_target_pair_count"], 4)
        self.assertEqual(report["summary"]["sampled_family_count"], 3)
        self.assertTrue(report["e2e_checks"]["mid_source_band_represented"])
        self.assertTrue(report["e2e_checks"]["rare_source_band_represented"])
        self.assertNotIn(
            "measured",
            {str(row["source"]) for row in report["sampled_rows"]},
        )
        self.assertTrue(
            all(row["manual_packet"]["total_rows"] >= 3 for row in report["manual_authoring_queue"])
        )

        markdown = render_full_family_representative_sample_markdown(report)
        self.assertIn("Full-Family Representative Sample", markdown)
        self.assertIn("Manual Authoring Queue", markdown)

    def test_marks_missing_full_pairs_for_review(self) -> None:
        report = build_full_family_representative_sample_report(
            bridge_payload={"pair": "en-es", "full_source_target_pairs": []},
            difficulty_payload={},
            wordnet_profiles_by_source={},
            generated_at="2026-05-06T00:00:00Z",
        )

        self.assertEqual(report["status"], "review")
        self.assertFalse(report["e2e_checks"]["full_source_target_pairs_available"])


def _pair(source: str, target: str, source_band: str) -> dict[str, object]:
    return {
        "source": source,
        "target": target,
        "source_zipf_band_en": source_band,
        "target_zipf_band_es": "zipf_4_to_5_common",
    }


if __name__ == "__main__":
    unittest.main()
