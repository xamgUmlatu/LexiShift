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

from semantic_decision_rule_matrix_en_es import (  # noqa: E402
    build_decision_rule_matrix_report,
    render_decision_rule_matrix_markdown,
)


class SemanticDecisionRuleMatrixTests(unittest.TestCase):
    def test_matrix_report_records_frozen_inputs_and_negative_control(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            dataset_path = root / "dataset.json"
            manifest_path = root / "manifest.json"
            dataset_path.write_text(json.dumps(_tiny_dataset()), encoding="utf-8")
            manifest_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "matrix_id": "test_matrix",
                        "dataset_path": str(dataset_path),
                        "defaults": {
                            "split_modulo": 2,
                            "locked_eval_remainders": [0],
                        },
                        "rows": [
                            {
                                "config_id": "control",
                                "is_control": True,
                                "scorer_id": "tfidf_cosine",
                                "context_view": "masked_sentence",
                                "sense_representation": "all_evidence_text",
                                "aggregation_rule": "single_concatenated_text",
                                "decision_rule": "active_minus_strongest_shadow",
                                "phrase_handling": "phrase_override",
                            },
                            {
                                "config_id": "negative_active_only",
                                "expected_failure_mode": "over_replace",
                                "scorer_id": "tfidf_cosine",
                                "context_view": "masked_sentence",
                                "sense_representation": "all_evidence_text",
                                "aggregation_rule": "single_concatenated_text",
                                "decision_rule": "active_minus_strongest_shadow",
                                "phrase_handling": "semantic_only",
                                "evidence_control": "active_only_source",
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )

            report = build_decision_rule_matrix_report(manifest_path=manifest_path)

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["input_fingerprint"]["case_count"], 3)
        self.assertEqual(report["row_count"], 2)
        self.assertEqual(report["case_result_count"], 6)
        self.assertIn("decision_signature_summary", report)
        self.assertIn("incumbent_delta_summary", report)
        self.assertIsNotNone(report["config_rows"][0]["ranking_roc_auc"])
        self.assertEqual(report["negative_control_summary"]["status"], "ok")
        negative = report["negative_control_summary"]["rows"][0]
        self.assertEqual(negative["config_id"], "negative_active_only")
        self.assertGreater(negative["harmful_replace_count"], 0)
        self.assertGreater(
            report["decision_signature_summary"]["unique_replace_signature_count"],
            0,
        )

    def test_separate_row_config_emits_threshold_and_dropout_diagnostics(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            dataset_path = root / "dataset.json"
            manifest_path = root / "manifest.json"
            dataset_path.write_text(json.dumps(_tiny_dataset()), encoding="utf-8")
            manifest_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "matrix_id": "test_matrix",
                        "dataset_path": str(dataset_path),
                        "rows": [
                            {
                                "config_id": "weighted_topk",
                                "is_control": True,
                                "scorer_id": "tfidf_cosine",
                                "context_view": "masked_sentence",
                                "sense_representation": "definition_and_example_rows_separate",
                                "aggregation_rule": "source_weighted_top_k",
                                "decision_rule": "active_minus_strongest_shadow",
                                "phrase_handling": "phrase_override",
                                "threshold_sensitivity": True,
                                "threshold_grid": [
                                    {
                                        "threshold_label": "margin_0",
                                        "min_margin": 0.0,
                                    },
                                    {
                                        "threshold_label": "margin_10",
                                        "min_margin": 0.1,
                                    },
                                ],
                                "source_dropout": True,
                                "source_dropout_families": [
                                    "definition",
                                    "auxiliary",
                                ],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            report = build_decision_rule_matrix_report(manifest_path=manifest_path)
            markdown = render_decision_rule_matrix_markdown(report)

        self.assertEqual(len(report["threshold_sensitivity"]), 2)
        self.assertEqual(len(report["source_dropout"]), 2)
        self.assertIn("Source-Family Dropout", markdown)
        case_trace = report["case_results"][0]
        self.assertIn("active_evidence_trace", case_trace)
        self.assertIn("shadow_evidence_traces", case_trace)

    def test_order_sensitive_context_and_evidence_surfaces_emit_traces(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            dataset_path = root / "dataset.json"
            manifest_path = root / "manifest.json"
            dataset_path.write_text(json.dumps(_tiny_dataset()), encoding="utf-8")
            manifest_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "matrix_id": "test_order_surface",
                        "dataset_path": str(dataset_path),
                        "rows": [
                            {
                                "config_id": "ordered_surface",
                                "is_control": True,
                                "scorer_id": "tfidf_cosine",
                                "context_view": "ordered_ngram_context",
                                "sense_representation": "ordered_evidence_phrase",
                                "aggregation_rule": "single_concatenated_text",
                                "decision_rule": "active_minus_strongest_shadow",
                                "phrase_handling": "phrase_override",
                            },
                            {
                                "config_id": "shuffled_surface",
                                "expected_failure_mode": "lexical_leakage",
                                "scorer_id": "tfidf_cosine",
                                "context_view": "shuffled_context_tokens",
                                "sense_representation": "shuffled_evidence_tokens",
                                "aggregation_rule": "single_concatenated_text",
                                "decision_rule": "active_minus_strongest_shadow",
                                "phrase_handling": "phrase_override",
                            },
                            {
                                "config_id": "dependency_role_surface",
                                "scorer_id": "tfidf_cosine",
                                "context_view": "dependency_role_context",
                                "sense_representation": "canonical_template_evidence",
                                "aggregation_rule": "single_concatenated_text",
                                "decision_rule": "active_minus_strongest_shadow",
                                "phrase_handling": "phrase_override",
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )

            report = build_decision_rule_matrix_report(manifest_path=manifest_path)

        self.assertEqual(report["row_count"], 3)
        ordered_case = next(
            row for row in report["case_results"] if row["config_id"] == "ordered_surface"
        )
        self.assertIn("ng2=", ordered_case["context_text"])
        active_trace = ordered_case["active_evidence_trace"][0]
        self.assertEqual(active_trace["source_family"], "ordered_evidence")
        self.assertIn("part1_order=", active_trace["text"])
        dependency_case = next(
            row for row in report["case_results"] if row["config_id"] == "dependency_role_surface"
        )
        self.assertIn("dep_frame=", dependency_case["context_text"])
        self.assertIn("role=", dependency_case["context_text"])

    def test_context_conditioned_source_rows_use_selector_scores(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            dataset_path = root / "dataset.json"
            evidence_path = root / "evidence.json"
            manifest_path = root / "manifest.json"
            dataset_path.write_text(json.dumps(_tiny_dataset()), encoding="utf-8")
            evidence_path.write_text(json.dumps(_tiny_evidence_batch()), encoding="utf-8")
            manifest_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "matrix_id": "test_context_conditioned",
                        "dataset_path": str(dataset_path),
                        "source_evidence_batch_paths": [str(evidence_path)],
                        "rows": [
                            {
                                "config_id": "context_selected",
                                "is_control": True,
                                "scorer_id": "tfidf_cosine",
                                "context_view": "masked_sentence",
                                "evidence_selector_context_view": "before_after_slot_context",
                                "evidence_selector_source_view": "before_after_slot_context",
                                "sense_representation": "contextualized_source_rows",
                                "aggregation_rule": "context_selected_max_row_score",
                                "selection_top_k": 1,
                                "decision_rule": "active_minus_strongest_shadow",
                                "phrase_handling": "phrase_override",
                            },
                            {
                                "config_id": "additive_source_rows",
                                "scorer_id": "tfidf_cosine",
                                "context_view": "masked_sentence",
                                "sense_representation": "definition_example_plus_source_rows_separate",
                                "aggregation_rule": "max_row_score",
                                "decision_rule": "active_minus_strongest_shadow",
                                "phrase_handling": "phrase_override",
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )

            report = build_decision_rule_matrix_report(manifest_path=manifest_path)

        self.assertEqual(report["status"], "ok")
        self.assertEqual(
            report["input_fingerprint"]["source_evidence_batches"][0]["attached_row_count"],
            2,
        )
        row = next(row for row in report["config_rows"] if row["config_id"] == "context_selected")
        self.assertEqual(row["evidence_selector_context_view"], "before_after_slot_context")
        self.assertEqual(row["selection_top_k"], 1)
        case_trace = next(
            item for item in report["case_results"] if item["config_id"] == "context_selected"
        )
        active_trace = case_trace["active_evidence_trace"][0]
        self.assertEqual(active_trace["source_family"], "wordnet_example_frames")
        self.assertIn("selection_score", active_trace)
        self.assertIn("selector_text", active_trace)
        self.assertIn("left_phrase=", active_trace["selector_text"])
        additive_case = next(
            item for item in report["case_results"] if item["config_id"] == "additive_source_rows"
        )
        additive_families = {row["source_family"] for row in additive_case["active_evidence_trace"]}
        self.assertIn("auxiliary", additive_families)
        self.assertIn("wordnet_example_frames", additive_families)

    def test_row_level_source_evidence_scopes_can_be_compared(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            dataset_path = root / "dataset.json"
            active_evidence_path = root / "active_evidence.json"
            shadow_evidence_path = root / "shadow_evidence.json"
            manifest_path = root / "manifest.json"
            evidence_batch = _tiny_evidence_batch()
            dataset_path.write_text(json.dumps(_tiny_dataset()), encoding="utf-8")
            active_evidence_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "row_count": 1,
                        "rows": [evidence_batch["rows"][0]],
                    }
                ),
                encoding="utf-8",
            )
            shadow_evidence_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "row_count": 1,
                        "rows": [evidence_batch["rows"][1]],
                    }
                ),
                encoding="utf-8",
            )
            manifest_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "matrix_id": "test_source_scope_matrix",
                        "dataset_path": str(dataset_path),
                        "source_evidence_batch_paths": [str(active_evidence_path)],
                        "defaults": {
                            "scorer_id": "tfidf_cosine",
                            "context_view": "masked_sentence",
                            "sense_representation": "source_rows_separate",
                            "aggregation_rule": "max_row_score",
                            "decision_rule": "active_minus_strongest_shadow",
                            "phrase_handling": "phrase_override",
                            "min_active_score": 0.01,
                        },
                        "rows": [
                            {
                                "config_id": "manifest_scope",
                                "is_control": True,
                            },
                            {
                                "config_id": "row_shadow_scope",
                                "source_evidence_scope_id": "shadow_only_scope",
                                "source_evidence_batch_paths": [str(shadow_evidence_path)],
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )

            report = build_decision_rule_matrix_report(manifest_path=manifest_path)
            markdown = render_decision_rule_matrix_markdown(report)

        rows_by_id = {row["config_id"]: row for row in report["config_rows"]}
        self.assertEqual(
            rows_by_id["manifest_scope"]["source_evidence_scope_id"], "manifest_default"
        )
        self.assertEqual(
            rows_by_id["row_shadow_scope"]["source_evidence_scope_id"],
            "shadow_only_scope",
        )
        self.assertEqual(rows_by_id["manifest_scope"]["source_evidence_attached_row_count"], 1)
        self.assertEqual(rows_by_id["row_shadow_scope"]["source_evidence_attached_row_count"], 1)
        self.assertEqual(len(report["source_evidence_scopes"]), 2)
        self.assertNotEqual(
            rows_by_id["manifest_scope"]["replace_case_signature"],
            rows_by_id["row_shadow_scope"]["replace_case_signature"],
        )
        self.assertIn("Source Evidence Scopes", markdown)

    def test_parameter_grid_expands_family_bakeoff_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            dataset_path = root / "dataset.json"
            manifest_path = root / "manifest.json"
            dataset_path.write_text(json.dumps(_tiny_dataset()), encoding="utf-8")
            manifest_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "matrix_id": "test_family_bakeoff",
                        "dataset_path": str(dataset_path),
                        "defaults": {
                            "scorer_id": "tfidf_cosine",
                            "context_view": "masked_sentence",
                            "sense_representation": "all_evidence_text",
                            "aggregation_rule": "single_concatenated_text",
                            "phrase_handling": "phrase_override",
                        },
                        "rows": [
                            {
                                "config_id": "margin_control",
                                "is_control": True,
                                "algorithm_family": "control_margin",
                                "decision_rule": "active_minus_strongest_shadow",
                                "min_active_score": 0.05,
                                "min_margin": 0.0,
                            },
                            {
                                "config_id": "family_margin",
                                "algorithm_family": "margin",
                                "decision_rule": "active_minus_strongest_shadow",
                                "parameter_grid": {
                                    "min_active_score": [0.0, 0.05],
                                    "min_margin": [0.0, 0.1],
                                },
                            },
                            {
                                "config_id": "family_ratio",
                                "algorithm_family": "ratio",
                                "decision_rule": "active_ratio_strongest_shadow",
                                "parameter_grid": {
                                    "min_active_score": [0.0],
                                    "ratio_threshold": [1.0, 1.1],
                                },
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )

            report = build_decision_rule_matrix_report(manifest_path=manifest_path)
            markdown = render_decision_rule_matrix_markdown(report)

        self.assertEqual(report["row_count"], 7)
        config_ids = {row["config_id"] for row in report["config_rows"]}
        self.assertIn("family_margin:a0__m0", config_ids)
        self.assertIn("family_margin:a0_05__m0_1", config_ids)
        families = {row["algorithm_family"]: row for row in report["family_bakeoff_summary"]}
        self.assertEqual(families["margin"]["config_count"], 4)
        self.assertEqual(families["ratio"]["config_count"], 2)
        self.assertIn("replace_case_signature", families["margin"]["best_row"])
        self.assertIn("ranking_average_precision", families["margin"]["best_row"])
        selection = {
            row["algorithm_family"]: row for row in report["selection_validation_summary"]["rows"]
        }
        self.assertIn("margin", selection)
        self.assertIn("locked_eval", selection["margin"]["selected_on_discovery"])
        self.assertIn("tied_group_count", report["metric_tie_summary"])
        self.assertIn("Algorithm Family Winners", markdown)
        self.assertIn("Decision Signature Clusters", markdown)
        self.assertIn("Headline Metric Ties", markdown)
        self.assertIn("Discovery Selection vs Locked Eval", markdown)

    def test_evaluation_suites_can_combine_full_and_case_only_payloads(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            dataset_path = root / "dataset.json"
            heldout_path = root / "heldout.json"
            manifest_path = root / "manifest.json"
            dataset = _tiny_dataset()
            dataset_path.write_text(json.dumps(dataset), encoding="utf-8")
            heldout_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "pair": "en-es",
                        "dataset_id": "tiny_heldout",
                        "families": [
                            {
                                "family_id": "family:bank",
                                "cases": dataset["families"][0]["cases"][:2],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            manifest_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "matrix_id": "test_suite_matrix",
                        "dataset_path": str(dataset_path),
                        "evaluation_suites": [
                            {
                                "suite_id": "frozen_v10",
                                "suite_role": "frozen_current",
                                "dataset_path": str(dataset_path),
                            },
                            {
                                "suite_id": "heldout_v1",
                                "suite_role": "locked_heldout",
                                "base_dataset_path": str(dataset_path),
                                "case_dataset_path": str(heldout_path),
                            },
                        ],
                        "rows": [
                            {
                                "config_id": "control",
                                "is_control": True,
                                "scorer_id": "tfidf_cosine",
                                "context_view": "masked_sentence",
                                "sense_representation": "all_evidence_text",
                                "aggregation_rule": "single_concatenated_text",
                                "decision_rule": "active_minus_strongest_shadow",
                                "phrase_handling": "phrase_override",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            report = build_decision_rule_matrix_report(manifest_path=manifest_path)
            markdown = render_decision_rule_matrix_markdown(report)

        self.assertEqual(report["input_fingerprint"]["case_count"], 5)
        self.assertEqual(report["input_fingerprint"]["evaluation_suite_count"], 2)
        self.assertEqual(len(report["evaluation_suites"]), 2)
        case_ids = {row["case_id"] for row in report["case_results"]}
        self.assertIn("frozen_v10::case:bank:finance", case_ids)
        self.assertIn("heldout_v1::case:bank:finance", case_ids)
        suite_ids = {row["suite_id"] for row in report["config_rows"][0]["suite_breakdown"]}
        self.assertEqual(suite_ids, {"frozen_v10", "heldout_v1"})
        self.assertIn("Evaluation Suite Breakdown", markdown)


def _tiny_dataset() -> dict[str, object]:
    return {
        "schema_version": 1,
        "pair": "en-es",
        "dataset_id": "tiny_semantic_decision_matrix",
        "families": [
            {
                "family_id": "family:bank",
                "trigger": "bank",
                "active": {
                    "sense_id": "sense:bank:financial",
                    "target_lemma": "banco",
                    "canonical_pos": "noun",
                    "evidence_views": {
                        "sense_label": "financial bank",
                        "gloss_text": "financial institution for cash money deposits accounts",
                        "all_evidence_text": (
                            "financial bank | financial institution for cash money "
                            "deposits accounts | loan account deposit"
                        ),
                    },
                },
                "shadows": [
                    {
                        "sense_id": "sense:bank:river",
                        "target_lemma": "orilla",
                        "canonical_pos": "noun",
                        "evidence_views": {
                            "sense_label": "river bank",
                            "gloss_text": "edge of river water shore",
                            "all_evidence_text": "river bank | edge of river water shore | grassy shore",
                        },
                    }
                ],
                "cases": [
                    {
                        "case_id": "case:bank:finance",
                        "sentence": "She deposited cash at the bank.",
                        "source_phrase": "bank",
                        "gold_winner": "sense:bank:financial",
                        "gold_decision": "replace",
                        "slice_tags": ["clear_active"],
                        "slice_dimensions": {"winner_type": ["active"]},
                    },
                    {
                        "case_id": "case:bank:river",
                        "sentence": "They rested on the grassy bank of the river.",
                        "source_phrase": "bank",
                        "gold_winner": "sense:bank:river",
                        "gold_decision": "abstain",
                        "slice_tags": ["clear_shadow"],
                        "slice_dimensions": {"winner_type": ["shadow"]},
                    },
                    {
                        "case_id": "case:bank:phrase",
                        "sentence": "You can bank on her support.",
                        "source_phrase": "bank",
                        "gold_winner": "none",
                        "gold_decision": "abstain",
                        "slice_tags": ["phrase_control"],
                        "slice_dimensions": {"winner_type": ["none"]},
                    },
                ],
            }
        ],
    }


def _tiny_evidence_batch() -> dict[str, object]:
    return {
        "schema_version": 1,
        "row_count": 2,
        "rows": [
            {
                "row_id": "active-bank-example",
                "evidence_id": "evidence:active-bank-example",
                "source_family": "wordnet_example_frames",
                "source_id": "wordnet_example_frames",
                "relation_type": "anchor_cue",
                "trigger": "bank",
                "normalized_trigger": "bank",
                "evidence_text": "The customer deposited cash at the bank before noon.",
                "metadata": {
                    "candidate_sense_id": "sense:bank:financial",
                },
            },
            {
                "row_id": "shadow-bank-example",
                "evidence_id": "evidence:shadow-bank-example",
                "source_family": "wordnet_example_frames",
                "source_id": "wordnet_example_frames",
                "relation_type": "shadow_candidate",
                "trigger": "bank",
                "normalized_trigger": "bank",
                "evidence_text": "The canoe drifted toward the muddy bank of the river.",
                "metadata": {
                    "candidate_sense_id": "sense:bank:river",
                },
            },
        ],
    }


if __name__ == "__main__":
    unittest.main()
