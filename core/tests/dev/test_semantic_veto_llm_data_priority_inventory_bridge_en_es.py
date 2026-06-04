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

from semantic_veto_llm_data_priority_inventory_bridge_en_es import (  # noqa: E402
    build_llm_data_priority_inventory_bridge_report,
    render_llm_data_priority_inventory_bridge_markdown,
)


class SemanticVetoLlmDataPriorityInventoryBridgeTests(unittest.TestCase):
    def test_inventory_bridge_separates_target_family_construction_from_llm_packets(self) -> None:
        report = build_llm_data_priority_inventory_bridge_report(
            inventory_payload=_inventory_payload(),
            priority_scan_payload=_priority_scan_payload(),
            top_n=3,
            generated_at="2026-05-06T00:00:00Z",
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["decision"], "llm_data_priority_inventory_bridge_established")
        self.assertTrue(report["e2e_checks"]["inventory_only_rows_have_no_llm_packet"])
        self.assertTrue(report["e2e_checks"]["scored_rows_link_to_priority_scan"])
        self.assertEqual(report["summary"]["inventory_candidate_count"], 3)
        self.assertEqual(report["summary"]["trigger_target_pair_scored_count"], 1)
        self.assertEqual(report["summary"]["needs_target_family_count"], 2)

        by_trigger = {row["trigger"]: row for row in report["priority_rows"]}
        self.assertEqual(by_trigger["change"]["readiness_stage"], "trigger_target_pair_scored")
        self.assertEqual(
            by_trigger["change"]["recommended_next_action"],
            "use_scored_pair_llm_packet_or_refresh_contexts",
        )
        self.assertEqual(
            by_trigger["blue"]["readiness_stage"], "needs_translation_target_shadow_family"
        )
        self.assertEqual(by_trigger["blue"]["llm_packet_from_scored_pairs"], {})

        markdown = render_llm_data_priority_inventory_bridge_markdown(report)
        self.assertIn("Inventory Bridge", markdown)
        self.assertIn("End-State Contract", markdown)
        self.assertIn("ordinary_lexical_replacement", markdown)


def _inventory_payload() -> dict[str, object]:
    return {
        "pair": "en-es",
        "decision": "inventory_candidates_found",
        "candidates": [
            _candidate("blue", 16.1, 16, {"adjective": 8, "noun": 7, "verb": 1}),
            _candidate("change", 16.1, 20, {"noun": 10, "verb": 10}),
            _candidate("plain", 13.5, 11, {"adjective": 7, "noun": 2, "verb": 1}),
        ],
    }


def _priority_scan_payload() -> dict[str, object]:
    return {
        "pair": "en-es",
        "decision": "llm_data_priority_scan_established",
        "priority_rows": [
            {
                "trigger": "change",
                "target_lemma": "cambio",
                "priority_rank": 4,
                "scored_context_llm_data_need": 0.31,
                "recommended_llm_packet": {
                    "active_rows": 4,
                    "shadow_rows": 4,
                    "phrase_rows": 8,
                    "locked_eval_rows": 4,
                },
            }
        ],
    }


def _candidate(
    trigger: str,
    score: float,
    sense_count: int,
    pos_counts: dict[str, int],
) -> dict[str, object]:
    return {
        "candidate_id": f"candidate:{trigger}",
        "trigger": trigger,
        "score": score,
        "sense_count": sense_count,
        "pos_counts": pos_counts,
        "source_example_count": 20,
        "source_definition_count": 12,
        "cross_pos": len(pos_counts) > 1,
        "noun_verb": "noun" in pos_counts and "verb" in pos_counts,
        "same_pos_polysemy": any(value >= 2 for value in pos_counts.values()),
        "sample_synsets": [{"definition": "unit", "example": "unit"}],
    }


if __name__ == "__main__":
    unittest.main()
