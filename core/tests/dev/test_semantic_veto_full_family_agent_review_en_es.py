from __future__ import annotations

from pathlib import Path
import sys
import unittest


CORE_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = CORE_ROOT.parent
SCRIPTS_ROOT = REPO_ROOT / "scripts" / "testing"
for candidate in (str(SCRIPTS_ROOT),):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from semantic_veto_full_family_agent_review_en_es import (  # noqa: E402
    build_full_family_agent_review_report,
    render_full_family_agent_review_markdown,
)


class SemanticVetoFullFamilyAgentReviewTests(unittest.TestCase):
    def test_records_full_family_review_without_trusting_rows(self) -> None:
        report = build_full_family_agent_review_report(
            packet_payload=_packet(),
            review_manifest=[
                _review("change", "cambio", "aligned_mapping_rewrite_contexts", "aligned"),
                _review(
                    "badmap",
                    "deducción",
                    "source_target_mapping_rejected",
                    "source_target_mapping_rejected",
                    action="exclude_from_trusted_eval",
                ),
            ],
            generated_at="2026-05-07T00:00:00Z",
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(
            report["decision"], "full_family_agent_review_complete_user_approval_required"
        )
        self.assertEqual(report["summary"]["family_count"], 2)
        self.assertEqual(report["summary"]["repair_pool_family_count"], 1)
        self.assertEqual(report["summary"]["excluded_family_count"], 1)
        self.assertEqual(report["summary"]["draft_case_count"], 3)
        self.assertEqual(report["summary"]["draft_shadow_count"], 1)
        self.assertEqual(report["issues"], [])
        self.assertEqual(
            report["family_reviews"][0]["case_policy"]["positive_active"],
            "rewrite_independent_contexts",
        )
        self.assertEqual(
            report["family_reviews"][1]["case_policy"]["positive_active"],
            "exclude_current_rows",
        )

        markdown = render_full_family_agent_review_markdown(report)
        self.assertIn("Full-Family Agent Review", markdown)
        self.assertIn("Repair-pool families", markdown)
        self.assertIn("change -> cambio", markdown)

    def test_flags_missing_reviews_and_non_full_packets(self) -> None:
        packet = _packet()
        packet["summary"]["dataset_family_count"] = 3
        report = build_full_family_agent_review_report(
            packet_payload=packet,
            review_manifest=[
                _review("change", "cambio", "aligned_mapping_rewrite_contexts", "aligned"),
            ],
            generated_at="2026-05-07T00:00:00Z",
        )

        self.assertEqual(report["status"], "review")
        self.assertIn("packet_does_not_cover_full_dataset", report["issues"])
        self.assertIn("missing_review:badmap->deducción", report["issues"])


def _packet() -> dict[str, object]:
    return {
        "schema_version": 1,
        "pair": "en-es",
        "decision": "full_family_human_review_packet_ready",
        "summary": {
            "dataset_family_count": 2,
            "review_family_count": 2,
        },
        "family_review_rows": [
            _family("change", "cambio", shadow=False),
            _family("badmap", "deducción", shadow=True),
        ],
    }


def _family(source: str, target: str, *, shadow: bool) -> dict[str, object]:
    family_id = f"fam:{source}:{target}"
    shadows = (
        [
            {
                "sense_id": f"{family_id}:shadow:1",
                "target_lemma": f"{source} alternate sense 1",
            }
        ]
        if shadow
        else []
    )
    cases = [
        {
            "case_id": f"{family_id}:001",
            "manual_case_type": "positive_active",
        }
    ]
    if shadow:
        cases.append(
            {
                "case_id": f"{family_id}:002",
                "manual_case_type": "shadow_negative",
            }
        )
    return {
        "family_id": family_id,
        "trigger": source,
        "target_lemma": target,
        "source_zipf_band_en": "zipf_5_plus_very_common",
        "target_zipf_band_es": "zipf_4_to_5_common",
        "polysemy_band": "low_1_to_3",
        "pos_shape": "same_pos_polysemy",
        "shadow_evidence": shadows,
        "case_review_rows": cases,
    }


def _review(
    source: str,
    target: str,
    disposition: str,
    active_status: str,
    *,
    action: str = "repair_pool",
) -> dict[str, str]:
    return {
        "trigger": source,
        "target": target,
        "active_sense_status": active_status,
        "family_disposition": disposition,
        "scoring_action": action,
        "corrected_active_gloss": "reviewed sense",
        "notes": "unit test review",
    }


if __name__ == "__main__":
    unittest.main()
