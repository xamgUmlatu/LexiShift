from __future__ import annotations

from pathlib import Path
import sys
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_learner_difficulty_final_ranking_en_de import (  # noqa: E402
    build_report,
    render_markdown,
)


class SrsLearnerDifficultyFinalRankingEnDeTests(unittest.TestCase):
    def test_exports_full_corrected_ranking_with_manual_restriction_metadata(self) -> None:
        report, csv_rows = build_report(
            signal_rows=[
                _row("alpha", 0.10, core_rank=2),
                _row("beta", 0.08, core_rank=1),
            ],
            review_pack_payload={},
            sweep_payload={},
            corrections_payload={
                "status": "sidecar_review_input",
                "corrections": [
                    {
                        "lemma": "beta",
                        "status": "active",
                        "correction_types": ["restricted_admission"],
                        "admission_override": "fixture_restriction",
                        "rationale": "fixture restriction",
                    }
                ],
            },
            candidate_id="raw_frequency_blend",
            candidate_grid="broad",
            csv_out=Path("docs/test_outputs/fixture.csv"),
            generated_at="2026-07-07T00:00:00+00:00",
        )

        self.assertEqual(
            report["decision"],
            "en_de_learner_difficulty_final_ranking_review_ready",
        )
        self.assertFalse(report["runtime_behavior_changed"])
        self.assertFalse(report["production_ranking_changed"])
        self.assertEqual(report["summary"]["correction_rows"], 1)
        self.assertEqual([row["lemma"] for row in csv_rows], ["beta", "alpha"])

        beta = next(row for row in csv_rows if row["lemma"] == "beta")
        self.assertEqual(beta["correction_types"], "restricted_admission")
        self.assertEqual(beta["admission_override"], "fixture_restriction")
        self.assertEqual(beta["topic_stretch_allowed"], "False")

        markdown = render_markdown(report)
        self.assertIn("en-de Learner Difficulty Final Ranking Review", markdown)
        self.assertIn("fixture_restriction", markdown)


def _row(lemma: str, frequency_blend: float, *, core_rank: int) -> dict[str, object]:
    return {
        "lemma": lemma,
        "frequency_blend": frequency_blend,
        "rank_base": frequency_blend,
        "pmw_base": frequency_blend,
        "core_rank": core_rank,
        "pmw": 1000.0 / core_rank,
        "pos": "SUB:NOM:SIN:MAS",
        "pos_bucket": "noun",
        "translations": [lemma],
    }


if __name__ == "__main__":
    unittest.main()
