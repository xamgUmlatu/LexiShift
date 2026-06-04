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

from semantic_veto_difficulty_stratification_en_es import (  # noqa: E402
    FrequencyLookup,
    build_difficulty_stratification_report,
    render_difficulty_stratification_markdown,
)


class SemanticVetoDifficultyStratificationTests(unittest.TestCase):
    def test_report_keeps_rank_bins_lanes_and_metadata_gaps_visible(self) -> None:
        report = build_difficulty_stratification_report(
            policy_payload=_policy(),
            llm_scoring_payload=_llm_scoring_payload(),
            llm_plan_payload=_llm_plan_payload(),
            v10_dataset_payload=_v10_dataset_payload(),
            wave7_dataset_payload=_wave7_dataset_payload(),
            source_frequency=FrequencyLookup.from_records(
                language="en",
                rows={
                    "bank": {"rank": 100, "frequency": 1000},
                    "like": {"rank": 700, "frequency": 500},
                },
            ),
            target_frequency=FrequencyLookup.from_records(
                language="es",
                rows={
                    "banco": {"rank": 800, "frequency": 300},
                    "gusto": {"rank": 1200, "frequency": 200},
                },
            ),
            source_zipf_by_trigger={"bank": 5.2, "like": 6.0},
            generated_at="2026-05-05T00:00:00Z",
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(
            report["decision"],
            "difficulty_stratification_baseline_established",
        )
        self.assertEqual(report["e2e_checks"]["policy_case_rows_read"], 2)
        self.assertEqual(report["e2e_checks"]["llm_case_rows_read"], 2)
        self.assertEqual(report["e2e_checks"]["total_case_rows"], 4)

        source_bins = {row["scope_id"]: row for row in report["source_trigger_rank_breakdowns_en"]}
        self.assertEqual(source_bins["1-500"]["case_count"], 2)
        self.assertEqual(source_bins["1-500"]["negative_allow_count"], 1)
        self.assertEqual(source_bins["501-1000"]["case_count"], 2)

        zipf_bins = {row["scope_id"]: row for row in report["source_zipf_breakdowns_en"]}
        self.assertEqual(zipf_bins["zipf_5_plus_very_common"]["case_count"], 4)
        self.assertEqual(zipf_bins["zipf_5_plus_very_common"]["source_zipf_known_rate"], 1.0)

        target_bins = {row["scope_id"]: row for row in report["target_lemma_rank_breakdowns_es"]}
        self.assertEqual(target_bins["501-1000"]["case_count"], 2)
        self.assertEqual(target_bins["1001-2000"]["case_count"], 2)

        case_traces = {row["case_id"]: row for row in report["case_traces"]}
        self.assertEqual(
            case_traces["policy-like-neg"]["target_lemma_frequency_match_kind"],
            "spanish_plural_fallback",
        )
        self.assertEqual(
            case_traces["policy-like-neg"]["source_zipf_band_en"],
            "zipf_5_plus_very_common",
        )
        self.assertEqual(case_traces["llm-bank-neg"]["declared_ambiguity_class"], "high")
        self.assertEqual(case_traces["policy-like-neg"]["wordnet_sense_count"], 11)

        diagnostics = report["summary"]["metadata_diagnostics"]
        self.assertEqual(diagnostics["source_rank_known_rows"], 4)
        self.assertEqual(diagnostics["source_zipf_known_rows"], 4)
        self.assertEqual(diagnostics["target_rank_known_rows"], 4)
        self.assertEqual(diagnostics["missing_source_rank_trigger_count"], 0)

        markdown = render_difficulty_stratification_markdown(report)
        self.assertIn("Semantic Veto Difficulty Stratification", markdown)
        self.assertIn("Source Trigger Rank", markdown)
        self.assertIn("Source Zipf Frequency", markdown)
        self.assertIn("spanish_plural_fallback", markdown)


def _policy() -> dict[str, object]:
    return {
        "schema_version": 1,
        "policy_id": "fixture_policy",
        "pair": "en-es",
        "acceptance": {
            "positive_allow_rate_min": 0.8,
            "negative_abstain_rate_min": 0.5,
        },
        "utility_weights": {
            "positive_allow": 1.0,
            "positive_abstain": -0.4,
            "negative_abstain": 0.8,
            "negative_allow": -0.6,
        },
        "lanes": [
            {
                "lane_id": "stress_fixture",
                "lane_type": "stress",
                "reports": [
                    {
                        "source_id": "inline_stress",
                        "suite_id": "active_shadow",
                        "report": {
                            "schema_version": 1,
                            "status": "ok",
                            "decision": "fixture",
                            "configured_case_results": [
                                _case(
                                    "policy-like-pos",
                                    "en-es:sentence-veto:like:gustos",
                                    "like",
                                    "replace",
                                    "replace",
                                    target="gustos",
                                ),
                                _case(
                                    "policy-like-neg",
                                    "en-es:sentence-veto:like:gustos",
                                    "like",
                                    "abstain",
                                    "abstain",
                                    target="gustos",
                                ),
                            ],
                        },
                    }
                ],
            }
        ],
    }


def _llm_scoring_payload() -> dict[str, object]:
    return {
        "coverage_rows": [
            {
                "family_id": "en-es:sentence-veto:bank:banco",
                "trigger": "bank",
                "active_target": "banco",
                "active_example_count": 2,
                "shadow_example_count": 2,
                "phrase_control_example_count": 1,
                "shadow_targets": ["orilla"],
            }
        ],
        "case_results": [
            _case(
                "llm-bank-pos",
                "en-es:sentence-veto:bank:banco",
                "bank",
                "replace",
                "replace",
                target="banco",
                pilot_family_id="pilot:bank:banco",
            ),
            _case(
                "llm-bank-neg",
                "en-es:sentence-veto:bank:banco",
                "bank",
                "abstain",
                "replace",
                target="banco",
                pilot_family_id="pilot:bank:banco",
            ),
        ],
    }


def _llm_plan_payload() -> dict[str, object]:
    return {
        "pilot_families": [
            {
                "family_id": "pilot:bank:banco",
                "trigger": "bank",
                "candidate_replacement": "banco",
                "frequency_band": "common",
                "ambiguity_class": "high",
            }
        ]
    }


def _v10_dataset_payload() -> dict[str, object]:
    return {
        "families": [
            {
                "family_id": "en-es:sentence-veto:bank:banco",
                "trigger": "bank",
                "active": {
                    "target_lemma": "banco",
                    "evidence_views": {"all_evidence_text": "financial bank"},
                },
                "shadows": [
                    {
                        "target_lemma": "orilla",
                        "evidence_views": {"all_evidence_text": "river bank"},
                    }
                ],
                "cases": [],
            }
        ]
    }


def _wave7_dataset_payload() -> dict[str, object]:
    return {
        "families": [
            {
                "family_id": "en-es:sentence-veto:like:gustos",
                "trigger": "like",
                "active": {
                    "target_lemma": "gustos",
                    "evidence_views": {"all_evidence_text": "things a person likes"},
                    "metadata": {"translation_rank": 18},
                },
                "shadows": [
                    {
                        "target_lemma": "atraer",
                        "evidence_views": {"all_evidence_text": "find attractive"},
                    }
                ],
                "metadata": {
                    "source_candidate": {
                        "sense_count": 11,
                        "pos_counts": {"noun": 2, "verb": 5, "adjective": 4},
                        "complexity_band": "broad",
                    },
                    "translation_candidates": [
                        {"translation": "gustar"},
                        {"translation": "atraer"},
                    ],
                },
                "cases": [
                    {
                        "case_id": "fixture-phrase",
                        "gold_winner": "none",
                        "slice_tags": ["phrase_no_winner"],
                    }
                ],
            }
        ]
    }


def _case(
    case_id: str,
    family_id: str,
    trigger: str,
    gold_decision: str,
    predicted_decision: str,
    *,
    target: str,
    pilot_family_id: str = "",
) -> dict[str, object]:
    return {
        "case_id": case_id,
        "family_id": family_id,
        "pilot_family_id": pilot_family_id,
        "trigger": trigger,
        "candidate_replacement": target,
        "sentence": f"Fixture sentence for {trigger}.",
        "gold_decision": gold_decision,
        "predicted_decision": predicted_decision,
        "active_score": 0.7,
        "strongest_shadow_score": 0.64,
        "phrase_control_score": 0.55,
        "phrase_preemption_hit": False,
    }


if __name__ == "__main__":
    unittest.main()
