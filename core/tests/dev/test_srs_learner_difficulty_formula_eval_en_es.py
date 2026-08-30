from __future__ import annotations

from pathlib import Path
import sys
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_learner_difficulty_formula_eval_en_es import build_report, render_markdown  # noqa: E402


class SrsLearnerDifficultyFormulaEvalEnEsTests(unittest.TestCase):
    def test_evaluates_variants_with_primary_and_all_numeric_splits(self) -> None:
        report = build_report(
            formula_report=_formula_report_fixture(),
            calibration_payload=_labels_payload(
                "calibration",
                [
                    _label("hospital", 0.10, 1),
                    _label("arcaísmo", 0.86, 2),
                    _label("son", 0.18, 4, state="deprioritized_vocab"),
                ],
            ),
            holdout_payload=_labels_payload(
                "holdout",
                [
                    _label("idea", 0.08, 3),
                    _label("recondito", 0.96, 6),
                ],
            ),
            generated_at="2026-07-05T00:00:00+00:00",
        )

        self.assertEqual(report["decision"], "en_es_learner_difficulty_formula_eval_ready")
        self.assertEqual(report["summary"]["best_variant_id"], "good")

        best = report["variants"][0]
        self.assertEqual(best["calibration_primary"]["label_count"], 2)
        self.assertEqual(best["calibration_all_numeric"]["label_count"], 3)
        self.assertGreater(
            best["calibration_primary"]["scores"]["balanced_score"],
            report["variants"][1]["calibration_primary"]["scores"]["balanced_score"],
        )

        markdown = render_markdown(report)
        self.assertIn("en-es Learner Difficulty Formula Eval", markdown)
        self.assertIn("good", markdown)


def _formula_report_fixture() -> dict[str, object]:
    return {
        "decision": "fixture_formula_probe",
        "generated_at": "2026-07-05T00:00:00+00:00",
        "inputs": {"top_n": 5},
        "rows": [
            _row("hospital", 10, "noun", good=0.12, bad=0.80),
            _row("arcaísmo", 2000, "noun", good=0.84, bad=0.20),
            _row("idea", 20, "noun", good=0.10, bad=0.70),
            _row("son", 5, "verb", good=0.16, bad=0.10),
            _row("recondito", 3000, "adjective", good=0.94, bad=0.30),
        ],
    }


def _row(lemma: str, rank: int, pos: str, *, good: float, bad: float) -> dict[str, object]:
    return {
        "lemma": lemma,
        "spalex_rank": float(rank),
        "pos": pos,
        "pos_bucket": "noun" if pos == "noun" else "other",
        "candidate_state": "normal_vocab",
        "variant_scores": {
            "good": good,
            "bad": bad,
        },
    }


def _labels_payload(payload_id: str, labels: list[dict[str, object]]) -> dict[str, object]:
    return {
        "calibration_id": payload_id,
        "holdout_id": payload_id,
        "labels": labels,
    }


def _label(
    lemma: str,
    expected: float,
    review_number: int,
    *,
    state: str = "normal_vocab",
) -> dict[str, object]:
    return {
        "lemma": lemma,
        "expected_candidate_state": state,
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
