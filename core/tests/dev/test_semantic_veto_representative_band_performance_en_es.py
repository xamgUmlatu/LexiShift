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

from semantic_veto_representative_band_performance_en_es import (  # noqa: E402
    build_representative_band_performance_report,
    render_representative_band_performance_markdown,
)


class SemanticVetoRepresentativeBandPerformanceTests(unittest.TestCase):
    def test_filters_representative_lane_and_reports_band_performance(self) -> None:
        report = build_representative_band_performance_report(
            policy_payload=_policy(),
            difficulty_payload={
                "pair": "en-es",
                "decision": "unit_difficulty",
                "case_traces": [
                    _row(
                        lane_id="sampling_stage1_representative_proxy",
                        case_id="r1",
                        trigger="bank",
                        product_outcome="positive_allow",
                        source_rank="501-1000",
                        winner="active",
                    ),
                    _row(
                        lane_id="sampling_stage1_representative_proxy",
                        case_id="r2",
                        trigger="bank",
                        product_outcome="negative_abstain",
                        source_rank="501-1000",
                        winner="shadow",
                    ),
                    _row(
                        lane_id="sampling_stage1_representative_proxy",
                        case_id="r3",
                        trigger="plant",
                        product_outcome="positive_abstain",
                        source_rank="missing",
                        winner="active",
                    ),
                    _row(
                        lane_id="stress_lane",
                        case_id="s1",
                        trigger="stress",
                        product_outcome="negative_allow",
                        source_rank="1-500",
                        winner="shadow",
                    ),
                ],
            },
            source_zipf_by_trigger={"bank": 5.2, "plant": 4.3},
            generated_at="2026-05-06T00:00:00Z",
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["summary"]["case_count"], 3)
        self.assertEqual(report["summary"]["source_rank_known_rows"], 2)
        self.assertEqual(report["summary"]["source_zipf_known_rows"], 3)
        self.assertEqual(
            report["answer_to_band_question"]["same_band_performance_claim"],
            "not_supported",
        )

        by_rank = {row["scope_id"]: row for row in report["breakdowns"]["source_trigger_rank_en"]}
        self.assertEqual(by_rank["501-1000"]["case_count"], 2)
        self.assertEqual(by_rank["501-1000"]["positive_allow_rate"], 1.0)
        self.assertEqual(by_rank["501-1000"]["negative_abstain_rate"], 1.0)
        self.assertEqual(by_rank["missing"]["positive_allow_rate"], 0.0)

        by_zipf = {row["scope_id"]: row for row in report["breakdowns"]["source_zipf_frequency_en"]}
        self.assertEqual(by_zipf["zipf_5_plus_very_common"]["case_count"], 2)
        self.assertEqual(by_zipf["zipf_4_to_5_common"]["case_count"], 1)
        self.assertEqual(by_zipf["zipf_4_to_5_common"]["positive_allow_rate"], 0.0)

        cross_rows = report["breakdowns"]["source_trigger_rank_en_by_gold_winner_type"]
        self.assertIn(
            ("501-1000", "active"),
            {(row["left_scope_id"], row["right_scope_id"]) for row in cross_rows},
        )

        markdown = render_representative_band_performance_markdown(report)
        self.assertIn("Answer To The Band Question", markdown)
        self.assertIn("Source Trigger Rank", markdown)
        self.assertIn("Source Zipf Frequency", markdown)

    def test_reports_review_when_lane_is_missing(self) -> None:
        report = build_representative_band_performance_report(
            policy_payload=_policy(),
            difficulty_payload={"case_traces": []},
            generated_at="2026-05-06T00:00:00Z",
        )

        self.assertEqual(report["status"], "review")
        self.assertIn("representative_lane_has_no_case_traces", report["summary"]["issues"])


def _policy() -> dict[str, object]:
    return {
        "pair": "en-es",
        "acceptance": {
            "positive_allow_rate_min": 0.8,
            "negative_abstain_rate_min": 0.5,
            "utility_must_beat_lexical_baseline": False,
            "utility_must_beat_abstain_all_baseline": False,
        },
        "utility_weights": {
            "positive_allow": 1.0,
            "positive_abstain": -0.4,
            "negative_abstain": 0.8,
            "negative_allow": -0.6,
        },
    }


def _row(
    *,
    lane_id: str,
    case_id: str,
    trigger: str,
    product_outcome: str,
    source_rank: str,
    winner: str,
) -> dict[str, object]:
    return {
        "lane_id": lane_id,
        "case_id": case_id,
        "family_id": f"fam:{trigger}",
        "trigger": trigger,
        "product_outcome": product_outcome,
        "source_trigger_rank_bin_en": source_rank,
        "target_lemma_rank_bin_es": "missing",
        "wordnet_sense_count_bin": "missing",
        "declared_ambiguity_class": "high",
        "gold_winner_type": winner,
        "context_source": "unit",
    }


if __name__ == "__main__":
    unittest.main()
