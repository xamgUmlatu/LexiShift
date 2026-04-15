from __future__ import annotations

from pathlib import Path
import sys
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from rulegen_profile_bank_analysis import (  # noqa: E402
    LoadedProfile,
    build_profile_bank_analysis,
    render_markdown_report,
)


def _case_payload(
    *,
    case_id: str,
    top1_source: str,
    top3_contains_expected: bool,
    rule_count: int,
    candidate_row_count: int,
    candidate_family_names: tuple[str, ...] = (),
) -> dict[str, object]:
    return {
        "case_id": case_id,
        "top1_source": top1_source,
        "top1_correct": top1_source == "battery",
        "top3_contains_expected": top3_contains_expected,
        "top1_forbidden": False,
        "forbidden_any_present": False,
        "rule_count": rule_count,
        "top1_is_variant": False,
        "trait_summary": {
            "router_input": {
                "target_length": 7,
                "target_token_count": 1,
                "candidate_row_count": candidate_row_count,
                "candidate_definition_bucket_count": 2,
                "candidate_phrase_count": 1,
                "candidate_variant_count": 0,
                "candidate_reverse_supported_count": 2,
                "candidate_reverse_hit_count": 1,
                "candidate_interjection_shadow_count": 0,
                "candidate_late_sense_count": 1,
                "candidate_target_pos_canonicals": ["noun"],
                "candidate_family_names": list(candidate_family_names),
            },
            "result_shape": {
                "selected_source_count": rule_count,
                "selected_multiword_count": 0,
                "top1_source_token_count": 1,
                "top1_multiword": False,
                "variant_rule_count": 0,
                "top1_is_variant": False,
            },
            "benchmark_only": {
                "expected_any_count": 1,
                "expected_top1_count": 1,
                "forbidden_top1_count": 0,
                "forbidden_any_count": 0,
                "expected_match_count": 1 if top3_contains_expected else 0,
                "forbidden_match_count": 0,
            },
        },
    }


class RulegenProfileBankAnalysisTest(unittest.TestCase):
    def test_build_profile_bank_analysis_tracks_differences_and_regions(self) -> None:
        canonical = LoadedProfile(
            label="canonical",
            benchmark_path=Path("canonical.json"),
            triage_path=Path("canonical_triage.json"),
            pair="en-es",
            best_run={
                "config_label": "canonical-config",
                "summary": {
                    "objective_score": 100.0,
                    "top1_accuracy": 1.0,
                    "top3_recall": 1.0,
                    "forbidden_any_rate": 0.0,
                    "avg_rules_per_target": 2.0,
                },
                "case_results": [
                    _case_payload(
                        case_id="en-es:bateria",
                        top1_source="battery",
                        top3_contains_expected=True,
                        rule_count=3,
                        candidate_row_count=10,
                        candidate_family_names=("music",),
                    ),
                    _case_payload(
                        case_id="en-es:red",
                        top1_source="web",
                        top3_contains_expected=True,
                        rule_count=4,
                        candidate_row_count=12,
                        candidate_family_names=("communication_network",),
                    ),
                ],
            },
            triage_items=({"case_id": "en-es:red"},),
        )
        admission = LoadedProfile(
            label="admission-tight",
            benchmark_path=Path("admission.json"),
            triage_path=Path("admission_triage.json"),
            pair="en-es",
            best_run={
                "config_label": "admission-config",
                "summary": {
                    "objective_score": 105.0,
                    "top1_accuracy": 1.0,
                    "top3_recall": 0.5,
                    "forbidden_any_rate": 0.0,
                    "avg_rules_per_target": 1.0,
                },
                "case_results": [
                    _case_payload(
                        case_id="en-es:bateria",
                        top1_source="battery",
                        top3_contains_expected=True,
                        rule_count=1,
                        candidate_row_count=10,
                        candidate_family_names=("music",),
                    ),
                    _case_payload(
                        case_id="en-es:red",
                        top1_source="web",
                        top3_contains_expected=False,
                        rule_count=2,
                        candidate_row_count=12,
                        candidate_family_names=("communication_network",),
                    ),
                ],
            },
            triage_items=({"case_id": "en-es:red"},),
        )

        analysis = build_profile_bank_analysis(
            profiles=(canonical, admission),
        )

        self.assertEqual(analysis["pair"], "en-es")
        self.assertEqual(analysis["comparison"]["top1_diff_case_ids"], [])
        self.assertEqual(analysis["comparison"]["top3_diff_case_ids"], ["en-es:red"])
        self.assertEqual(
            sorted(analysis["comparison"]["rule_count_diff_case_ids"]),
            ["en-es:bateria", "en-es:red"],
        )
        trait_regions = analysis["trait_regions"]
        self.assertTrue(
            any(
                region["trait"] == "candidate_family"
                and region["value"] == "communication_network"
                and region["best_profiles"] == ["canonical"]
                for region in trait_regions
            )
        )

    def test_render_markdown_report_includes_trait_region_section(self) -> None:
        analysis = {
            "generated_at": "2026-03-29T00:00:00+00:00",
            "pair": "en-es",
            "profile_labels": ["canonical"],
            "profiles": {
                "canonical": {
                    "config_label": "cfg",
                    "summary": {
                        "objective_score": 100.0,
                        "top1_accuracy": 1.0,
                        "top3_recall": 1.0,
                        "forbidden_any_rate": 0.0,
                        "avg_rules_per_target": 2.0,
                    },
                    "triage_case_ids": [],
                }
            },
            "comparison": {
                "top1_diff_case_ids": [],
                "top3_diff_case_ids": [],
                "rule_count_diff_case_ids": [],
            },
            "trait_regions": [
                {
                    "trait": "candidate_family",
                    "value": "communication_network",
                    "case_count": 2,
                    "case_ids": ["en-es:red", "en-es:cadena"],
                    "avg_case_objective_by_profile": {"canonical": 77.0},
                    "best_profiles": ["canonical"],
                }
            ],
        }

        markdown = render_markdown_report(analysis)

        self.assertIn("## Trait Regions", markdown)
        self.assertIn("communication_network", markdown)
        self.assertIn("`canonical`=77.00", markdown)


if __name__ == "__main__":
    unittest.main()
