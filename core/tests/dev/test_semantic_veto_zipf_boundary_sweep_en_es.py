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

from semantic_veto_zipf_boundary_sweep_en_es import (  # noqa: E402
    build_zipf_boundary_sweep_report,
    render_zipf_boundary_sweep_markdown,
)


class SemanticVetoZipfBoundarySweepTests(unittest.TestCase):
    def test_scores_current_scheme_against_observed_rows_and_full_denominator(self) -> None:
        report = build_zipf_boundary_sweep_report(
            difficulty_payload={
                "pair": "en-es",
                "decision": "difficulty_stratification_baseline_established",
                "case_traces": [
                    _case("sampling_stage1_representative_proxy", 5.8, "positive_abstain"),
                    _case("sampling_stage1_representative_proxy", 5.7, "positive_abstain"),
                    _case("sampling_stage1_representative_proxy", 4.6, "positive_allow"),
                    _case("sampling_stage1_representative_proxy", 4.4, "negative_abstain"),
                    _case("sampling_stage1_representative_proxy", 3.4, "negative_allow"),
                    _case("semantic_veto_llm_pilot_en_es_v1", 5.9, "negative_allow"),
                ],
            },
            bridge_payload={
                "pair": "en-es",
                "decision": "srs_zipf_bridge_established",
                "full_source_target_pairs": [
                    {"source": "change", "target": "cambio", "source_zipf_frequency_en": 5.5},
                    {"source": "order", "target": "orden", "source_zipf_frequency_en": 5.2},
                    {"source": "bark", "target": "ladrar", "source_zipf_frequency_en": 3.6},
                    {"source": "abate", "target": "decrecer", "source_zipf_frequency_en": 2.5},
                ],
            },
            generated_at="2026-05-06T00:00:00Z",
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["summary"]["case_count"], 5)
        self.assertEqual(report["summary"]["full_source_target_pair_count"], 4)
        self.assertGreater(report["summary"]["scheme_count"], 1)
        self.assertIn("current_5_4_3", {row["scheme_id"] for row in report["scheme_rows"]})
        self.assertIn("case_band_rows", report["current_scheme"])
        self.assertIn("full_source_family_band_rows", report["current_scheme"])

        markdown = render_zipf_boundary_sweep_markdown(report)
        self.assertIn("Zipf Boundary Sweep", markdown)
        self.assertIn("Current Scheme", markdown)


def _case(lane_id: str, zipf: float, outcome: str) -> dict[str, object]:
    return {
        "lane_id": lane_id,
        "source_zipf_frequency_en": zipf,
        "product_outcome": outcome,
    }


if __name__ == "__main__":
    unittest.main()
