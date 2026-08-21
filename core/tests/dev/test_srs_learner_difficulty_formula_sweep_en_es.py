from __future__ import annotations

from pathlib import Path
import sys
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_learner_difficulty_formula_sweep_en_es import (  # noqa: E402
    build_report,
    generate_candidates,
    render_markdown,
)


class SrsLearnerDifficultyFormulaSweepEnEsTests(unittest.TestCase):
    def test_sweeps_components_and_reports_holdout_guarded_candidates(self) -> None:
        report = build_report(
            formula_report=_formula_report_fixture(),
            calibration_payload=_labels_payload(
                "calibration",
                [
                    _label("hotel", 0.18, 1),
                    _label("idea", 0.12, 2),
                    _label("recondito", 0.92, 3),
                ],
            ),
            holdout_payload=_labels_payload(
                "holdout",
                [
                    _label("hospital", 0.18, 4),
                    _label("arcaico", 0.84, 5),
                ],
            ),
            generated_at="2026-07-05T00:00:00+00:00",
        )

        self.assertEqual(report["decision"], "en_es_learner_difficulty_formula_sweep_ready")
        self.assertGreater(report["method"]["candidate_count"], 100)
        self.assertIn("current_best_baseline", report["summary"])
        self.assertIn("calibration_top", report["leaderboards"])
        self.assertIn("stable_top", report["leaderboards"])
        candidate_ids = [candidate.candidate_id for candidate in generate_candidates()]
        self.assertTrue(any("__ue_" in candidate_id for candidate_id in candidate_ids))
        self.assertTrue(any("__wf_" in candidate_id for candidate_id in candidate_ids))
        self.assertTrue(any("__lex_" in candidate_id for candidate_id in candidate_ids))
        self.assertTrue(any("__lsbq_" in candidate_id for candidate_id in candidate_ids))
        self.assertTrue(any("__lsbs_" in candidate_id for candidate_id in candidate_ids))

        best = report["summary"]["best_calibration_candidate"]
        self.assertIn("ls", best["candidate_id"])
        self.assertGreaterEqual(best["calibration_balanced"], 0.7)

        markdown = render_markdown(report)
        self.assertIn("en-es Learner Difficulty Formula Sweep", markdown)
        self.assertIn("Selection note", markdown)
        self.assertIn("Holdout-Guarded Top", markdown)


def _formula_report_fixture() -> dict[str, object]:
    return {
        "decision": "fixture_formula_probe",
        "generated_at": "2026-07-05T00:00:00+00:00",
        "inputs": {"top_n": 5},
        "rows": [
            _row("hotel", 10, 0.50, 0.50, learner_zipf_gap=0.38, learner_blend_gap=0.38),
            _row("idea", 20, 0.34, 0.34, learner_zipf_gap=0.19, learner_blend_gap=0.19),
            _row("hospital", 30, 0.48, 0.48, learner_zipf_gap=0.35, learner_blend_gap=0.35),
            _row("recondito", 3000, 0.92, 0.92),
            _row("arcaico", 2600, 0.84, 0.84, marked=0.5),
        ],
    }


def _row(
    lemma: str,
    rank: int,
    zipf_base: float,
    blend: float,
    *,
    learner_zipf_gap: float = 0.0,
    learner_blend_gap: float = 0.0,
    marked: float = 0.0,
) -> dict[str, object]:
    current_best = max(0.0, zipf_base - min(learner_zipf_gap * 0.8, 0.18))
    return {
        "lemma": lemma,
        "spalex_rank": float(rank),
        "pos": "noun",
        "pos_bucket": "noun",
        "candidate_state": "normal_vocab",
        "translations": [],
        "components": {
            "zipf_base": zipf_base,
            "spalex_blend": blend,
            "learner_core_gap_zipf_confident": learner_zipf_gap,
            "learner_core_gap_blend_confident": learner_blend_gap,
            "learner_core_gap_zipf_quality": learner_zipf_gap * 0.8,
            "learner_core_gap_blend_quality": learner_blend_gap * 0.8,
            "learner_core_gap_zipf_strict": learner_zipf_gap * 0.6,
            "learner_core_gap_blend_strict": learner_blend_gap * 0.6,
            "gated_dict_marked_usage_risk": marked,
        },
        "variant_scores": {
            "zipf_frequency_only": zipf_base,
            "learner_source_zipf_medium": current_best,
        },
    }


def _labels_payload(payload_id: str, labels: list[dict[str, object]]) -> dict[str, object]:
    return {
        "calibration_id": payload_id,
        "holdout_id": payload_id,
        "labels": labels,
    }


def _label(lemma: str, expected: float, review_number: int) -> dict[str, object]:
    return {
        "lemma": lemma,
        "expected_candidate_state": "normal_vocab",
        "expected_presentation_mode": "vocab",
        "expected_problem_class": "normal_vocab",
        "expected_difficulty_band": _band(expected),
        "expected_learner_difficulty": expected,
        "review_number": review_number,
        "review_flags": [],
        "review_confidence": 0.9,
        "rationale": "",
    }


def _band(score: float) -> str:
    if score < 0.20:
        return "beginner"
    if score < 0.40:
        return "core"
    if score < 0.60:
        return "intermediate"
    if score < 0.80:
        return "advanced"
    if score < 0.94:
        return "tail"
    return "recondite"


if __name__ == "__main__":
    unittest.main()
