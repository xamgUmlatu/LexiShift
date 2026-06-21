from __future__ import annotations

from pathlib import Path
import sys
import unittest

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_learner_difficulty_source_arbitration_en_ja import (  # noqa: E402
    ComponentView,
    SourceArbitrationCandidate,
    family_parts,
    pedagogical_values_for_candidate,
)


def _component_view(
    *,
    names: tuple[str, ...],
    rows: list[dict[str, float]],
    lemmas: tuple[str, ...],
    readings: tuple[str, ...],
    ranks: tuple[float, ...],
    frequency: tuple[float, ...],
) -> ComponentView:
    values = np.zeros((len(rows), len(names)), dtype=np.float32)
    present = np.zeros((len(rows), len(names)), dtype=bool)
    name_to_index = {name: index for index, name in enumerate(names)}
    for row_index, row in enumerate(rows):
        for name, value in row.items():
            index = name_to_index[name]
            values[row_index, index] = float(value)
            present[row_index, index] = True
    return ComponentView(
        names=names,
        name_to_index=name_to_index,
        values=values,
        present=present,
        frequency=np.asarray(frequency, dtype=np.float32),
        target_positions=np.linspace(0.0, 1.0, num=len(rows), dtype=np.float32),
        lemmas=np.asarray(lemmas),
        readings=np.asarray(readings),
        identities=np.asarray([f"id-{index}" for index in range(len(rows))]),
        candidate_states=np.full(len(rows), "normal_vocab"),
        core_ranks=np.asarray(ranks, dtype=np.float32),
    )


def _candidate(
    *,
    jlpt_ped_mode: str = "broad",
    jlpt_exact_blend: float = 0.0,
    jlpt_exact_blend_gate_mode: str = "none",
    jlpt_exact_min_gap: float = 0.0,
    jlpt_inherited_penalty: float = 0.0,
    jlpt_inherited_penalty_mode: str = "none",
) -> SourceArbitrationCandidate:
    return SourceArbitrationCandidate(
        candidate_id="test",
        candidate_family="test",
        ped_mode="min",
        native_mode="mean",
        base_mode="ped_native_min",
        ped_strength=1.0,
        tail_source="base",
        tail_lower=0.50,
        tail_upper=0.85,
        burden_mode="mean",
        burden_delta=0.05,
        entity_delta=0.0,
        entity_gate_mode="weak",
        topic_delta=0.0,
        topic_gate_mode="rarity",
        ordinary_cap=0.58,
        ordinary_cap_mode="hard",
        ordinary_cap_strength=1.0,
        ordinary_gate_mode="mean",
        reading_guard_delta=0.0,
        tail_floor=0.0,
        tail_floor_mode="none",
        same_surface_floor=0.0,
        same_surface_floor_mode="none",
        same_surface_source_attenuation=0.0,
        same_surface_source_attenuation_mode="none",
        jlpt_ped_mode=jlpt_ped_mode,
        jlpt_exact_blend=jlpt_exact_blend,
        jlpt_exact_blend_gate_mode=jlpt_exact_blend_gate_mode,
        jlpt_exact_min_gap=jlpt_exact_min_gap,
        jlpt_inherited_penalty=jlpt_inherited_penalty,
        jlpt_inherited_penalty_mode=jlpt_inherited_penalty_mode,
    )


class TestSrsLearnerDifficultySourceArbitration(unittest.TestCase):
    def test_exact_preferred_pedagogical_score_uses_exact_jlpt_when_present(
        self,
    ) -> None:
        names = (
            "jlpt_vocab_difficulty",
            "jlpt_vocab_exact_difficulty",
            "jlpt_vocab_exact_known",
            "jlpt_vocab_surface_known",
        )
        view = _component_view(
            names=names,
            rows=[
                {
                    "jlpt_vocab_difficulty": 0.08,
                    "jlpt_vocab_exact_difficulty": 0.42,
                    "jlpt_vocab_exact_known": 1.0,
                    "jlpt_vocab_surface_known": 1.0,
                },
                {
                    "jlpt_vocab_difficulty": 0.08,
                    "jlpt_vocab_exact_difficulty": 0.08,
                    "jlpt_vocab_exact_known": 1.0,
                    "jlpt_vocab_surface_known": 1.0,
                },
            ],
            lemmas=("辛い", "辛い"),
            readings=("つらい", "からい"),
            ranks=(1911.0, 7282.0),
            frequency=(0.62, 0.88),
        )

        parts = family_parts(view)

        self.assertAlmostEqual(float(parts["ped_min"][0]), 0.08, places=6)
        self.assertAlmostEqual(
            float(parts["ped_exact_preferred_min"][0]),
            0.42,
            places=6,
        )
        self.assertAlmostEqual(
            float(parts["ped_exact_preferred_min"][1]),
            0.08,
            places=6,
        )

    def test_effective_jlpt_blends_exact_gap_and_family_only_penalty(self) -> None:
        names = (
            "jlpt_vocab_difficulty",
            "jlpt_vocab_exact_difficulty",
            "jlpt_vocab_exact_known",
            "jlpt_vocab_surface_known",
        )
        view = _component_view(
            names=names,
            rows=[
                {
                    "jlpt_vocab_difficulty": 0.08,
                    "jlpt_vocab_exact_difficulty": 0.42,
                    "jlpt_vocab_exact_known": 1.0,
                    "jlpt_vocab_surface_known": 1.0,
                },
                {
                    "jlpt_vocab_difficulty": 0.08,
                    "jlpt_vocab_surface_known": 1.0,
                },
            ],
            lemmas=("辛い", "外国"),
            readings=("つらい", "とつくに"),
            ranks=(1911.0, np.nan),
            frequency=(0.62, 0.999),
        )

        parts = family_parts(view)
        values = pedagogical_values_for_candidate(
            _candidate(
                jlpt_ped_mode="effective",
                jlpt_exact_blend=0.50,
                jlpt_exact_blend_gate_mode="all_exact_harder",
                jlpt_inherited_penalty=0.14,
                jlpt_inherited_penalty_mode="family_only",
            ),
            parts=parts,
        )

        self.assertAlmostEqual(float(values[0]), 0.25, places=6)
        self.assertAlmostEqual(float(values[1]), 0.22, places=6)

    def test_family_only_same_surface_risk_requires_broad_pedagogical_inheritance(
        self,
    ) -> None:
        names = (
            "jlpt_vocab_difficulty",
            "jlpt_vocab_exact_difficulty",
            "jlpt_vocab_exact_known",
            "jlpt_vocab_surface_known",
            "jmdict_reading_form_marked_risk",
            "rare_non_standard_reading_risk",
        )
        view = _component_view(
            names=names,
            rows=[
                {
                    "jlpt_vocab_difficulty": 0.08,
                    "jlpt_vocab_surface_known": 1.0,
                    "jmdict_reading_form_marked_risk": 1.0,
                    "rare_non_standard_reading_risk": 1.0,
                },
                {
                    "jlpt_vocab_difficulty": 0.08,
                    "jlpt_vocab_exact_difficulty": 0.08,
                    "jlpt_vocab_exact_known": 1.0,
                    "jlpt_vocab_surface_known": 1.0,
                    "jmdict_reading_form_marked_risk": 1.0,
                },
            ],
            lemmas=("外国", "外国"),
            readings=("とつくに", "がいこく"),
            ranks=(np.nan, 413.0),
            frequency=(0.999, 0.55),
        )

        parts = family_parts(view)

        self.assertAlmostEqual(
            float(parts["jlpt_vocab_family_only_known"][0]),
            1.0,
            places=6,
        )
        self.assertAlmostEqual(
            float(parts["same_surface_pedagogical_family_only_risk"][0]),
            1.0,
            places=6,
        )
        self.assertAlmostEqual(
            float(parts["same_surface_pedagogical_family_only_risk"][1]),
            0.0,
            places=6,
        )


if __name__ == "__main__":
    unittest.main()
