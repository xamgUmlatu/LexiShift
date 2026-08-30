from __future__ import annotations

from pathlib import Path
import sys
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_learner_difficulty_residual_patterns_en_es import (  # noqa: E402
    build_report,
    render_markdown,
)


class SrsLearnerDifficultyResidualPatternsEnEsTests(unittest.TestCase):
    def test_groups_residuals_by_computable_tags(self) -> None:
        report = build_report(
            formula_report=_formula_report_fixture(),
            sweep_payload={},
            calibration_payload=_labels_payload(
                "calibration",
                [
                    _label("regional", 0.50, ["marked_rare_or_regional"]),
                    _label("parte", 0.24, []),
                ],
            ),
            holdout_payload=_labels_payload("holdout", [_label("hotel", 0.18, [])]),
            candidate_id="spalex_blend__lsb_w090_c022__cog_l__no_guard",
            error_threshold=0.10,
            change_threshold=0.02,
            detail_limit=8,
            generated_at="2026-07-05T00:00:00+00:00",
        )

        self.assertEqual(
            report["decision"],
            "en_es_learner_difficulty_residual_patterns_ready",
        )
        self.assertEqual(report["summary"]["residual_count"], 2)
        families = {item["family"]: item for item in report["residual_families"]}
        self.assertIn("broad_learner_absent", families)
        self.assertIn("cognate_rescue_active", families)
        self.assertEqual(families["broad_learner_absent"]["too_hard_count"], 1)
        self.assertEqual(families["cognate_rescue_active"]["too_easy_count"], 1)
        routes = {item["route"]: item for item in report["component_problem_routes"]}
        self.assertIn("spoken_regional_commonness_gap", routes)
        self.assertIn("learner_cognate_over_rescue", routes)
        self.assertGreaterEqual(routes["spoken_regional_commonness_gap"]["residual_count"], 1)
        self.assertGreaterEqual(routes["learner_cognate_over_rescue"]["residual_count"], 1)
        self.assertGreaterEqual(report["candidate_vs_baseline_changes"]["regression_count"], 1)

        markdown = render_markdown(report)
        self.assertIn("en-es Learner Difficulty Residual Patterns", markdown)
        self.assertIn("Residual Families", markdown)
        self.assertIn("Component Problem Routes", markdown)
        self.assertIn("Largest Residual Rows", markdown)


def _formula_report_fixture() -> dict[str, object]:
    return {
        "decision": "fixture_formula_probe",
        "generated_at": "2026-07-05T00:00:00+00:00",
        "inputs": {"top_n": 3},
        "rows": [
            _row(
                "regional",
                baseline=0.84,
                blend=0.84,
                broad_known=False,
                marked=0.70,
                marked_terms=["slang"],
            ),
            _row(
                "parte",
                baseline=0.11,
                blend=0.24,
                broad_known=True,
                learner_gap=0.16,
                cognate=0.55,
            ),
            _row(
                "hotel",
                baseline=0.18,
                blend=0.34,
                broad_known=True,
                learner_gap=0.18,
            ),
        ],
    }


def _row(
    lemma: str,
    *,
    baseline: float,
    blend: float,
    broad_known: bool,
    learner_gap: float = 0.0,
    cognate: float = 0.0,
    marked: float = 0.0,
    marked_terms: list[str] | None = None,
) -> dict[str, object]:
    return {
        "lemma": lemma,
        "spalex_rank": 1000.0,
        "pos": "noun",
        "pos_bucket": "noun",
        "candidate_state": "normal_vocab",
        "translations": ["fixture"],
        "learner_source": (
            [{"source_id": "openlingo_mit_spanish_dictionary"}] if broad_known else []
        ),
        "learner_source_context": {
            "broad_source_available": True,
            "broad_source_known": broad_known,
            "broad_source_absent": not broad_known,
        },
        "dictionary": {
            "entry_count": 1,
            "marked_terms": marked_terms or [],
            "topics": [],
        },
        "components": {
            "zipf_base": blend,
            "spalex_blend": blend,
            "learner_core_gap_blend_confident": learner_gap,
            "learner_core_gap_zipf_confident": learner_gap,
            "learner_core_confidence": 0.74 if broad_known else 0.0,
            "cognate_rescue": cognate,
            "gated_dict_marked_usage_risk": marked,
        },
        "variant_scores": {
            "learner_source_zipf_medium": baseline,
        },
    }


def _labels_payload(payload_id: str, labels: list[dict[str, object]]) -> dict[str, object]:
    return {
        "calibration_id": payload_id,
        "holdout_id": payload_id,
        "labels": labels,
    }


def _label(lemma: str, expected: float, flags: list[str]) -> dict[str, object]:
    return {
        "lemma": lemma,
        "expected_candidate_state": "normal_vocab",
        "expected_presentation_mode": "vocab",
        "expected_problem_class": "normal_vocab",
        "expected_difficulty_band": _band(expected),
        "expected_learner_difficulty": expected,
        "review_flags": flags,
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
