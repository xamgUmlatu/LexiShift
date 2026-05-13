from __future__ import annotations

from pathlib import Path
import sys
import unittest


CORE_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = CORE_ROOT.parent
SCRIPTS_ROOT = REPO_ROOT / "scripts" / "testing"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from semantic_veto_denominator_audit_en_es import (  # noqa: E402
    build_denominator_audit_report,
    render_denominator_audit_markdown,
)


class SemanticVetoDenominatorAuditTests(unittest.TestCase):
    def test_explains_denominator_identity_and_exhausted_queue(self) -> None:
        report = build_denominator_audit_report(
            srs_zipf_bridge_payload=_bridge_payload(),
            active_only_plan_payload=_plan_payload(),
            source_target_review_payload=_review_payload(),
            registry_payload=_registry_payload(),
            generated_at="2026-05-14T00:00:00+00:00",
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(
            report["summary"]["accounting_identity"],
            "3 = 1 pre-full-generation covered + 1 reviewed/generated + 1 excluded",
        )
        self.assertEqual(report["summary"]["srs_unique_target_lemmas"], 4)
        self.assertEqual(report["summary"]["semantic_veto_denominator_families"], 3)
        self.assertEqual(report["summary"]["covered_families"], 2)
        self.assertEqual(report["summary"]["uncovered_families"], 1)
        self.assertEqual(report["checks"]["current_generation_queue_exhausted"], True)
        self.assertEqual(report["checks"]["uncovered_rows_are_review_exclusions"], True)

        markdown = render_denominator_audit_markdown(report)
        self.assertIn("SRS learner-target universe", markdown)
        self.assertIn("Semantic-veto replacement denominator", markdown)
        self.assertIn("3 = 1 pre-full-generation covered", markdown)
        self.assertIn("expand_or_replace_spanish_frequency_pack", markdown)

    def test_marks_mismatched_inputs_for_review(self) -> None:
        plan = _plan_payload()
        plan["summary"]["denominator_family_count"] = 4
        report = build_denominator_audit_report(
            srs_zipf_bridge_payload=_bridge_payload(),
            active_only_plan_payload=plan,
            source_target_review_payload=_review_payload(),
            registry_payload=_registry_payload(),
            generated_at="2026-05-14T00:00:00+00:00",
        )

        self.assertEqual(report["status"], "review")
        self.assertIn("bridge_and_plan_denominator_match", report["issues"])


def _bridge_payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "pair": "en-es",
        "decision": "srs_zipf_bridge_established",
        "inputs": {
            "full_srs": {
                "frequency_db": "/tmp/freq-es.sqlite",
                "frequency_db_exists": True,
                "top_n": 50000,
                "seed_row_count": 4,
                "unique_target_count": 4,
            },
            "full_rulegen": {
                "translation_dict_path": "/tmp/freedict.sqlite",
                "translation_dict_exists": True,
                "reverse_translation_dict_path": "/tmp/wiktionary.sqlite",
                "reverse_translation_dict_exists": True,
                "target_count": 4,
                "rule_count": 3,
                "source_target_pair_count": 3,
                "elapsed_seconds": 0.25,
            },
        },
        "summary": {
            "full_srs_admissible_seed_row_count": 4,
            "full_srs_admissible_target_count": 4,
            "full_source_target_pair_count": 3,
        },
        "full_source_target_family_zipf_matrix": [
            {
                "source_zipf_band_en": "zipf_5_plus_very_common",
                "target_zipf_band_es": "zipf_5_plus_very_common",
                "family_count": 3,
                "share": 1.0,
            }
        ],
    }


def _plan_payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "pair": "en-es",
        "decision": "active_only_full_generation_plan_needs_review",
        "summary": {
            "denominator_family_count": 3,
            "denominator_source_trigger_count": 3,
            "denominator_target_count": 3,
            "covered_denominator_family_count": 2,
            "covered_denominator_family_share": 0.6667,
            "uncovered_family_count": 1,
            "generation_queue_family_count": 0,
            "selected_request_count": 0,
            "evidence_outside_denominator_key_count": 0,
        },
        "coverage_by_source_band": [
            {
                "source_band": "zipf_5_plus_very_common",
                "family_count": 3,
                "covered_family_count": 2,
                "covered_share": 0.6667,
                "uncovered_family_count": 1,
            }
        ],
        "coverage_by_target_band": [
            {
                "target_band": "zipf_5_plus_very_common",
                "family_count": 3,
                "covered_family_count": 2,
                "covered_share": 0.6667,
                "uncovered_family_count": 1,
            }
        ],
        "all_uncovered_families": [
            {
                "source": "capital",
                "target": "capital",
                "source_target_review_decision": "exclude_no_visible_replacement",
                "source_zipf_band_en": "zipf_5_plus_very_common",
                "target_zipf_band_es": "zipf_5_plus_very_common",
            }
        ],
    }


def _review_payload() -> dict[str, object]:
    return {
        "decision": "cumulative_reviewed_for_pre_spend_active_only_generation",
        "decisions": [
            {
                "source": "current",
                "target": "corriente",
                "decision": "approve_direct_mapping",
                "approved_for_active_only_generation": True,
            },
            {
                "source": "capital",
                "target": "capital",
                "decision": "exclude_no_visible_replacement",
                "approved_for_active_only_generation": False,
            },
        ],
    }


def _registry_payload() -> dict[str, object]:
    return {
        "current_candidate": {
            "current_result": {
                "families": 1,
            }
        }
    }


if __name__ == "__main__":
    unittest.main()
