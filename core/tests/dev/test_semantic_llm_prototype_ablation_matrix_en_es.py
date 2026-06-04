from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

CORE_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = CORE_ROOT.parent
SCRIPTS_ROOT = REPO_ROOT / "scripts" / "testing"
for candidate in (str(CORE_ROOT), str(SCRIPTS_ROOT)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from semantic_llm_prototype_ablation_matrix_en_es import (  # noqa: E402
    build_prototype_ablation_matrix_report,
    render_prototype_ablation_matrix_markdown,
)


class SemanticLlmPrototypeAblationMatrixTests(unittest.TestCase):
    def test_matrix_crosses_sources_scopes_contexts_and_guard_shapes(self) -> None:
        queue_payload, dataset_payload = _sample_inputs()
        report = build_prototype_ablation_matrix_report(
            queue_payload=queue_payload,
            dataset_payload=dataset_payload,
            source_modes=("reviewed_dataset", "empty_batch", "custom_source"),
            source_payload_overrides={"custom_source": _normalized_evidence_batch()},
            scopes=("prompt_queue", "all_dataset_families"),
            scorers=("token_jaccard",),
            context_views=("masked_sentence", "raw_sentence"),
            min_active_scores=(0.0,),
            min_margins=(0.0,),
            generated_at="2026-04-25T12:00:00Z",
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["decision_contract"], "binary_replace_or_abstain")
        self.assertEqual(report["row_count"], 72)
        self.assertEqual(report["run_report_count"], 12)
        self.assertEqual(
            set(report["best_by_context_view"]),
            {"masked_sentence", "raw_sentence"},
        )
        self.assertIn("active_shadow_phrase_containment", report["best_by_decision_shape"])
        self.assertIn(
            "active_shadow_phrase_semantic_surface_pos",
            report["best_by_decision_shape"],
        )
        self.assertIn("reviewed_dataset", report["best_by_source_mode"])
        self.assertIn("empty_batch", report["best_by_source_mode"])
        self.assertIn("custom_source", report["best_by_source_mode"])
        self.assertEqual(report["assumption_audit"]["best_oracle_row"]["source_class"], "oracle")
        self.assertEqual(
            report["assumption_audit"]["best_candidate_source_row"]["source_class"],
            "candidate_source",
        )
        self.assertIn(
            "false_abstain_case_ids",
            report["assumption_audit"]["best_candidate_source_row"],
        )

        custom_all_rows = [
            row
            for row in report["rows"]
            if row["source_mode"] == "custom_source"
            and row["scope"] == "all_dataset_families"
            and row["context_view"] == "masked_sentence"
        ]
        self.assertTrue(custom_all_rows)
        self.assertEqual(custom_all_rows[0]["source_coverage"]["families_total"], 2)
        self.assertEqual(custom_all_rows[0]["source_coverage"]["active_covered_families"], 1)

        markdown = render_prototype_ablation_matrix_markdown(report)
        self.assertIn("Semantic LLM Prototype Ablation Matrix", markdown)
        self.assertIn("Best by Source Mode", markdown)
        self.assertIn("Assumption Audit", markdown)

    def test_generated_source_variants_filter_data_nodes(self) -> None:
        queue_payload, dataset_payload = _sample_inputs()
        with tempfile.TemporaryDirectory() as tmp_dir:
            generated_path = Path(tmp_dir) / "generated.json"
            generated_path.write_text(
                json.dumps(_normalized_evidence_batch(), ensure_ascii=False),
                encoding="utf-8",
            )

            report = build_prototype_ablation_matrix_report(
                queue_payload=queue_payload,
                dataset_payload=dataset_payload,
                source_modes=(
                    "generated_composite",
                    "generated_active_only",
                    "generated_no_phrase",
                    "generated_no_shadow",
                ),
                scopes=("prompt_queue",),
                scorers=("token_jaccard",),
                context_views=("masked_sentence",),
                min_active_scores=(0.0,),
                min_margins=(0.0,),
                generated_composite_path=generated_path,
                generated_at="2026-04-25T12:00:00Z",
            )

        self.assertEqual(report["row_count"], 24)
        by_source = {
            row["source_mode"]: row["source_coverage"]
            for row in report["rows"]
            if row["decision_shape"] == "active_shadow_family_pos_guard"
        }
        self.assertEqual(by_source["generated_composite"]["any_shadow_covered_families"], 1)
        self.assertEqual(by_source["generated_composite"]["phrase_covered_families"], 1)
        self.assertEqual(by_source["generated_active_only"]["any_shadow_covered_families"], 0)
        self.assertEqual(by_source["generated_active_only"]["phrase_covered_families"], 0)
        self.assertEqual(by_source["generated_no_phrase"]["phrase_covered_families"], 0)
        self.assertEqual(by_source["generated_no_shadow"]["any_shadow_covered_families"], 0)

    def test_matrix_sweeps_phrase_prototype_margin_independently(self) -> None:
        queue_payload, dataset_payload = _sample_inputs()
        report = build_prototype_ablation_matrix_report(
            queue_payload=queue_payload,
            dataset_payload=dataset_payload,
            source_modes=("custom_source",),
            source_payload_overrides={"custom_source": _normalized_evidence_batch()},
            scopes=("prompt_queue",),
            scorers=("token_jaccard",),
            context_views=("masked_sentence",),
            min_active_scores=(0.0,),
            min_margins=(0.0,),
            phrase_prototype_margins=(0.0, 0.1),
            generated_at="2026-04-25T12:00:00Z",
        )

        self.assertEqual(report["grid"]["phrase_prototype_margins"], [0.0, 0.1])
        self.assertEqual(report["row_count"], 12)
        phrase_rows = [
            row
            for row in report["rows"]
            if row["decision_shape"] == "active_shadow_phrase_semantic_prototypes"
        ]
        self.assertEqual(
            {row["phrase_prototype_margin"] for row in phrase_rows},
            {0.0, 0.1},
        )
        self.assertTrue(all(":p=" in row["matrix_id"] for row in phrase_rows))

    def test_zero_quality_case_rows_are_not_selected_as_best(self) -> None:
        queue_payload, dataset_payload = _sample_inputs()
        for family in dataset_payload["families"]:
            for case in family["cases"]:
                case["slice_tags"] = ["loader_only", "not_quality_evaluation"]

        report = build_prototype_ablation_matrix_report(
            queue_payload=queue_payload,
            dataset_payload=dataset_payload,
            source_modes=("custom_source",),
            source_payload_overrides={"custom_source": _normalized_evidence_batch()},
            scopes=("prompt_queue",),
            scorers=("token_jaccard",),
            context_views=("masked_sentence",),
            min_active_scores=(0.0,),
            min_margins=(0.0,),
            generated_at="2026-04-25T12:00:00Z",
        )

        self.assertTrue(report["rows"])
        self.assertTrue(all(row["cases_total"] == 0 for row in report["rows"]))
        self.assertIsNone(report["best_row"])
        self.assertIsNone(report["best_candidate_source_row"])
        self.assertIsNone(report["assumption_audit"]["best_candidate_source_row"])


def _sample_inputs() -> tuple[dict[str, object], dict[str, object]]:
    queue_payload = {
        "queue_id": "semantic_prompt_bakeoff_test",
        "families": [
            {
                "family_id": "fam:check",
                "trigger": "check",
                "role": "target",
                "likely_bucket": "needs_cue_data",
            }
        ],
    }
    dataset_payload = {
        "schema_version": 1,
        "pair": "en-es",
        "dataset_id": "en_es_sentence_veto_test",
        "families": [
            _family(
                family_id="fam:check",
                trigger="check",
                active_target="cheque",
                shadow_target="revisar",
                active_case_id="check:001",
                active_sentence="The check was signed and deposited yesterday.",
                shadow_case_id="check:002",
                shadow_sentence="They will check the records carefully tonight.",
            ),
            _family(
                family_id="fam:order",
                trigger="order",
                active_target="pedido",
                shadow_target="ordenar",
                active_case_id="order:001",
                active_sentence="The order arrived in a sealed box.",
                shadow_case_id="order:002",
                shadow_sentence="Please order the reports by date.",
            ),
        ],
    }
    return queue_payload, dataset_payload


def _normalized_evidence_batch() -> dict[str, object]:
    return {
        "schema_version": 1,
        "source_id": "test_evidence",
        "batch_id": "test",
        "rows": [
            {
                "relation_type": "anchor_cue",
                "trigger": "check",
                "evidence_text": "cleared deposit payment rent",
                "metadata": {
                    "family_id": "fam:check",
                    "active_sense_id": "fam:check:active",
                },
            },
            {
                "relation_type": "shadow_candidate",
                "trigger": "check",
                "evidence_text": "inspect records figures",
                "metadata": {
                    "family_id": "fam:check",
                    "candidate_sense_id": "fam:check:shadow",
                },
            },
            {
                "relation_type": "phrase_control_example",
                "trigger": "check",
                "evidence_text": "The rain check is valid next week.",
                "metadata": {"family_id": "fam:check"},
            },
        ],
    }


def _family(
    *,
    family_id: str,
    trigger: str,
    active_target: str,
    shadow_target: str,
    active_case_id: str,
    active_sentence: str,
    shadow_case_id: str,
    shadow_sentence: str,
) -> dict[str, object]:
    active_id = f"{family_id}:active"
    shadow_id = f"{family_id}:shadow"
    return {
        "family_id": family_id,
        "trigger": trigger,
        "active": {
            "sense_id": active_id,
            "target_lemma": active_target,
            "canonical_pos": "noun",
            "evidence_views": {
                "sense_label": f"{trigger} noun",
                "all_evidence_text": f"{trigger} noun",
            },
        },
        "shadows": [
            {
                "sense_id": shadow_id,
                "target_lemma": shadow_target,
                "canonical_pos": "verb",
                "evidence_views": {
                    "sense_label": f"{trigger} verb",
                    "all_evidence_text": f"{trigger} verb",
                },
            }
        ],
        "cases": [
            {
                "case_id": active_case_id,
                "sentence": active_sentence,
                "source_phrase": trigger,
                "gold_winner": active_id,
                "gold_decision": "replace",
                "slice_tags": ["clear_active", "cross_pos"],
            },
            {
                "case_id": shadow_case_id,
                "sentence": shadow_sentence,
                "source_phrase": trigger,
                "gold_winner": shadow_id,
                "gold_decision": "abstain",
                "slice_tags": ["clear_shadow", "cross_pos"],
            },
        ],
    }


if __name__ == "__main__":
    unittest.main()
