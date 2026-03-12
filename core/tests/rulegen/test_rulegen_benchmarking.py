from __future__ import annotations

import os
import sys
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lexishift_core.replacement.core import RuleMetadata, VocabRule  # noqa: E402
from lexishift_core.rulegen.benchmarking import (  # noqa: E402
    RulegenBenchmarkCase,
    RulegenBenchmarkObjectiveWeights,
    evaluate_benchmark_case,
    normalize_benchmark_phrase,
    summarize_benchmark_results,
)


def _build_rule(
    source_phrase: str,
    replacement: str,
    *,
    confidence: float = 0.5,
    morphology: dict[str, object] | None = None,
) -> VocabRule:
    return VocabRule(
        source_phrase=source_phrase,
        replacement=replacement,
        metadata=RuleMetadata(
            language_pair="en-es",
            confidence=confidence,
            morphology=morphology,
        ),
    )


class TestRulegenBenchmarking(unittest.TestCase):
    def test_normalize_benchmark_phrase_collapses_case_and_spacing(self) -> None:
        self.assertEqual(normalize_benchmark_phrase("  HOuR   "), "hour")
        self.assertEqual(normalize_benchmark_phrase("look   like"), "look like")

    def test_evaluate_case_tracks_expected_and_forbidden_hits(self) -> None:
        case = RulegenBenchmarkCase(
            case_id="en-es:hora",
            pair="en-es",
            target="hora",
            expected_any=("hour", "time"),
            expected_top1_any=("hour",),
            forbidden_top1=("times",),
            forbidden_any=("times",),
        )
        rules = [
            _build_rule("hour", "hora", confidence=0.9),
            _build_rule(
                "hours",
                "hora",
                confidence=0.4,
                morphology={
                    "source_form": "plural",
                    "target_surface": "horas",
                    "target_lemma": "hora",
                },
            ),
        ]

        result = evaluate_benchmark_case(case, rules)

        self.assertEqual(result.top1_source, "hour")
        self.assertEqual(result.top3_sources, ("hour", "hours"))
        self.assertTrue(result.top1_correct)
        self.assertTrue(result.top3_contains_expected)
        self.assertFalse(result.top1_forbidden)
        self.assertFalse(result.forbidden_any_present)
        self.assertEqual(result.variant_rule_count, 1)
        self.assertFalse(result.top1_is_variant)

    def test_summary_computes_rates_and_objective(self) -> None:
        case_a = RulegenBenchmarkCase(
            case_id="a",
            pair="en-es",
            target="hora",
            expected_any=("hour",),
            forbidden_top1=("times",),
            forbidden_any=("times",),
        )
        case_b = RulegenBenchmarkCase(
            case_id="b",
            pair="en-es",
            target="trabajo",
            expected_any=("work", "job"),
            forbidden_top1=("laboring",),
            forbidden_any=("laboring",),
        )
        result_a = evaluate_benchmark_case(case_a, [_build_rule("hour", "hora", confidence=0.9)])
        result_b = evaluate_benchmark_case(
            case_b,
            [
                _build_rule(
                    "laboring",
                    "trabajo",
                    confidence=0.5,
                    morphology={
                        "source_form": "plural",
                        "target_surface": "trabajos",
                        "target_lemma": "trabajo",
                    },
                )
            ],
        )
        summary = summarize_benchmark_results(
            pair="en-es",
            case_results=[result_a, result_b],
            objective_weights=RulegenBenchmarkObjectiveWeights(
                top1_accuracy=100.0,
                top3_recall=50.0,
                forbidden_top1_rate=100.0,
                forbidden_any_rate=50.0,
                avg_rules_per_target=0.0,
                variant_top1_rate=0.0,
            ),
        )

        self.assertEqual(summary.case_count, 2)
        self.assertEqual(summary.top1_correct_count, 1)
        self.assertEqual(summary.top3_contains_expected_count, 1)
        self.assertEqual(summary.forbidden_top1_count, 1)
        self.assertEqual(summary.forbidden_any_count, 1)
        self.assertAlmostEqual(summary.top1_accuracy, 0.5, places=6)
        self.assertAlmostEqual(summary.top3_recall, 0.5, places=6)
        self.assertAlmostEqual(summary.forbidden_top1_rate, 0.5, places=6)
        self.assertAlmostEqual(summary.forbidden_any_rate, 0.5, places=6)
        self.assertEqual(summary.variant_rule_count, 1)
        self.assertEqual(summary.total_rule_count, 2)
        self.assertAlmostEqual(summary.objective_score, 0.0, places=6)


if __name__ == "__main__":
    unittest.main()
