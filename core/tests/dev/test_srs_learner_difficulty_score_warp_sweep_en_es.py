from __future__ import annotations

from pathlib import Path
import sys
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_learner_difficulty_score_warp_sweep_en_es import (  # noqa: E402
    build_report,
    render_markdown,
)


class SrsLearnerDifficultyScoreWarpSweepEnEsTests(unittest.TestCase):
    def test_sweeps_post_score_warps_and_reports_calibration_win(self) -> None:
        report = build_report(
            formula_report=_formula_report_fixture(),
            formula_sweep_payload={},
            calibration_payload=_labels_payload(
                "calibration",
                [
                    _label("bajo", 0.00),
                    _label("medio", 0.50),
                    _label("alto", 1.00),
                ],
            ),
            holdout_payload=_labels_payload(
                "holdout",
                [
                    _label("bajo_h", 0.00),
                    _label("alto_h", 1.00),
                ],
            ),
            candidate_ids=("spalex_blend__no_ls__no_cog__no_wf__no_guard",),
            generated_at="2026-07-05T00:00:00+00:00",
        )

        self.assertEqual(
            report["decision"],
            "en_es_learner_difficulty_score_warp_sweep_ready",
        )
        self.assertFalse(report["runtime_behavior_changed"])
        self.assertFalse(report["production_ranking_changed"])
        self.assertGreater(report["method"]["warp_count"], 5)

        best_calibration = report["summary"]["best_calibration_profile"]
        identity = report["summary"]["best_identity_profile"]
        self.assertNotEqual(best_calibration["warp_id"], "identity")
        self.assertLess(
            best_calibration["calibration_mae"],
            identity["calibration_mae"],
        )

        markdown = render_markdown(report)
        self.assertIn("en-es Learner Difficulty Score Warp Sweep", markdown)
        self.assertIn("Calibration Top", markdown)
        self.assertIn("score warps", markdown)

    def test_stratified_pool_keeps_key_formula_dimensions_open(self) -> None:
        report = build_report(
            formula_report=_formula_report_fixture(),
            formula_sweep_payload={},
            calibration_payload=_labels_payload(
                "calibration",
                [
                    _label("bajo", 0.00),
                    _label("medio", 0.50),
                    _label("alto", 1.00),
                ],
            ),
            holdout_payload=_labels_payload(
                "holdout",
                [
                    _label("bajo_h", 0.00),
                    _label("alto_h", 1.00),
                ],
            ),
            candidate_pool="stratified",
            candidate_limit=36,
            generated_at="2026-07-05T00:00:00+00:00",
        )

        method = report["method"]
        self.assertEqual(method["candidate_pool"], "stratified")
        self.assertEqual(method["candidate_count"], 36)
        summary = method["selected_candidate_profile_summary"]
        self.assertGreaterEqual(len(summary["base"]), 2)
        self.assertGreaterEqual(len(summary["learner"]), 4)
        self.assertGreaterEqual(len(summary["cognate"]), 4)
        self.assertGreaterEqual(len(summary["side_source"]), 4)
        self.assertGreaterEqual(len(summary["guard"]), 4)

        markdown = render_markdown(report)
        self.assertIn("Candidate Shape Coverage", markdown)
        self.assertIn("spalex_blend", markdown)

    def test_manual_corrections_apply_after_warp(self) -> None:
        report = build_report(
            formula_report=_formula_report_fixture(),
            formula_sweep_payload={},
            calibration_payload=_labels_payload(
                "calibration",
                [
                    _label("bajo", 0.85),
                    _label("medio", 0.50),
                    _label("alto", 1.00),
                ],
            ),
            holdout_payload=_labels_payload("holdout", [_label("alto_h", 1.00)]),
            corrections_payload={
                "status": "fixture",
                "corrections": [
                    {
                        "lemma": "bajo",
                        "score_override": 0.85,
                        "status": "active",
                    }
                ],
            },
            candidate_ids=("spalex_blend__no_ls__no_cog__no_wf__no_guard",),
            generated_at="2026-07-05T00:00:00+00:00",
        )

        method = report["method"]
        self.assertTrue(method["manual_corrections_applied"])
        self.assertEqual(method["manual_correction_count"], 1)

        identity = next(
            row for row in report["selected_profile_details"] if row["warp_id"] == "identity"
        )
        observed = {
            row["lemma"]: row["observed"]
            for row in identity["calibration_primary"]["largest_errors"]
        }
        self.assertEqual(observed["bajo"], 0.85)


def _formula_report_fixture() -> dict[str, object]:
    rows = [
        _row("bajo", 0.20, 10),
        _row("medio", 0.40, 20),
        _row("alto", 0.60, 30),
        _row("bajo_h", 0.20, 40),
        _row("alto_h", 0.60, 50),
    ]
    return {
        "decision": "fixture_formula_probe",
        "generated_at": "2026-07-05T00:00:00+00:00",
        "inputs": {"top_n": len(rows)},
        "rows": rows,
    }


def _row(lemma: str, score: float, rank: int) -> dict[str, object]:
    return {
        "lemma": lemma,
        "candidate_state": "normal_vocab",
        "pos": "noun",
        "pos_bucket": "noun",
        "spalex_rank": float(rank),
        "components": {
            "spalex_blend": score,
            "zipf_base": score,
            "rank_base": score,
        },
        "variant_scores": {
            "spalex_blend_frequency": score,
        },
    }


def _labels_payload(payload_id: str, labels: list[dict[str, object]]) -> dict[str, object]:
    return {
        "calibration_id": payload_id,
        "holdout_id": payload_id,
        "labels": labels,
    }


def _label(lemma: str, expected: float) -> dict[str, object]:
    return {
        "lemma": lemma,
        "expected_candidate_state": "normal_vocab",
        "expected_presentation_mode": "vocab",
        "expected_problem_class": "normal_vocab",
        "expected_difficulty_band": "fixture",
        "expected_learner_difficulty": expected,
        "review_flags": [],
        "review_confidence": 0.9,
        "rationale": "",
    }


if __name__ == "__main__":
    unittest.main()
