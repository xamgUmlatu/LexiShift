from __future__ import annotations

from pathlib import Path
import sys
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_learner_difficulty_formula_sweep_en_de import (  # noqa: E402
    _build_product_objective_context,
    _evaluate_sentinel_objective,
    _score_row,
    _select_candidates,
    build_report,
    generate_candidates,
    render_markdown,
)


class SrsLearnerDifficultyFormulaSweepEnDeTests(unittest.TestCase):
    def test_builds_sweep_report_and_excludes_restricted_null_labels(self) -> None:
        report = build_report(
            signal_rows=_signal_rows_fixture(),
            calibration_payload={
                "calibration_id": "fixture_cal",
                "labels": [
                    _label(1, "haus", 0.08, "beginner"),
                    _label(2, "problem", 0.12, "beginner"),
                    _label(4, "langwort", 0.78, "advanced"),
                ],
            },
            holdout_payload={
                "holdout_id": "fixture_holdout",
                "labels": [
                    _label(3, "artifact", None, None, state="restricted_admission"),
                    _label(5, "katze", 0.08, "beginner"),
                ],
            },
            max_candidates=20,
            candidate_sample_mode="head",
            generated_at="2026-07-06T00:00:00+00:00",
        )

        self.assertEqual(report["decision"], "en_de_learner_difficulty_formula_sweep_ready")
        self.assertFalse(report["runtime_behavior_changed"])
        self.assertFalse(report["production_ranking_changed"])
        self.assertEqual(report["inputs"]["calibration_count"], 3)
        self.assertEqual(report["inputs"]["holdout_count"], 2)
        self.assertEqual(report["method"]["candidate_count"], 20)
        self.assertGreater(len(generate_candidates()), 20)
        self.assertTrue(
            any("learner" in candidate.candidate_id for candidate in generate_candidates())
        )

        best = report["summary"]["best_calibration_candidate"]
        self.assertIsInstance(best["candidate_id"], str)
        self.assertTrue(best["candidate_id"])
        self.assertEqual(
            report["summary"]["raw_frequency_baseline"]["candidate_id"],
            "raw_frequency_blend",
        )
        self.assertEqual(
            report["leaderboards"]["calibration_top"][0]["calibration_primary"]["label_count"],
            3,
        )
        self.assertEqual(
            report["leaderboards"]["calibration_top"][0]["holdout_primary"]["label_count"],
            1,
        )

        markdown = render_markdown(report)
        self.assertIn("en-de Learner Difficulty Formula Sweep", markdown)
        self.assertIn("Calibration Top", markdown)
        self.assertIn("Candidate grid", markdown)

    def test_coarse_candidate_sampling_spreads_across_grid(self) -> None:
        candidates = list(generate_candidates())
        sampled = _select_candidates(candidates, max_candidates=50, sample_mode="coarse")
        sampled_ids = [candidate.candidate_id for candidate in sampled]

        self.assertEqual(len(sampled), 50)
        self.assertEqual(sampled_ids[0], "raw_frequency_blend")
        self.assertTrue(any("_modern20_" in candidate_id for candidate_id in sampled_ids))
        self.assertTrue(any("_src0_" in candidate_id for candidate_id in sampled_ids))
        self.assertTrue(any("_wf22_" in candidate_id for candidate_id in sampled_ids))
        self.assertNotEqual(
            sampled_ids,
            [candidate.candidate_id for candidate in candidates[:50]],
        )

    def test_candidate_grid_exposes_new_source_shapes(self) -> None:
        candidate_ids = {candidate.candidate_id for candidate in generate_candidates()}

        self.assertTrue(any("_src0_" in candidate_id for candidate_id in candidate_ids))
        self.assertTrue(any("_wf22_" in candidate_id for candidate_id in candidate_ids))
        self.assertTrue(any("_modern20_" in candidate_id for candidate_id in candidate_ids))
        self.assertTrue(any("_goethea1_60_" in candidate_id for candidate_id in candidate_ids))
        self.assertTrue(
            any("_modern_child_tail_" in candidate_id for candidate_id in candidate_ids)
        )
        self.assertTrue(any("_absence_medium" in candidate_id for candidate_id in candidate_ids))
        self.assertTrue(any("_learnbackoff" in candidate_id for candidate_id in candidate_ids))
        self.assertTrue(any("_sensepos" in candidate_id for candidate_id in candidate_ids))
        self.assertTrue(any("_domaincmp" in candidate_id for candidate_id in candidate_ids))
        self.assertTrue(any("_function" in candidate_id for candidate_id in candidate_ids))
        self.assertTrue(any("_smartguards" in candidate_id for candidate_id in candidate_ids))
        self.assertTrue(any("_struct" in candidate_id for candidate_id in candidate_ids))
        self.assertTrue(
            any("_struct_floors_medium" in candidate_id for candidate_id in candidate_ids)
        )
        self.assertTrue(
            any("_struct_floors_domain_strong" in candidate_id for candidate_id in candidate_ids)
        )
        self.assertTrue(
            any(
                "_struct_floors_sense_poly_strong" in candidate_id for candidate_id in candidate_ids
            )
        )

    def test_product_objective_adds_sidecar_selection_metrics(self) -> None:
        report = build_report(
            signal_rows=_signal_rows_fixture(),
            calibration_payload={
                "labels": [
                    _label(1, "haus", 0.08, "beginner"),
                    _label(2, "problem", 0.12, "beginner"),
                    _label(4, "langwort", 0.78, "advanced"),
                ]
            },
            holdout_payload={
                "labels": [
                    _label(3, "artifact", None, None, state="restricted_admission"),
                    _label(5, "katze", 0.08, "beginner"),
                ]
            },
            product_objective_payload={
                "objective_id": "fixture_product_objective",
                "distribution": {
                    "target_decile_weights": [0.1] * 10,
                    "cdf_tolerance": 0.25,
                },
                "selection_weight": 0.2,
                "objective_weights": {"distribution": 0.4, "sentinel": 0.6},
                "default_sentinel_margin": 0.1,
                "sentinels": [
                    {"lemma": "katze", "ceiling": 0.2, "cohort": "beginner_rescue"},
                    {"lemma": "langwort", "floor": 0.7, "cohort": "tail_guard"},
                ],
            },
            product_objective_sample_size=5,
            max_candidates=6,
            candidate_sample_mode="head",
            generated_at="2026-07-06T00:00:00+00:00",
        )

        self.assertEqual(report["inputs"]["product_objective_id"], "fixture_product_objective")
        self.assertEqual(report["inputs"]["product_sentinel_count"], 2)
        self.assertEqual(report["inputs"]["product_distribution_sample_count"], 5)
        self.assertIn("product_top", report["leaderboards"])

        best_product = report["summary"]["best_product_candidate"]
        self.assertIsNotNone(best_product["product_objective_score"])
        self.assertIsNotNone(best_product["product_stable_score"])

        top_record = report["leaderboards"]["product_top"][0]
        product_objective = top_record["product_objective"]
        self.assertTrue(product_objective["enabled"])
        self.assertIn("sentinel", product_objective)
        sentinel = product_objective["sentinel"]
        self.assertIn("mean_score", sentinel)
        self.assertIn("cohort_balanced_score", sentinel)
        self.assertIn("severe_violation_score", sentinel)
        self.assertIn("worst_violation_score", sentinel)

        markdown = render_markdown(report)
        self.assertIn("best product-aware", markdown)
        self.assertIn("Product-Aware Top", markdown)
        self.assertIn("Sentinel components", markdown)

    def test_sentinel_policy_penalizes_severe_cohort_failures(self) -> None:
        rows = [
            _row(f"easy{i}", 0.10, rank=0.10, pmw=0.10, translations=(f"easy {i}",))
            for i in range(9)
        ]
        rows.append(_row("tailmiss", 0.10, rank=0.10, pmw=0.10, translations=("tail miss",)))
        rows_by_lemma = {str(row["lemma"]): row for row in rows}
        context = _build_product_objective_context(
            rows=rows,
            rows_by_lemma=rows_by_lemma,
            payload={
                "objective_id": "fixture",
                "sentinel_policy": {
                    "component_weights": {
                        "mean": 0.4,
                        "cohort_balanced": 0.3,
                        "severe_violation": 0.15,
                        "worst_violation": 0.15,
                    },
                    "severe_threshold": 1.0,
                    "severe_violation_budget": 4.0,
                    "worst_violation_tolerance": 2.0,
                },
                "sentinels": [
                    {
                        "lemma": f"easy{i}",
                        "ceiling": 0.30,
                        "cohort": "beginner_rescue",
                    }
                    for i in range(9)
                ]
                + [
                    {
                        "lemma": "tailmiss",
                        "floor": 0.30,
                        "cohort": "tail_guard",
                    }
                ],
            },
            sample_size=0,
        )
        raw_candidate = next(
            candidate
            for candidate in generate_candidates()
            if candidate.candidate_id == "raw_frequency_blend"
        )

        sentinel = _evaluate_sentinel_objective(candidate=raw_candidate, product_context=context)

        self.assertEqual(sentinel["severe_violation_count"], 1)
        self.assertAlmostEqual(float(sentinel["worst_normalized_violation"]), 2.0)
        self.assertLess(float(sentinel["score"]), float(sentinel["mean_score"]))

    def test_refined_candidate_grid_targets_coarse_winner_neighborhood(self) -> None:
        broad_ids = {candidate.candidate_id for candidate in generate_candidates("broad")}
        refined = generate_candidates("refined")
        refined_ids = {candidate.candidate_id for candidate in refined}

        self.assertLess(len(refined), len(broad_ids))
        self.assertIn(
            "rw075_rg135_pg100_wg112_wf10_pedagogical_mix_long16_poly04",
            refined_ids,
        )
        self.assertIn(
            "rw065_rg150_pg120_wg108_modern20_pedmix_strong_tail_medium",
            refined_ids,
        )
        self.assertTrue(any("_wf06_" in candidate_id for candidate_id in refined_ids))
        self.assertTrue(any("_modern28_" in candidate_id for candidate_id in refined_ids))
        self.assertFalse(any("_klexikon_cap" in candidate_id for candidate_id in refined_ids))

    def test_floor_refined_candidate_grid_targets_structural_floor_region(self) -> None:
        refined = generate_candidates("refined")
        floor_refined = generate_candidates("floor_refined")
        floor_ids = {candidate.candidate_id for candidate in floor_refined}

        self.assertLess(len(floor_refined), len(refined))
        self.assertTrue(any("_struct_floors_light" in candidate_id for candidate_id in floor_ids))
        self.assertTrue(any("_struct_floors_medium" in candidate_id for candidate_id in floor_ids))
        self.assertTrue(
            any("_struct_floors_balanced_high" in candidate_id for candidate_id in floor_ids)
        )
        self.assertTrue(any("_wf22_" in candidate_id for candidate_id in floor_ids))
        self.assertTrue(any("_modern20_" in candidate_id for candidate_id in floor_ids))
        self.assertTrue(any("_learnercore50_" in candidate_id for candidate_id in floor_ids))

    def test_source_soft_ceilings_and_modern_base_scores_are_active(self) -> None:
        row = _row(
            "gehen",
            0.80,
            rank=0.80,
            pmw=0.80,
            translations=("go",),
            learner_known=1.0,
            learner_score=0.08,
            learner_confidence=1.0,
            goethe_a1_known=1.0,
            goethe_a1_score=0.08,
            goethe_a1_confidence=1.0,
            wordfreq_known=1.0,
            wordfreq_commonness=0.90,
            subtitles_known=1.0,
            subtitles_commonness=0.75,
            klexikon_known=1.0,
        )
        plain_candidate = _candidate_with("_src0_ease0_guard0")
        wordfreq_candidate = _candidate_with("_wf22_ease0_guard0")
        goethe_candidate = _candidate_with("_src0_goethea1_60_guard0")
        klexikon_candidate = _candidate_with("_src0_klexikon_cap25_guard0")

        plain_score = _score_row(plain_candidate, row)
        wordfreq_score = _score_row(wordfreq_candidate, row)
        goethe_score = _score_row(goethe_candidate, row)
        klexikon_score = _score_row(klexikon_candidate, row)

        self.assertIsNotNone(plain_score)
        self.assertIsNotNone(wordfreq_score)
        self.assertIsNotNone(goethe_score)
        self.assertIsNotNone(klexikon_score)
        self.assertLess(wordfreq_score, plain_score)
        self.assertLess(goethe_score, plain_score)
        self.assertLess(klexikon_score, plain_score)

    def test_new_guard_components_raise_targeted_failure_shapes(self) -> None:
        domain_row = _row(
            "bundesverfassungsgericht",
            0.68,
            rank=0.68,
            pmw=0.62,
            length=1.0,
            compound=1.0,
            translations=("federal constitutional court",),
        )
        sense_row = _row(
            "tagen",
            0.34,
            rank=0.34,
            pmw=0.28,
            pos=("SUB:NOM:SIN:NEU:INF|VER:1:PLU:PRÄ:SFT|VER:3:PLU:PRÄ:SFT|VER:INF:SFT"),
            translations=("meet", "convene", "session", "sitting", "meeting", "hold"),
            learner_known=1.0,
            learner_score=0.32,
            learner_confidence=1.0,
        )
        function_row = _row(
            "zwar",
            0.26,
            rank=0.26,
            pmw=0.20,
            pos="ADV:CAU",
            pos_bucket="adverb",
            translations=(),
            learner_known=1.0,
            learner_score=0.32,
            learner_confidence=1.0,
        )
        learner_backoff_row = _row(
            "ausmachen",
            0.58,
            rank=0.58,
            pmw=0.50,
            pos="SUB:NOM:SIN:NEU:INF|VER:INF:SFT",
            translations=("turn off", "constitute", "spot", "distinguish", "douse"),
            learner_known=1.0,
            learner_score=0.08,
            learner_confidence=1.0,
        )

        plain = _candidate_with("_src0_ease0_guard0")
        domain_guard = _candidate_with("_src0_ease0_domaincmp12")
        sense_guard = _candidate_with("_src0_ease0_sensepos08_poly04")
        function_guard = _candidate_with("_src0_ease0_function08_sense04")
        learner_plain = _candidate_with("_src0_learnercore45_guard0")
        learner_backoff = _candidate_with("_src0_learnercore45_learnbackoff06")

        self.assertGreater(_score_row(domain_guard, domain_row), _score_row(plain, domain_row))
        self.assertGreater(_score_row(sense_guard, sense_row), _score_row(plain, sense_row))
        self.assertGreater(
            _score_row(function_guard, function_row), _score_row(plain, function_row)
        )
        self.assertGreater(
            _score_row(learner_backoff, learner_backoff_row),
            _score_row(learner_plain, learner_backoff_row),
        )

    def test_structural_guards_back_off_ease_and_apply_bounded_floors(self) -> None:
        ambiguous_learner_row = _row(
            "ausmachen",
            0.58,
            rank=0.58,
            pmw=0.50,
            pos="SUB:NOM:SIN:NEU:INF|VER:INF:SFT",
            translations=("turn off", "constitute", "spot", "distinguish", "douse"),
            learner_known=1.0,
            learner_score=0.08,
            learner_confidence=1.0,
        )
        domain_row = _row(
            "bundesverfassungsgericht",
            0.68,
            rank=0.68,
            pmw=0.62,
            length=1.0,
            compound=1.0,
            translations=("federal constitutional court",),
        )

        learner_plain = _candidate_with("_src0_learnercore45_guard0")
        learner_structural = _candidate_with("_src0_learnercore45_struct_combo_medium")
        plain = _candidate_with("_src0_ease0_guard0")
        structural = _candidate_with("_src0_ease0_struct_combo_medium")

        self.assertGreater(
            _score_row(learner_structural, ambiguous_learner_row),
            _score_row(learner_plain, ambiguous_learner_row),
        )
        self.assertGreater(
            _score_row(structural, domain_row),
            _score_row(plain, domain_row),
        )
        self.assertLessEqual(
            _score_row(structural, domain_row) - _score_row(plain, domain_row),
            0.20,
        )


def _signal_rows_fixture() -> list[dict[str, object]]:
    return [
        _row("haus", 0.05, rank=0.05, pmw=0.05, translations=("house",)),
        _row("problem", 0.18, rank=0.20, pmw=0.16, sim=0.95, translations=("problem",)),
        _row("artifact", 0.10, rank=0.10, pmw=0.10, translations=()),
        _row(
            "langwort",
            0.78,
            rank=0.78,
            pmw=0.76,
            length=0.70,
            compound=1.0,
            translations=("long word",),
        ),
        _row("katze", 0.62, rank=0.62, pmw=0.62, translations=("cat",)),
    ]


def _row(
    lemma: str,
    base: float,
    *,
    rank: float,
    pmw: float,
    sim: float = 0.0,
    length: float = 0.0,
    compound: float = 0.0,
    translations: tuple[str, ...],
    learner_known: float = 0.0,
    learner_score: float = 0.0,
    learner_confidence: float = 0.0,
    goethe_a1_known: float = 0.0,
    goethe_a1_score: float = 0.0,
    goethe_a1_confidence: float = 0.0,
    goethe_stem_known: float = 0.0,
    goethe_stem_score: float = 0.0,
    goethe_stem_confidence: float = 0.0,
    wordfreq_known: float = 0.0,
    wordfreq_commonness: float = 0.0,
    subtitles_known: float = 0.0,
    subtitles_commonness: float = 0.0,
    klexikon_known: float = 0.0,
    pos: str = "SUB:NOM:SIN:NEU",
    pos_bucket: str = "noun",
    topic_documented: float = 0.0,
) -> dict[str, object]:
    return {
        "lemma": lemma,
        "frequency_blend": base,
        "rank_base": rank,
        "pmw_base": pmw,
        "pos": pos,
        "pos_bucket": pos_bucket,
        "content_pos_gate": 1.0,
        "other_pos_risk": 0.0,
        "length_risk": length,
        "compound_like": compound,
        "topic_documented": topic_documented,
        "translation_count": len(translations),
        "translation_count_score": min(1.0, len(translations) / 8.0),
        "translations": list(translations),
        "english_translation_tokens": [token for text in translations for token in text.split()],
        "english_translation_frequency_ease": 0.8 if translations else 0.0,
        "english_translation_similarity_ease": sim,
        "reverse_support_count": len(translations),
        "reverse_support_score": min(1.0, len(translations) / 3.0),
        "reverse_support_terms": list(translations),
        "learner_source_known": learner_known,
        "learner_core_score": learner_score,
        "learner_source_confidence": learner_confidence,
        "broad_learner_source_absent": 1.0 if learner_known <= 0.0 else 0.0,
        "openlingo_learner_source_known": learner_known,
        "openlingo_learner_core_score": learner_score,
        "openlingo_learner_source_confidence": learner_confidence,
        "goethe_official_a1_learner_source_known": goethe_a1_known,
        "goethe_official_a1_learner_core_score": goethe_a1_score,
        "goethe_official_a1_learner_source_confidence": goethe_a1_confidence,
        "goethe_stem_learner_source_known": goethe_stem_known,
        "goethe_stem_learner_core_score": goethe_stem_score,
        "goethe_stem_learner_source_confidence": goethe_stem_confidence,
        "odenet_basis_learner_source_known": 0.0,
        "odenet_basis_learner_core_score": 0.0,
        "odenet_basis_learner_source_confidence": 0.0,
        "external_modern_source_known": 1.0 if wordfreq_known or subtitles_known else 0.0,
        "external_modern_frequency_score": max(wordfreq_commonness, subtitles_commonness),
        "wordfreq_de_known": wordfreq_known,
        "wordfreq_de_commonness_score": wordfreq_commonness,
        "opensubtitles_cistem_known": subtitles_known,
        "opensubtitles_cistem_frequency_score": subtitles_commonness,
        "klexikon_title_known": klexikon_known,
        "wiktionary_entry_count": 1,
        "wiktionary_pos_count": 1,
        "wiktionary_sense_count_score": 0.0,
    }


def _candidate_with(fragment: str):
    for candidate in generate_candidates():
        if fragment in candidate.candidate_id:
            return candidate
    raise AssertionError(f"candidate not found: {fragment}")


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
