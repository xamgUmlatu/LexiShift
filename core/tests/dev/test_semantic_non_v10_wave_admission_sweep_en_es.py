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

from semantic_non_v10_wave_admission_sweep_en_es import (  # noqa: E402
    _admission_selected_dataset,
    _admission_selected_queue,
    _best_variant,
    _parse_evidence_config,
    _semantic_portfolio,
    render_non_v10_wave_admission_sweep_markdown,
)


class SemanticNonV10WaveAdmissionSweepTests(unittest.TestCase):
    def test_best_variant_prefers_semantic_completion_then_admitted_rows(self) -> None:
        rows = [
            {
                "variant_id": "low",
                "semantic_contract_complete_family_count": 5,
                "final_admitted_row_count": 30,
                "sense_rejected_row_count": 1,
                "wordnet_row_count": 40,
                "selected_family_count": 8,
            },
            {
                "variant_id": "high",
                "semantic_contract_complete_family_count": 6,
                "final_admitted_row_count": 20,
                "sense_rejected_row_count": 8,
                "wordnet_row_count": 30,
                "selected_family_count": 8,
            },
        ]

        self.assertEqual(_best_variant(rows)["variant_id"], "high")

    def test_render_sweep_markdown_surfaces_best_variant_and_gaps(self) -> None:
        report = {
            "status": "review",
            "decision": "semantic_gaps_remain",
            "generated_at": "2026-04-28T00:00:00Z",
            "summary": {
                "variant_count": 1,
                "requested_pool_size": 8,
                "selection_size": 8,
                "best_variant_id": "min0p12-definition_and_example-rows2",
                "best_semantic_contract_complete_family_count": 6,
                "best_final_admitted_row_count": 26,
                "best_phrase_contract_complete_family_count": 0,
                "best_admission_selected_family_count": 6,
                "admission_selected_family_count": 8,
                "selection_strategy": "portfolio",
                "portfolio_semantic_complete_family_count": 8,
                "translation_support_mode": "forward_only_upper_bound",
            },
            "best_variant": {
                "variant_id": "min0p12-definition_and_example-rows2",
                "selected_triggers": ["change", "look"],
                "admission_selected_triggers": ["look"],
                "wordnet_row_count": 36,
                "final_admitted_row_count": 26,
                "semantic_contract_complete_family_count": 6,
                "phrase_contract_complete_family_count": 0,
                "semantic_gap_family_keys": ["en-es:sentence-veto:change:cambio"],
            },
            "semantic_portfolio": {
                "semantic_complete_family_count": 8,
                "semantic_complete_family_keys": ["en-es:sentence-veto:look:aspecto"],
                "semantic_complete_triggers": ["look"],
                "admission_selected_family_keys": ["en-es:sentence-veto:look:aspecto"],
                "admission_selected_triggers": ["look"],
            },
            "variant_rows": [
                {
                    "variant_id": "min0p12-definition_and_example-rows2",
                    "is_best": True,
                    "extraction_min_link_score": 0.12,
                    "selected_family_count": 8,
                    "wordnet_row_count": 36,
                    "final_admitted_row_count": 26,
                    "sense_rejected_row_count": 10,
                    "semantic_contract_complete_family_count": 6,
                    "phrase_contract_complete_family_count": 0,
                }
            ],
            "limitations": ["draft_waves_are_unreviewed_and_not_promotion_candidates"],
            "next_steps": ["add independent held-out cases before any promotion claim"],
        }

        markdown = render_non_v10_wave_admission_sweep_markdown(report)

        self.assertIn("Best variant: `min0p12-definition_and_example-rows2`", markdown)
        self.assertIn("Translation support mode: `forward_only_upper_bound`", markdown)
        self.assertIn("Selection strategy: `portfolio`", markdown)
        self.assertIn("Admission-selected triggers: `look`", markdown)
        self.assertIn("Semantic gaps: `en-es:sentence-veto:change:cambio`", markdown)

    def test_parse_evidence_config(self) -> None:
        config = _parse_evidence_config("definition_and_example:2:0")

        self.assertEqual(config.mode, "definition_and_example")
        self.assertEqual(config.max_rows_per_sense, 2)
        self.assertEqual(config.extraction_min_link_score, 0.0)

    def test_selected_outputs_use_explicit_ids(self) -> None:
        families = [{"family_id": "fam:look", "trigger": "look"}]
        dataset = _admission_selected_dataset(
            families,
            best_variant={
                "variant_id": "best",
                "semantic_contract_complete_family_count": 1,
                "translation_support_mode": "forward_only_upper_bound",
            },
            selection_size=1,
            selection_strategy="portfolio",
            dataset_id="custom_dataset",
            generated_at="2026-04-28T00:00:00Z",
        )
        queue = _admission_selected_queue(
            families,
            best_variant={
                "variant_id": "best",
                "translation_support_mode": "forward_only_upper_bound",
            },
            dataset_id="custom_dataset",
            queue_id="custom_queue",
            selection_strategy="portfolio",
            generated_at="2026-04-28T00:00:00Z",
        )

        self.assertEqual(dataset["dataset_id"], "custom_dataset")
        self.assertEqual(dataset["source_sweep_selection_strategy"], "portfolio")
        self.assertEqual(dataset["translation_support_mode"], "forward_only_upper_bound")
        self.assertEqual(queue["dataset_id"], "custom_dataset")
        self.assertEqual(queue["queue_id"], "custom_queue")
        self.assertEqual(queue["source_sweep_selection_strategy"], "portfolio")
        self.assertEqual(queue["translation_support_mode"], "forward_only_upper_bound")

    def test_semantic_portfolio_unions_complete_families_across_variants(self) -> None:
        portfolio = _semantic_portfolio(
            [
                {
                    "variant_id": "a",
                    "selected_family_keys": ["fam:one", "fam:two"],
                    "selected_triggers": ["one", "two"],
                    "semantic_complete_family_keys": ["fam:one"],
                },
                {
                    "variant_id": "b",
                    "selected_family_keys": ["fam:one", "fam:two"],
                    "selected_triggers": ["one", "two"],
                    "semantic_complete_family_keys": ["fam:two"],
                },
            ]
        )

        self.assertEqual(portfolio["semantic_complete_family_count"], 2)
        self.assertEqual(portfolio["semantic_complete_family_keys"], ["fam:one", "fam:two"])
        self.assertEqual(portfolio["semantic_complete_triggers"], ["one", "two"])
        self.assertEqual(
            portfolio["supporting_variant_ids_by_family_key"],
            {"fam:one": ["a"], "fam:two": ["b"]},
        )


if __name__ == "__main__":
    unittest.main()
