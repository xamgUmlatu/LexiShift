from __future__ import annotations

from pathlib import Path
import sys
import unittest


CORE_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = CORE_ROOT.parent
SCRIPTS_ROOT = REPO_ROOT / "scripts" / "testing"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from semantic_veto_evidence_gap_active_only_poc_requests_en_es import (  # noqa: E402
    build_active_only_poc_request_report,
    render_active_only_poc_request_markdown,
)


class SemanticVetoEvidenceGapActiveOnlyPocRequestsTests(unittest.TestCase):
    def test_freezes_balanced_active_only_batch(self) -> None:
        report = build_active_only_poc_request_report(
            source_payload=_source_payload(),
            source_path=Path("docs/test_outputs/source.json"),
            generated_at="2026-05-09T00:00:00Z",
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["summary"]["request_count"], 24)
        self.assertEqual(report["summary"]["family_count"], 24)
        self.assertEqual(report["summary"]["expected_generated_item_count"], 48)
        self.assertEqual(
            {
                arm: row["request_count"]
                for arm, row in report["summary"]["requests_by_arm"].items()
            },
            {"high_need": 8, "low_control": 8, "middle_control": 8},
        )
        self.assertTrue(
            all(row["slot_type"] == "active_evidence_expansion" for row in report["requests"])
        )
        markdown = render_active_only_poc_request_markdown(report)
        self.assertIn("Active-Only PoC", markdown)
        self.assertIn("high_need", markdown)

    def test_unbalanced_batch_needs_review(self) -> None:
        payload = _source_payload()
        removed_active = False
        retained_requests = []
        for row in payload["requests"]:
            if not removed_active and row["slot_type"] == "active_evidence_expansion":
                removed_active = True
                continue
            retained_requests.append(row)
        payload["requests"] = retained_requests

        report = build_active_only_poc_request_report(
            source_payload=payload,
            generated_at="2026-05-09T00:00:00Z",
        )

        self.assertEqual(report["status"], "review")
        self.assertGreater(report["request_checks"]["issue_count"], 0)


def _source_payload() -> dict[str, object]:
    requests = []
    for arm in ("high_need", "middle_control", "low_control"):
        for index in range(8):
            family_id = f"family:{arm}:{index}"
            requests.append(
                {
                    "request_id": f"{family_id}:active",
                    "family_id": family_id,
                    "pilot_arm": arm,
                    "slot_type": "active_evidence_expansion",
                    "requested_items": 2,
                    "prompt_text": f"source {index}",
                    "trigger": f"source{index}",
                    "active_target_lemma": f"target{index}",
                    "estimated_input_tokens": 10,
                    "expected_output_token_budget": 280,
                }
            )
            requests.append(
                {
                    "request_id": f"{family_id}:shadow",
                    "family_id": family_id,
                    "pilot_arm": arm,
                    "slot_type": "shadow_or_competitor_evidence_probe",
                    "requested_items": 2,
                    "prompt_text": f"shadow {index}",
                    "trigger": f"source{index}",
                    "active_target_lemma": f"target{index}",
                }
            )
    return {
        "schema_version": 1,
        "pair": "en-es",
        "pilot": {
            "pilot_id": "pilot",
            "plan_status": "ok",
            "request_kind": "semantic_veto_evidence_gap_generation",
            "prompt_id": "semantic_veto_evidence_gap_generation_v5",
        },
        "requests": requests,
    }


if __name__ == "__main__":
    unittest.main()
