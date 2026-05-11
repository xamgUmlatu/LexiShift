from __future__ import annotations

from pathlib import Path
import sys
import unittest


CORE_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = CORE_ROOT.parent
SCRIPTS_ROOT = REPO_ROOT / "scripts" / "testing"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from semantic_veto_active_only_scale_tranche_requests_en_es import (  # noqa: E402
    build_active_only_scale_tranche_request_report,
    render_active_only_scale_tranche_markdown,
)


class SemanticVetoActiveOnlyScaleTrancheRequestsTests(unittest.TestCase):
    def test_selects_only_uncovered_active_requests_without_llm_call(self) -> None:
        report = build_active_only_scale_tranche_request_report(
            band_plan_payload=_band_plan_payload(),
            existing_evidence_payloads=[_covered_evidence_payload("family:bank:banco")],
            requested_items=3,
            generated_at="2026-05-10T00:00:00Z",
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(
            report["decision"],
            "active_only_scale_tranche_request_packet_ready",
        )
        self.assertEqual(report["strict_flow"]["llm_call"], "none")
        self.assertEqual(report["strict_flow"]["shadow_generation"], "excluded")
        self.assertEqual(report["selection"]["covered_family_count"], 1)
        self.assertEqual(report["selection"]["selected_family_count"], 2)
        self.assertEqual(report["summary"]["request_count"], 2)
        self.assertEqual(report["summary"]["expected_generated_item_count"], 6)
        self.assertEqual(report["summary"]["requests_by_arm"]["high_need"]["request_count"], 1)
        self.assertEqual(
            report["summary"]["requests_by_arm"]["middle_control"]["request_count"],
            1,
        )
        self.assertEqual(report["request_checks"]["all_active_only"], True)

        request_ids = [request["request_id"] for request in report["requests"]]
        self.assertFalse(any("family:bank:banco" in value for value in request_ids))
        for request in report["requests"]:
            self.assertEqual(request["slot_type"], "active_evidence_expansion")
            self.assertEqual(request["requested_items"], 3)
            self.assertEqual(request["expected_output_token_budget"], 420)
            self.assertIn("Return exactly one JSON object", request["prompt_text"])
            self.assertIn("known_shadow_targets", request["prompt_text"])

        selected_slot = report["selected_families"][0]["planned_generation_slots"][0]
        self.assertEqual(selected_slot["requested_items"], 3)

        markdown = render_active_only_scale_tranche_markdown(report)
        self.assertIn("Active-Only Scale Tranche Requests", markdown)
        self.assertIn("Covered families excluded: `1`", markdown)

    def test_reports_review_when_every_family_is_already_covered(self) -> None:
        report = build_active_only_scale_tranche_request_report(
            band_plan_payload={"schema_version": 1, "pair": "en-es", "band_family_rows": []},
            existing_evidence_payloads=[],
            generated_at="2026-05-10T00:00:00Z",
        )

        self.assertEqual(report["status"], "review")
        self.assertEqual(report["summary"]["request_count"], 0)
        self.assertIn("No uncovered families selected.", report["issues"][0]["message"])


def _band_plan_payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "pair": "en-es",
        "band_family_rows": [
            _family("high_need", 1, "family:bank:banco", "bank", "banco"),
            _family("high_need", 2, "family:current:contemporaneo", "current", "contemporáneo"),
            _family("middle_control", 1, "family:pair:par", "pair", "par"),
        ],
    }


def _family(
    arm: str,
    band_rank: int,
    family_id: str,
    trigger: str,
    target: str,
) -> dict[str, object]:
    return {
        "family_id": family_id,
        "pilot_arm": arm,
        "band_rank": band_rank,
        "predicted_need": 0.75,
        "trigger": trigger,
        "target_lemma": target,
        "active": {
            "target_lemma": target,
            "evidence_text": f"{trigger} means {target} in the active sense.",
        },
        "shadows": [{"target_lemma": "orilla"}],
    }


def _covered_evidence_payload(family_id: str) -> dict[str, object]:
    return {
        "schema_version": 1,
        "rows": [
            {
                "source_id": f"{family_id}:source:001",
                "metadata": {"family_id": family_id},
            }
        ],
    }


if __name__ == "__main__":
    unittest.main()
