from __future__ import annotations

from pathlib import Path
import sys
import unittest


CORE_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = CORE_ROOT.parent
SCRIPTS_ROOT = REPO_ROOT / "scripts" / "testing"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from semantic_veto_evidence_gap_prompt_variant_requests_en_es import (  # noqa: E402
    build_prompt_variant_manifest,
    build_prompt_variant_packets,
    render_prompt_variant_manifest_markdown,
)


class SemanticVetoEvidenceGapPromptVariantRequestsTests(unittest.TestCase):
    def test_builds_four_variants_over_same_active_only_denominator(self) -> None:
        packets = build_prompt_variant_packets(
            source_payload=_source_payload(),
            dataset_payload=_dataset_payload(),
            generated_at="2026-05-09T00:00:00Z",
        )
        report = build_prompt_variant_manifest(
            packets=packets,
            packet_paths={variant_id: Path(f"{variant_id}.json") for variant_id in packets},
            generated_at="2026-05-09T00:00:00Z",
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(
            set(packets),
            {
                "v5_refresh_control",
                "v6_pos_only",
                "v6_diversity_only",
                "v6_pos_diversity",
            },
        )
        family_sets = {
            variant_id: {row["family_id"] for row in packet["requests"]}
            for variant_id, packet in packets.items()
        }
        self.assertEqual(len({tuple(sorted(values)) for values in family_sets.values()}), 1)
        self.assertEqual(report["summary"]["total_request_count_if_all_variants_run"], 96)

        control_prompt = packets["v5_refresh_control"]["requests"][0]["prompt_text"]
        self.assertEqual(control_prompt, "existing v5 prompt")
        pos_prompt = packets["v6_pos_only"]["requests"][0]["prompt_text"]
        self.assertIn("expected_pos: verb", pos_prompt)
        self.assertIn("Avoid noun-like frames", pos_prompt)
        combined_prompt = packets["v6_pos_diversity"]["requests"][0]["prompt_text"]
        self.assertIn("Diversity rules", combined_prompt)
        self.assertIn("source_pos_frame", combined_prompt)

        markdown = render_prompt_variant_manifest_markdown(report)
        self.assertIn("Prompt Variant", markdown)
        self.assertIn("v6_pos_diversity", markdown)


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
                    "slot_id": f"{family_id}:active",
                    "slot_type": "active_evidence_expansion",
                    "slot_target_lemma": "sonreír",
                    "requested_items": 2,
                    "prompt_text": "existing v5 prompt",
                    "trigger": "smile",
                    "active_target_lemma": "sonreír",
                    "active_evidence_text": "smile -> sonreír | smile as a verb",
                    "estimated_input_tokens": 10,
                    "expected_output_token_budget": 280,
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


def _dataset_payload() -> dict[str, object]:
    return {
        "families": [
            {
                "family_id": f"family:{arm}:{index}",
                "active": {"canonical_pos": "verb"},
            }
            for arm in ("high_need", "middle_control", "low_control")
            for index in range(8)
        ]
    }


if __name__ == "__main__":
    unittest.main()
