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

from semantic_non_v10_source_portfolio_materialize_en_es import (  # noqa: E402
    _choose_supporting_variants,
    _materialization_report,
    _materialized_candidate_batch,
    _materialized_selected_payloads,
    _variant_specs_by_id,
    render_source_portfolio_materialization_markdown,
)


class SemanticNonV10SourcePortfolioMaterializeTests(unittest.TestCase):
    def test_choose_supporting_variants_prefers_best_when_available(self) -> None:
        choices = _choose_supporting_variants(
            selected_keys=["fam:one", "fam:two"],
            support_by_family={
                "fam:one": ["simple", "best"],
                "fam:two": ["fallback"],
            },
            best_variant_id="best",
        )

        self.assertEqual(choices, {"fam:one": "best", "fam:two": "fallback"})

    def test_variant_specs_by_id_preserves_extraction_score(self) -> None:
        specs = _variant_specs_by_id(
            [
                {
                    "variant_id": "min0p12-extract0-definition_and_example-rows2",
                    "min_link_score": 0.12,
                    "extraction_min_link_score": 0.0,
                    "evidence_mode": "definition_and_example",
                    "max_rows_per_sense": 2,
                }
            ]
        )

        self.assertEqual(
            specs["min0p12-extract0-definition_and_example-rows2"]["min_link_score"], 0.12
        )
        self.assertEqual(
            specs["min0p12-extract0-definition_and_example-rows2"]["extraction_min_link_score"],
            0.0,
        )

    def test_materialized_candidate_batch_keeps_only_chosen_family_rows(self) -> None:
        row_one = {
            "row_id": "one",
            "metadata": {"family_id": "fam:one"},
            "provenance": {"source_id": "source"},
        }
        row_two = {
            "row_id": "two",
            "metadata": {"family_id": "fam:two"},
            "provenance": {"source_id": "source"},
        }
        batch, families = _materialized_candidate_batch(
            selected_keys=["fam:one"],
            chosen_variant_by_family={"fam:one": "best"},
            variant_batches={"best": {"candidate_admitted_batch": {"rows": [row_one, row_two]}}},
            selected_dataset={"families": [{"family_id": "fam:one", "trigger": "one"}]},
            batch_id="batch",
            source_id="source",
            generated_at="2026-04-29T00:00:00Z",
        )

        self.assertEqual(batch["row_count"], 1)
        self.assertEqual(batch["rows"][0]["row_id"], "one")
        self.assertEqual(batch["rows"][0]["metadata"]["source_portfolio_variant_id"], "best")
        self.assertEqual(families[0]["row_count"], 1)

    def test_materialized_selected_payloads_use_chosen_variant_family(self) -> None:
        dataset, queue = _materialized_selected_payloads(
            selected_keys=["fam:rest"],
            chosen_variant_by_family={"fam:rest": "rest_variant"},
            variant_batches={
                "rest_variant": {
                    "dataset_payload": {
                        "families": [
                            {
                                "family_id": "fam:rest",
                                "trigger": "rest",
                                "shadows": [{"sense_id": "rest:descanso:shadow"}],
                            }
                        ]
                    }
                }
            },
            sweep_selected_dataset={
                "dataset_id": "selected",
                "families": [
                    {
                        "family_id": "fam:rest",
                        "trigger": "rest",
                        "shadows": [{"sense_id": "rest:descansar:shadow"}],
                    }
                ],
            },
            sweep_selected_queue={"queue_id": "queue"},
            generated_at="2026-04-29T00:00:00Z",
        )

        self.assertEqual(dataset["families"][0]["shadows"][0]["sense_id"], "rest:descanso:shadow")
        self.assertEqual(dataset["source_sweep_selection_strategy"], "portfolio_materialized")
        self.assertEqual(queue["families"][0]["family_id"], "fam:rest")

    def test_render_materialization_markdown_surfaces_family_table(self) -> None:
        report = _materialization_report(
            generated_at="2026-04-29T00:00:00Z",
            sweep_report={"artifacts": {}},
            selected_keys=["fam:one"],
            chosen_variant_by_family={"fam:one": "best"},
            family_rows=[
                {
                    "family_id": "fam:one",
                    "trigger": "one",
                    "supporting_variant_id": "best",
                    "row_count": 2,
                }
            ],
            portfolio_batch={"row_count": 2},
            cycle_report={
                "status": "ok",
                "summary": {
                    "final_admitted_row_count": 2,
                    "semantic_contract_complete_family_count": 1,
                    "phrase_contract_complete_family_count": 0,
                },
            },
        )

        markdown = render_source_portfolio_materialization_markdown(report)

        self.assertEqual(report["status"], "ok")
        self.assertIn("Decision: `source_portfolio_materialized`", markdown)
        self.assertIn("`fam:one`", markdown)
        self.assertIn("`best`", markdown)


if __name__ == "__main__":
    unittest.main()
