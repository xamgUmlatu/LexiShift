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
from semantic_veto_representative_sampling_methodology_comparison_en_es import (  # noqa: E402
    build_sampling_methodology_comparison_report,
    render_sampling_methodology_comparison_markdown,
)
from semantic_wordnet_source_adapter_support import WordNetIndex  # noqa: E402


class SemanticVetoRepresentativeSamplingMethodologyComparisonTests(unittest.TestCase):
    def test_compares_old_rank_sorted_pilot_with_representative_cells(self) -> None:
        report = build_sampling_methodology_comparison_report(
            pilot_payload=_pilot_payload(),
            representative_sample_payload=_sample_payload(),
            construction_payload=_construction_payload(),
            source_frequency=FrequencyLookup.from_records(
                language="en",
                rows={
                    "alpha": {"rank": 100, "frequency": 1000},
                    "bravo": {"rank": 120, "frequency": 900},
                    "charlie": {"rank": 140, "frequency": 800},
                    "delta": {"rank": 160, "frequency": 700},
                    "echo": {"rank": 180, "frequency": 600},
                    "foxtrot": {"rank": 1200, "frequency": 500},
                    "golf": {"rank": 1400, "frequency": 400},
                    "hotel": {"rank": 5200, "frequency": 300},
                },
            ),
            wordnet_index=_wordnet_index(),
            difficulty_payload={"case_traces": []},
            sample_sizes=[1, 2],
            seeds=["seed-a", "seed-b"],
            generated_at="2026-05-06T00:00:00Z",
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["decision"], "sampling_methodology_comparison_established")
        old = report["comparison"]["old_heuristic_group_pilot"]
        new = report["comparison"]["representative_sampler"]
        self.assertEqual(old["primary_selected_trigger_count"], 2)
        self.assertEqual(new["sampled_trigger_count"], 3)
        self.assertEqual(new["sampled_nonempty_cell_coverage_rate"], 1.0)
        self.assertTrue(report["e2e_checks"]["stability_runs_cover_all_nonempty_cells"])
        self.assertEqual(report["sampling_stability"]["seed_count"], 2)
        self.assertIn(
            "heuristic_difficulty_surface", {row["sweep"] for row in report["sweep_rerun_status"]}
        )

        markdown = render_sampling_methodology_comparison_markdown(report)
        self.assertIn("Sampling Methodology Comparison", markdown)
        self.assertIn("Old Group Bias", markdown)


def _pilot_payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "summary": {"candidate_pool_count": 8},
        "groups": [
            {
                "group_id": "core_high_polysemy",
                "selection_mode": "pre_outcome",
                "triggers": [
                    _pilot_row("alpha", rank=100, senses=10, pos_count=2),
                    _pilot_row("bravo", rank=120, senses=10, pos_count=2),
                ],
            },
            {
                "group_id": "measured_missing_rank_high_failure_sentinel",
                "selection_mode": "outcome_informed_sentinel",
                "triggers": [_pilot_row("missing", rank=None, senses=3, pos_count=1)],
            },
        ],
    }


def _pilot_row(trigger: str, *, rank: int | None, senses: int, pos_count: int) -> dict[str, object]:
    return {
        "trigger": trigger,
        "source_rank": rank,
        "wordnet_sense_count": senses,
        "wordnet_pos_count": pos_count,
    }


def _sample_payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "pair": "en-es",
        "status": "ok",
        "decision": "representative_heuristic_band_sample_frozen",
        "methodology": {"sample_per_cell": 2},
        "summary": {
            "candidate_universe_count": 8,
            "cell_count": 3,
            "nonempty_cell_count": 3,
        },
        "cells": [
            _cell(
                "source_rank_band=1-500::polysemy_band=high_10_plus::pos_shape=cross_pos_polysemy"
            ),
            _cell("source_rank_band=1001-2000::polysemy_band=low_1_to_3::pos_shape=single_sense"),
            _cell("source_rank_band=>10000::polysemy_band=low_1_to_3::pos_shape=single_sense"),
        ],
        "sampled_rows": [
            _sample_row(
                "alpha",
                "source_rank_band=1-500::polysemy_band=high_10_plus::pos_shape=cross_pos_polysemy",
            ),
            _sample_row(
                "foxtrot",
                "source_rank_band=1001-2000::polysemy_band=low_1_to_3::pos_shape=single_sense",
            ),
            _sample_row(
                "hotel", "source_rank_band=>10000::polysemy_band=low_1_to_3::pos_shape=single_sense"
            ),
        ],
    }


def _cell(cell_id: str) -> dict[str, object]:
    return {"cell_id": cell_id, "eligible_count": 1}


def _sample_row(trigger: str, cell_id: str) -> dict[str, object]:
    parts = dict(part.split("=", 1) for part in cell_id.split("::"))
    return {
        "trigger": trigger,
        "cell_id": cell_id,
        "source_rank_band": parts["source_rank_band"],
        "polysemy_band": parts["polysemy_band"],
        "pos_shape": parts["pos_shape"],
        "cell_sampling_weight": 1.0,
    }


def _construction_payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "summary": {
            "attempted_sample_count": 3,
            "source_ready_family_count": 1,
            "weak_diagnostic_family_count": 1,
            "blocked_count": 1,
            "source_ready_rate": 0.3333,
            "reason_counts": {"constructed_family": 2, "missing_noun_or_verb_translation": 1},
        },
    }


def _wordnet_index() -> WordNetIndex:
    entries: dict[str, dict[str, object]] = {}
    synsets: dict[str, dict[str, object]] = {}

    def add_word(word: str, pos_counts: dict[str, int]) -> None:
        entry = {}
        for pos, count in pos_counts.items():
            senses = []
            for index in range(count):
                synset_id = f"{word}-{pos}-{index}"
                senses.append({"synset": synset_id})
                synsets[synset_id] = {
                    "definition": [f"{word} {pos} definition {index}"],
                    "example": [f"{word} {pos} sample {index}"],
                    "members": [word],
                }
            entry[pos] = {"sense": senses}
        entries[word] = entry

    add_word("alpha", {"n": 5, "v": 5})
    add_word("bravo", {"n": 5, "v": 5})
    add_word("charlie", {"n": 5, "v": 5})
    add_word("delta", {"n": 5, "v": 5})
    add_word("echo", {"n": 5, "v": 5})
    add_word("foxtrot", {"n": 1})
    add_word("golf", {"n": 1})
    add_word("hotel", {"n": 1})
    return WordNetIndex(
        entries_by_word=entries,
        synsets_by_id=synsets,
        hyponyms_by_synset={},
        source_file_count=1,
    )


if __name__ == "__main__":
    unittest.main()
