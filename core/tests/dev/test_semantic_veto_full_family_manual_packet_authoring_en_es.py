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

from semantic_routing_sentence_veto_support import load_sentence_veto_dataset  # noqa: E402
from semantic_veto_full_family_manual_packet_authoring_en_es import (  # noqa: E402
    build_full_family_manual_packet_authoring_report,
    render_full_family_manual_packet_markdown,
)


class SemanticVetoFullFamilyManualPacketAuthoringTests(unittest.TestCase):
    def test_materializes_scoreable_dataset_from_frozen_sample(self) -> None:
        report, dataset = build_full_family_manual_packet_authoring_report(
            sample_payload={
                "pair": "en-es",
                "decision": "full_family_representative_sample_frozen",
                "manual_authoring_queue": [
                    _sample("change", "cambio", "zipf_5_plus_very_common", "candidate_polysemic"),
                    _sample("abate", "decrecer", "zipf_below_3_rare", "not_applicable"),
                    _sample("bark", "ladrar", "zipf_3_to_4_mid", "candidate_polysemic"),
                ],
            },
            sense_rows_by_source={
                "change": [
                    _sense("n", "the act of becoming different", "The change happened slowly."),
                    _sense(
                        "n", "coins received back after payment", "I need change for the meter."
                    ),
                ],
                "abate": [
                    _sense("v", "to become less intense", "The storm will abate tonight."),
                ],
                "bark": [
                    _sense("v", "to make a dog sound", "The dogs bark loudly."),
                    _sense("n", "the outer covering of a tree", "The bark was rough."),
                ],
            },
            generated_at="2026-05-06T00:00:00Z",
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["summary"]["dataset_family_count"], 3)
        self.assertEqual(report["summary"]["dataset_case_count"], 8)
        self.assertTrue(report["e2e_checks"]["mid_cases_present"])
        self.assertTrue(report["e2e_checks"]["rare_cases_present"])
        self.assertEqual(dataset["dataset_id"], "en_es_full_family_representative_manual_v1")

        families = {family["trigger"]: family for family in dataset["families"]}
        self.assertEqual(len(families["change"]["shadows"]), 1)
        self.assertEqual(len(families["abate"]["shadows"]), 0)
        self.assertEqual(
            {case["gold_decision"] for case in families["change"]["cases"]},
            {"replace", "abstain"},
        )
        for family in families.values():
            sentences = [case["sentence"] for case in family["cases"]]
            self.assertEqual(len(sentences), len(set(sentences)))
            self.assertFalse(any("same sense as the Spanish target" in row for row in sentences))
            self.assertFalse(any("vocabulary term" in row for row in sentences))
            evidence = family["active"]["evidence_views"]
            self.assertNotIn(family["cases"][0]["sentence"], evidence["all_evidence_text"])
            self.assertIn("source_examples_text", evidence)

        tmp_path = REPO_ROOT / "docs" / "test_outputs" / "_tmp_full_family_packet_test.json"
        try:
            tmp_path.write_text(__import__("json").dumps(dataset), encoding="utf-8")
            loaded = load_sentence_veto_dataset(tmp_path)
            self.assertEqual(len(loaded["families"]), 3)
        finally:
            tmp_path.unlink(missing_ok=True)

        markdown = render_full_family_manual_packet_markdown(report)
        self.assertIn("Full-Family Manual Packet", markdown)
        self.assertIn("agent_draft_human_review_pending", markdown)


def _sample(source: str, target: str, source_band: str, shadow_contract: str) -> dict[str, object]:
    return {
        "source": source,
        "target": target,
        "source_zipf_band_en": source_band,
        "target_zipf_band_es": "zipf_4_to_5_common",
        "wordnet_polysemy_band": "medium_4_to_9",
        "wordnet_pos_shape": "cross_pos_polysemy",
        "manual_packet": {
            "shadow_contract": shadow_contract,
        },
    }


def _sense(pos: str, definition: str, example: str) -> dict[str, object]:
    return {
        "pos": pos,
        "definition": definition,
        "examples": [example],
        "synset_id": definition.replace(" ", "_"),
    }


if __name__ == "__main__":
    unittest.main()
