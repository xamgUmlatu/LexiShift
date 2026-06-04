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

from semantic_source_reference_lane_en_es import (  # noqa: E402
    build_source_reference_lane_report,
    render_source_reference_lane_markdown,
)


class SemanticSourceReferenceLaneTests(unittest.TestCase):
    def test_reference_lane_report_passes_when_artifacts_match_manifest(self) -> None:
        report = build_source_reference_lane_report(
            manifest_payload=_manifest(),
            source_cycle_payload=_source_cycle(),
            heldout_payload=_heldout(),
            evidence_batch_payload=_evidence_batch(),
            generated_at="2026-04-25T12:00:00Z",
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["decision"], "reference_lane_frozen")
        self.assertEqual(report["summary"]["failed_check_count"], 0)
        self.assertGreater(report["summary"]["check_count"], 20)

        markdown = render_source_reference_lane_markdown(report)
        self.assertIn("Semantic Source Reference Lane", markdown)
        self.assertIn("reference_lane_frozen", markdown)
        self.assertIn("runtime_phrase_source_policy", markdown)

    def test_reference_lane_report_flags_metric_drift(self) -> None:
        source_cycle = _source_cycle()
        source_cycle["summary"]["best_ablation_row"]["false_abstain_count"] = 1

        report = build_source_reference_lane_report(
            manifest_payload=_manifest(),
            source_cycle_payload=source_cycle,
            heldout_payload=_heldout(),
            evidence_batch_payload=_evidence_batch(),
            generated_at="2026-04-25T12:00:00Z",
        )

        self.assertEqual(report["status"], "review")
        self.assertEqual(report["decision"], "reference_lane_review")
        failed_ids = {check["check_id"] for check in report["failed_checks"]}
        self.assertIn("source_cycle.best_ablation_false_abstain_count", failed_ids)

    def test_reference_lane_can_freeze_cell_depth_evidence(self) -> None:
        manifest = _manifest()
        manifest["expected"]["evidence_batch"].update(
            {
                "row_count": 3,
                "relation_type_counts": {
                    "anchor_cue": 2,
                    "shadow_candidate": 1,
                },
                "cell_active_related_wordnet_depth2_plus_min_count": 1,
            }
        )
        evidence = _evidence_batch()
        evidence["row_count"] = 3
        evidence["rows"].append(
            {
                "relation_type": "anchor_cue",
                "metadata": {
                    "family_id": "en-es:sentence-veto:cell:celula",
                    "wordnet_relation_path": ["cell-n", "blood-cell-n", "red-blood-cell-n"],
                },
            }
        )

        report = build_source_reference_lane_report(
            manifest_payload=manifest,
            source_cycle_payload=_source_cycle(),
            heldout_payload=_heldout(),
            evidence_batch_payload=evidence,
            generated_at="2026-04-25T12:00:00Z",
        )

        self.assertEqual(report["status"], "ok")
        check_ids = {check["check_id"] for check in report["checks"]}
        self.assertIn("evidence.cell_active_related_wordnet_depth2_plus_min_count", check_ids)

    def test_reference_lane_can_track_phrase_policy_candidate_separately(self) -> None:
        manifest = _manifest()
        manifest["phrase_policy_candidate_lane"] = {
            "source_mode": "promotion_candidate_composite",
            "scorer_id": "sentence_transformer_cosine",
            "context_view": "masked_sentence",
            "min_active_score": 0.0,
            "min_margin": 0.005,
            "decision_shape": "active_shadow_containment_surface_pos",
        }
        manifest["expected"]["phrase_heldout_validation"] = {
            "status": "ok",
            "decision": "heldout_pass",
            "family_count": 1,
            "case_count": 2,
            "harmful_replace_count": 0,
            "false_abstain_count": 0,
            "replace_recall": 0.0,
            "decision_accuracy": 1.0,
        }

        report = build_source_reference_lane_report(
            manifest_payload=manifest,
            source_cycle_payload=_source_cycle(),
            heldout_payload=_heldout(),
            phrase_heldout_payload=_phrase_heldout(),
            evidence_batch_payload=_evidence_batch(),
            generated_at="2026-04-25T12:00:00Z",
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["summary"]["phrase_heldout_status"], "ok")
        check_ids = {check["check_id"] for check in report["checks"]}
        self.assertIn("phrase_heldout.configured_lane.min_margin", check_ids)


def _manifest() -> dict[str, object]:
    return {
        "schema_version": 1,
        "pair": "en-es",
        "lane_id": "test_lane",
        "configured_lane": {
            "source_mode": "cycle_merged",
            "scorer_id": "sentence_transformer_cosine",
            "context_view": "masked_sentence",
            "min_active_score": 0.0,
            "min_margin": 0.0,
            "decision_shape": "active_shadow_containment_surface_pos",
        },
        "artifacts": {
            "source_cycle_json": "cycle.json",
            "heldout_validation_json": "heldout.json",
            "admitted_evidence_batch_json": "evidence.json",
        },
        "known_non_runtime_blockers": ["runtime_phrase_source_policy"],
        "expected": {
            "source_cycle": {
                "status": "ok",
                "decision": "promotion_candidate",
                "offline_promotion_lane": "semantic_active_shadow",
                "offline_semantic_lane_status": "promotion_candidate",
                "runtime_publication_status": "blocked",
                "runtime_publication_blockers": [
                    "runtime_phrase_source_policy",
                    "broader_heldout_breadth",
                    "runtime_packaging_feasibility",
                ],
                "heldout_validation_status": "ok",
                "heldout_validation_decision": "heldout_pass",
                "heldout_validation_passed": True,
                "leakage_rejected_row_count": 0,
                "sense_rejected_row_count": 0,
                "final_admitted_row_count": 2,
                "families_total": 1,
                "semantic_contract_complete_family_count": 1,
                "phrase_contract_complete_family_count": 0,
                "best_ablation_cases_total": 2,
                "best_ablation_harmful_replace_count": 0,
                "best_ablation_false_abstain_count": 0,
                "best_ablation_replace_recall": 1.0,
                "best_ablation_decision_accuracy": 1.0,
            },
            "heldout_validation": {
                "status": "ok",
                "decision": "heldout_pass",
                "family_count": 1,
                "case_count": 2,
                "harmful_replace_count": 0,
                "false_abstain_count": 0,
                "replace_recall": 1.0,
                "decision_accuracy": 1.0,
            },
            "evidence_batch": {
                "source_id": "test_source",
                "batch_id": "test_batch",
                "row_count": 2,
                "relation_type_counts": {
                    "anchor_cue": 1,
                    "shadow_candidate": 1,
                },
                "plant_active_related_wordnet_min_count": 1,
            },
        },
    }


def _source_cycle() -> dict[str, object]:
    return {
        "status": "ok",
        "decision": "promotion_candidate",
        "summary": {
            "leakage_rejected_row_count": 0,
            "sense_rejected_row_count": 0,
            "final_admitted_row_count": 2,
            "families_total": 1,
            "semantic_contract_complete_family_count": 1,
            "phrase_contract_complete_family_count": 0,
            "heldout_validation": {
                "status": "ok",
                "decision": "heldout_pass",
                "passed": True,
            },
            "best_ablation_row": {
                "source_mode": "cycle_merged",
                "scorer_id": "sentence_transformer_cosine",
                "context_view": "masked_sentence",
                "min_active_score": 0.0,
                "min_margin": 0.0,
                "decision_shape": "active_shadow_containment_surface_pos",
                "cases_total": 2,
                "harmful_replace_count": 0,
                "false_abstain_count": 0,
                "replace_recall": 1.0,
                "decision_accuracy": 1.0,
            },
        },
        "policy": {
            "offline_promotion_lane": "semantic_active_shadow",
            "offline_semantic_lane_status": "promotion_candidate",
            "runtime_publication_status": "blocked",
            "runtime_publication_blockers": [
                "runtime_phrase_source_policy",
                "broader_heldout_breadth",
                "runtime_packaging_feasibility",
            ],
        },
    }


def _heldout() -> dict[str, object]:
    return {
        "status": "ok",
        "decision": "heldout_pass",
        "summary": {
            "family_count": 1,
            "case_count": 2,
            "harmful_replace_count": 0,
            "false_abstain_count": 0,
            "replace_recall": 1.0,
            "decision_accuracy": 1.0,
        },
        "configured_lane": {
            "scorer_id": "sentence_transformer_cosine",
            "context_view": "masked_sentence",
            "min_active_score": 0.0,
            "min_margin": 0.0,
            "decision_shape": "active_shadow_containment_surface_pos",
        },
    }


def _phrase_heldout() -> dict[str, object]:
    payload = _heldout()
    payload["summary"].update(
        {
            "gold_replace_cases": 0,
            "gold_abstain_cases": 2,
            "replace_recall": 0.0,
            "decision_accuracy": 1.0,
        }
    )
    payload["configured_lane"].update(
        {
            "source_mode": "promotion_candidate_composite",
            "min_margin": 0.005,
        }
    )
    return payload


def _evidence_batch() -> dict[str, object]:
    return {
        "source_id": "test_source",
        "batch_id": "test_batch",
        "row_count": 2,
        "rows": [
            {
                "relation_type": "anchor_cue",
                "metadata": {
                    "family_id": "en-es:sentence-veto:plant:planta",
                    "wordnet_source_relation": "direct_hyponym",
                },
            },
            {"relation_type": "shadow_candidate", "metadata": {"family_id": "fam"}},
        ],
    }


if __name__ == "__main__":
    unittest.main()
