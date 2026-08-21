from __future__ import annotations

from pathlib import Path
import sys
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_learner_difficulty_source_shape_breadth_sweep_en_de import (  # noqa: E402
    SOURCE_GROUPS,
    _score_row,
    build_report,
    generate_candidates,
    generate_source_shapes,
    render_markdown,
)


class SrsLearnerDifficultySourceShapeBreadthSweepEnDeTests(unittest.TestCase):
    def test_builds_breadth_report_with_source_family_diagnostics(self) -> None:
        report = build_report(
            signal_rows=_signal_rows_fixture(),
            calibration_payload={
                "calibration_id": "fixture_cal",
                "labels": [
                    _label(1, "haus", 0.08, "beginner"),
                    _label(2, "basiswort", 0.22, "core"),
                    _label(3, "stammwort", 0.32, "core"),
                    _label(4, "altertum", 0.76, "advanced"),
                ],
            },
            holdout_payload={
                "holdout_id": "fixture_holdout",
                "labels": [
                    _label(5, "konfliktwort", 0.62, "advanced"),
                    _label(6, "artifact", None, None, state="restricted_admission"),
                ],
            },
            max_candidates=30,
            generated_at="2026-07-06T00:00:00+00:00",
        )

        self.assertEqual(
            report["decision"],
            "en_de_learner_difficulty_source_shape_breadth_sweep_ready",
        )
        self.assertFalse(report["runtime_behavior_changed"])
        self.assertFalse(report["production_ranking_changed"])
        self.assertEqual(report["method"]["candidate_count"], 30)
        self.assertGreater(len(generate_candidates()), 30)
        self.assertIn("source_conflict", report["method"]["shape_families"])
        self.assertIn("wiktionary_guard", report["method"]["shape_families"])
        self.assertIn("source_conflict", SOURCE_GROUPS)
        self.assertGreater(len(generate_source_shapes()), 10)

        summary = report["summary"]
        self.assertEqual(
            summary["raw_frequency_baseline"]["candidate_id"],
            "raw_frequency_blend__none",
        )
        self.assertEqual(
            summary["legacy_current_formula_analog"]["candidate_id"],
            "current_best_curve__legacy_openlingo50_floor25",
        )
        self.assertTrue(summary["best_stable_candidate"]["candidate_id"])

        family_rows = report["leaderboards"]["best_by_source_family"]
        self.assertTrue(any(row["source_family"] == "legacy_openlingo" for row in family_rows))

        selected = report["selected_candidate_details"][0]
        self.assertIn("source_group_shift_summary", selected)
        self.assertIn("openlingo_known", selected["source_group_shift_summary"])
        self.assertIn("largest_base_shifts", selected)
        self.assertEqual(
            report["leaderboards"]["calibration_top"][0]["calibration_primary"]["label_count"],
            4,
        )
        self.assertEqual(
            report["leaderboards"]["calibration_top"][0]["holdout_primary"]["label_count"],
            1,
        )

        markdown = render_markdown(report)
        self.assertIn("en-de Learner Difficulty Source-Shape Breadth Sweep", markdown)
        self.assertIn("Best By Source Family", markdown)
        self.assertIn("Source-group shifts", markdown)

    def test_openlingo_cap_does_not_move_goethe_only_rows(self) -> None:
        rows = {str(row["lemma"]): row for row in _signal_rows_fixture()}
        candidates = {candidate.candidate_id: candidate for candidate in generate_candidates()}

        none = candidates["raw_frequency_blend__none"]
        cap = candidates["raw_frequency_blend__openlingo_cap_strong"]

        self.assertLess(_score_row(cap, rows["haus"]), _score_row(none, rows["haus"]))
        self.assertEqual(
            _score_row(cap, rows["stammwort"]),
            _score_row(none, rows["stammwort"]),
        )


def _signal_rows_fixture() -> list[dict[str, object]]:
    return [
        _row(
            "haus",
            0.22,
            rank=0.22,
            pmw=0.20,
            translations=("house",),
            openlingo=(0.08, 0.82),
        ),
        _row(
            "basiswort",
            0.58,
            rank=0.58,
            pmw=0.56,
            translations=("basic word",),
            odenet=(0.18, 0.55),
        ),
        _row(
            "stammwort",
            0.62,
            rank=0.62,
            pmw=0.60,
            translations=("stem word",),
            goethe=(0.28, 0.30),
        ),
        _row(
            "altertum",
            0.50,
            rank=0.50,
            pmw=0.50,
            translations=("antiquity",),
            wiktionary_rare=1.0,
            wiktionary_marked=1.0,
        ),
        _row(
            "konfliktwort",
            0.42,
            rank=0.42,
            pmw=0.42,
            translations=("conflict word",),
            openlingo=(0.12, 0.82),
            wiktionary_form=0.8,
        ),
        _row("artifact", 0.18, rank=0.18, pmw=0.18, translations=()),
    ]


def _row(
    lemma: str,
    base: float,
    *,
    rank: float,
    pmw: float,
    translations: tuple[str, ...],
    openlingo: tuple[float, float] | None = None,
    odenet: tuple[float, float] | None = None,
    goethe: tuple[float, float] | None = None,
    wiktionary_rare: float = 0.0,
    wiktionary_marked: float = 0.0,
    wiktionary_form: float = 0.0,
) -> dict[str, object]:
    learner_known = any(source is not None for source in (openlingo, odenet, goethe))
    return {
        "language_pair": "en-de",
        "lemma": lemma,
        "frequency_blend": base,
        "rank_base": rank,
        "pmw_base": pmw,
        "pos": "SUB:NOM:SIN:NEU",
        "pos_bucket": "noun",
        "content_pos_gate": 1.0,
        "topic_documented": 0.0,
        "translation_count": len(translations),
        "translation_count_score": min(1.0, len(translations) / 8.0),
        "translations": list(translations),
        "english_translation_tokens": [token for text in translations for token in text.split()],
        "english_translation_frequency_ease": 0.8 if translations else 0.0,
        "english_translation_similarity_ease": 0.0,
        "reverse_support_count": len(translations),
        "reverse_support_score": min(1.0, len(translations) / 3.0),
        "learner_source_known": 1.0 if learner_known else 0.0,
        "openlingo_learner_source_known": 1.0 if openlingo else 0.0,
        "openlingo_learner_core_score": openlingo[0] if openlingo else 0.0,
        "openlingo_learner_source_confidence": openlingo[1] if openlingo else 0.0,
        "odenet_basis_learner_source_known": 1.0 if odenet else 0.0,
        "odenet_basis_learner_core_score": odenet[0] if odenet else 0.0,
        "odenet_basis_learner_source_confidence": odenet[1] if odenet else 0.0,
        "goethe_stem_learner_source_known": 1.0 if goethe else 0.0,
        "goethe_stem_learner_core_score": goethe[0] if goethe else 0.0,
        "goethe_stem_learner_source_confidence": goethe[1] if goethe else 0.0,
        "wiktionary_metadata_known": 1.0,
        "wiktionary_marked_usage_flag": wiktionary_marked,
        "wiktionary_rare_dated_flag": wiktionary_rare,
        "wiktionary_sensitive_flag": 0.0,
        "wiktionary_form_variant_score": wiktionary_form,
        "wiktionary_sense_count_score": 0.2,
    }


def _label(
    number: int,
    lemma: str,
    expected: float | None,
    band: str | None,
    *,
    state: str = "normal_vocab",
) -> dict[str, object]:
    return {
        "review_number": number,
        "lemma": lemma,
        "expected_learner_difficulty": expected,
        "expected_difficulty_band": band,
        "expected_candidate_state": state,
        "review_flags": [],
    }


if __name__ == "__main__":
    unittest.main()
