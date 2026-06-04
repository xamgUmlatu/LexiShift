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

from semantic_veto_difficulty_stratification_en_es import FrequencyLookup  # noqa: E402
from semantic_veto_heuristic_group_pilot_en_es import (  # noqa: E402
    build_heuristic_group_pilot_report,
    render_heuristic_group_pilot_markdown,
)
from semantic_wordnet_source_adapter_support import WordNetIndex  # noqa: E402


class SemanticVetoHeuristicGroupPilotTests(unittest.TestCase):
    def test_primary_groups_are_pre_outcome_and_sentinel_is_separate(self) -> None:
        report = build_heuristic_group_pilot_report(
            source_frequency=FrequencyLookup.from_records(
                language="en",
                rows={
                    "alpha": {"rank": 100, "frequency": 1000},
                    "bravo": {"rank": 200, "frequency": 900},
                    "charlie": {"rank": 1200, "frequency": 800},
                    "delta": {"rank": 1300, "frequency": 700},
                    "echo": {"rank": 5200, "frequency": 600},
                    "foxtrot": {"rank": 5300, "frequency": 500},
                    "plant": {"rank": 300, "frequency": 400},
                },
            ),
            wordnet_index=_wordnet_index(),
            difficulty_payload={
                "status": "ok",
                "case_traces": [{"trigger": "plant"}],
                "trigger_risk_summary": [
                    {
                        "trigger": "plant",
                        "source_trigger_rank_bin_en": "missing",
                        "failure_count": 4,
                        "negative_allow_count": 3,
                        "positive_abstain_count": 1,
                    }
                ],
            },
            group_size=1,
            sentinel_size=1,
            generated_at="2026-05-05T00:00:00Z",
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(
            report["decision"],
            "heuristic_group_pilot_ready_for_manual_tests",
        )
        groups = {row["group_id"]: row for row in report["groups"]}
        self.assertEqual(groups["core_high_polysemy"]["triggers"][0]["trigger"], "alpha")
        self.assertEqual(groups["core_low_polysemy_control"]["triggers"][0]["trigger"], "bravo")
        self.assertEqual(groups["mid_high_polysemy"]["triggers"][0]["trigger"], "charlie")
        self.assertEqual(groups["mid_low_polysemy_control"]["triggers"][0]["trigger"], "delta")
        self.assertEqual(groups["tail_high_polysemy"]["triggers"][0]["trigger"], "echo")
        self.assertEqual(groups["tail_low_polysemy_control"]["triggers"][0]["trigger"], "foxtrot")

        sentinel = groups["measured_missing_rank_high_failure_sentinel"]
        self.assertEqual(sentinel["selection_mode"], "outcome_informed_sentinel")
        self.assertEqual(sentinel["triggers"][0]["trigger"], "plant")
        self.assertEqual(sentinel["triggers"][0]["observed_failure_count"], 4)

        primary_triggers = {
            trigger["trigger"]
            for group in report["groups"]
            if group["selection_mode"] == "pre_outcome"
            for trigger in group["triggers"]
        }
        self.assertNotIn("plant", primary_triggers)

        manual_packet = report["manual_review_packet"]
        self.assertEqual(len(manual_packet), 7)
        self.assertTrue(all(len(row["case_slots"]) == 5 for row in manual_packet))
        self.assertIn("input_fingerprint", report)

        markdown = render_heuristic_group_pilot_markdown(report)
        self.assertIn("Heuristic Group Pilot", markdown)
        self.assertIn("outcome-informed", markdown)
        self.assertIn("core_high_polysemy", markdown)


def _wordnet_index() -> WordNetIndex:
    entries: dict[str, dict[str, object]] = {}
    synsets: dict[str, dict[str, object]] = {}

    def add_word(word: str, pos_counts: dict[str, int]) -> None:
        entry = {}
        for pos, count in pos_counts.items():
            senses = []
            for index in range(count):
                synset_id = f"{word}-{pos}-{index}"
                senses.append({"synset": synset_id, "sent": [f"{word} {pos} example {index}"]})
                synsets[synset_id] = {
                    "definition": [f"{word} {pos} definition {index}"],
                    "example": [f"{word} {pos} sample {index}"],
                    "members": [word],
                }
            entry[pos] = {"sense": senses}
        entries[word] = entry

    add_word("alpha", {"n": 5, "v": 5})
    add_word("bravo", {"n": 2})
    add_word("charlie", {"n": 4, "v": 4})
    add_word("delta", {"n": 1})
    add_word("echo", {"n": 4, "v": 4})
    add_word("foxtrot", {"n": 1})
    add_word("plant", {"n": 6, "v": 4})
    return WordNetIndex(
        entries_by_word=entries,
        synsets_by_id=synsets,
        hyponyms_by_synset={},
        source_file_count=2,
    )


if __name__ == "__main__":
    unittest.main()
