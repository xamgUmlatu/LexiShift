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
from semantic_veto_representative_heuristic_band_sampler_en_es import (  # noqa: E402
    _sample_sort_key,
    build_representative_heuristic_band_sampler_report,
    render_representative_heuristic_band_sampler_markdown,
)
from semantic_wordnet_source_adapter_support import WordNetIndex  # noqa: E402


class SemanticVetoRepresentativeHeuristicBandSamplerTests(unittest.TestCase):
    def test_samples_by_frozen_cell_seed_not_rank_order(self) -> None:
        report = build_representative_heuristic_band_sampler_report(
            source_frequency=FrequencyLookup.from_records(
                language="en",
                rows={
                    "alpha": {"rank": 100, "frequency": 1000},
                    "bravo": {"rank": 120, "frequency": 900},
                    "charlie": {"rank": 140, "frequency": 800},
                    "delta": {"rank": 160, "frequency": 700},
                    "echo": {"rank": 180, "frequency": 600},
                    "foxtrot": {"rank": 220, "frequency": 500},
                    "golf": {"rank": 1500, "frequency": 400},
                },
            ),
            wordnet_index=_wordnet_index(),
            difficulty_payload={
                "status": "ok",
                "case_traces": [
                    {
                        "trigger": "delta",
                        "gold_decision": "replace",
                        "product_outcome": "positive_allow",
                    }
                ],
            },
            sample_per_cell=2,
            seed="unit-test-seed",
            generated_at="2026-05-06T00:00:00Z",
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["decision"], "representative_heuristic_band_sample_frozen")
        self.assertEqual(report["summary"]["measured_trigger_exclusion_count"], 1)
        sampled_triggers = {row["trigger"] for row in report["sampled_rows"]}
        self.assertNotIn("delta", sampled_triggers)

        high_cross_cell = next(
            cell
            for cell in report["cells"]
            if cell["source_rank_band"] == "1-500"
            and cell["polysemy_band"] == "high_10_plus"
            and cell["pos_shape"] == "cross_pos_polysemy"
        )
        eligible = [
            {
                "trigger": "charlie",
                "source_rank_band": "1-500",
                "polysemy_band": "high_10_plus",
                "pos_shape": "cross_pos_polysemy",
            },
            {
                "trigger": "echo",
                "source_rank_band": "1-500",
                "polysemy_band": "high_10_plus",
                "pos_shape": "cross_pos_polysemy",
            },
            {
                "trigger": "foxtrot",
                "source_rank_band": "1-500",
                "polysemy_band": "high_10_plus",
                "pos_shape": "cross_pos_polysemy",
            },
        ]
        expected = [
            row["trigger"]
            for row in sorted(
                eligible,
                key=lambda row: _sample_sort_key(
                    seed="unit-test-seed",
                    row=row,
                    cell_key=("1-500", "high_10_plus", "cross_pos_polysemy"),
                ),
            )[:2]
        ]
        self.assertEqual(high_cross_cell["sampled_triggers"], expected)
        self.assertEqual(high_cross_cell["eligible_count"], 3)
        self.assertEqual(high_cross_cell["sample_count"], 2)
        self.assertEqual(high_cross_cell["cell_sampling_weight"], 1.5)

        forbidden = {"gold_decision", "product_outcome", "observed_failure_count"}
        self.assertTrue(all(forbidden.isdisjoint(row.keys()) for row in report["sampled_rows"]))
        self.assertTrue(report["e2e_checks"]["empty_cells_are_preserved"])

        markdown = render_representative_heuristic_band_sampler_markdown(report)
        self.assertIn("Representative Heuristic-Band Sampler", markdown)
        self.assertIn("hard-case bias", markdown)


def _wordnet_index() -> WordNetIndex:
    entries: dict[str, dict[str, object]] = {}
    synsets: dict[str, dict[str, object]] = {}

    def add_word(word: str, pos_counts: dict[str, int]) -> None:
        entry = {}
        for pos, count in pos_counts.items():
            senses = []
            for index in range(count):
                synset_id = f"{word}-{pos}-{index}"
                senses.append({"synset": synset_id, "sent": [f"{word} {pos} example"]})
                synsets[synset_id] = {
                    "definition": [f"{word} {pos} definition {index}"],
                    "example": [f"{word} {pos} sample {index}"],
                    "members": [word],
                }
            entry[pos] = {"sense": senses}
        entries[word] = entry

    add_word("alpha", {"n": 1})
    add_word("bravo", {"n": 4})
    add_word("charlie", {"n": 5, "v": 5})
    add_word("delta", {"n": 5, "v": 5})
    add_word("echo", {"n": 5, "v": 5})
    add_word("foxtrot", {"n": 5, "v": 5})
    add_word("golf", {"n": 2, "v": 2})
    return WordNetIndex(
        entries_by_word=entries,
        synsets_by_id=synsets,
        hyponyms_by_synset={},
        source_file_count=1,
    )


if __name__ == "__main__":
    unittest.main()
