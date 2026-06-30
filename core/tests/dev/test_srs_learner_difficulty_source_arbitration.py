from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_learner_difficulty_source_arbitration_en_ja import (  # noqa: E402
    ComponentView,
    SourceArbitrationCandidate,
    base_family_rescue_score,
    family_parts,
    jmdict_priority_guard_gate,
    native_values_for_candidate,
    ordinary_protected_score,
    pedagogical_values_for_candidate,
    same_surface_alt_reading_floor_score,
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
    base_family_rescue_margin: float = 0.0,
    base_family_rescue_strength: float = 0.0,
    base_family_rescue_gate_mode: str = "none",
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
        base_family_rescue_margin=base_family_rescue_margin,
        base_family_rescue_strength=base_family_rescue_strength,
        base_family_rescue_gate_mode=base_family_rescue_gate_mode,
    )


class TestSrsLearnerDifficultySourceArbitration(unittest.TestCase):
    def test_base_family_rescue_caps_surface_near_dictionary_base(self) -> None:
        view = _component_view(
            names=(),
            rows=[{}, {}],
            lemmas=("翻る", "翻って"),
            readings=("ひるがえる", "ひるがえって"),
            ranks=(100.0, 1000.0),
            frequency=(0.45, 0.85),
        )
        candidate = _candidate(
            base_family_rescue_margin=0.06,
            base_family_rescue_strength=1.0,
            base_family_rescue_gate_mode="score_gap",
        )

        with patch(
            "srs_learner_difficulty_source_arbitration_en_ja._base_family_dictionary_form",
            side_effect=lambda surface: "翻る" if surface == "翻って" else None,
        ):
            adjusted = base_family_rescue_score(
                candidate,
                np.asarray((0.45, 0.85), dtype=np.float32),
                view=view,
            )

        self.assertAlmostEqual(float(adjusted[0]), 0.45, places=6)
        self.assertAlmostEqual(float(adjusted[1]), 0.51, places=6)

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

    def test_family_parts_prefers_effective_jlpt_exact_when_available(self) -> None:
        names = (
            "jlpt_vocab_difficulty",
            "jlpt_vocab_exact_difficulty",
            "jlpt_vocab_exact_known",
            "jlpt_vocab_effective_exact_difficulty",
            "jlpt_vocab_effective_exact_known",
            "jlpt_vocab_normalized_exact_known",
            "jlpt_vocab_surface_known",
        )
        view = _component_view(
            names=names,
            rows=[
                {
                    "jlpt_vocab_difficulty": 0.08,
                    "jlpt_vocab_exact_known": 0.0,
                    "jlpt_vocab_effective_exact_difficulty": 0.22,
                    "jlpt_vocab_effective_exact_known": 1.0,
                    "jlpt_vocab_normalized_exact_known": 1.0,
                    "jlpt_vocab_surface_known": 1.0,
                }
            ],
            lemmas=("矢張り",),
            readings=("やはり",),
            ranks=(410.0,),
            frequency=(0.30,),
        )

        parts = family_parts(view)

        self.assertAlmostEqual(
            float(parts["ped_exact_preferred_min"][0]),
            0.22,
            places=6,
        )
        self.assertAlmostEqual(float(parts["jlpt_vocab_exact_known"][0]), 1.0, places=6)
        self.assertAlmostEqual(float(parts["jlpt_vocab_raw_exact_known"][0]), 0.0, places=6)
        self.assertAlmostEqual(float(parts["jlpt_vocab_family_only_known"][0]), 0.0, places=6)

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

    def test_gradient_same_surface_floor_can_reproduce_exact_protected_hard_floor(
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
        raw = np.zeros(2, dtype=np.float32)
        hard_candidate = replace(
            _candidate(),
            same_surface_secondary_floor=0.42,
            same_surface_secondary_floor_mode=(
                "pedagogical_family_only_rare_pollution_unprotected_exact"
            ),
        )
        gradient_candidate = replace(
            _candidate(),
            same_surface_gradient_high_floor=0.42,
            same_surface_gradient_mode="exact_protected_evidence",
            same_surface_gradient_curve="linear",
            same_surface_gradient_commonness_cap=0.0,
            same_surface_gradient_lesson_rescue=0.0,
            same_surface_gradient_marked_boost=0.0,
        )

        hard = same_surface_alt_reading_floor_score(hard_candidate, raw, parts=parts)
        gradient = same_surface_alt_reading_floor_score(gradient_candidate, raw, parts=parts)

        np.testing.assert_allclose(gradient, hard, atol=1e-6)

    def test_jmdict_priority_guard_uses_pair_priority_leak_risk(self) -> None:
        names = (
            "jmdict_priority",
            "jmdict_pair_priority_leak_risk",
        )
        view = _component_view(
            names=names,
            rows=[
                {
                    "jmdict_priority": 0.0,
                    "jmdict_pair_priority_leak_risk": 1.0,
                }
            ],
            lemmas=("而して",),
            readings=("しこうして",),
            ranks=(np.nan,),
            frequency=(0.95,),
        )
        parts = family_parts(view)
        candidate = replace(
            _candidate(),
            jmdict_priority_guard_mode="marked",
            jmdict_priority_guard_strength=1.0,
            jmdict_priority_guard_curve="linear",
            jmdict_priority_guard_ped_rescue=0.0,
        )

        gate = jmdict_priority_guard_gate(candidate, parts=parts)

        self.assertAlmostEqual(float(gate[0]), 1.0, places=6)

    def test_pair_safe_priority_source_replaces_native_jmdict_priority(self) -> None:
        names = (
            "jmdict_priority",
            "jmdict_pair_safe_priority",
            "tubelex_frequency",
        )
        view = _component_view(
            names=names,
            rows=[
                {
                    "jmdict_priority": 0.0,
                    "jmdict_pair_safe_priority": 1.0,
                    "tubelex_frequency": 0.6,
                }
            ],
            lemmas=("而して",),
            readings=("しこうして",),
            ranks=(np.nan,),
            frequency=(0.6,),
        )
        parts = family_parts(view)

        legacy = native_values_for_candidate(_candidate(), parts=parts)
        pair_safe = native_values_for_candidate(
            replace(
                _candidate(),
                jmdict_priority_source="pair_safe",
            ),
            parts=parts,
        )
        raise_half = native_values_for_candidate(
            replace(
                _candidate(),
                jmdict_priority_source="pair_safe_raise",
                jmdict_pair_safe_blend=0.5,
            ),
            parts=parts,
        )

        self.assertAlmostEqual(float(legacy[0]), 0.4, places=6)
        self.assertAlmostEqual(float(raise_half[0]), 0.5666667, places=6)
        self.assertAlmostEqual(float(pair_safe[0]), 0.7333333, places=6)

    def test_pair_safe_priority_source_recomputes_ordinary_gate(self) -> None:
        names = (
            "jmdict_priority",
            "jmdict_pair_safe_priority",
        )
        view = _component_view(
            names=names,
            rows=[
                {
                    "jmdict_priority": 0.0,
                    "jmdict_pair_safe_priority": 1.0,
                }
            ],
            lemmas=("而して",),
            readings=("しこうして",),
            ranks=(np.nan,),
            frequency=(0.95,),
        )
        parts = family_parts(view)
        raw = np.asarray([0.9], dtype=np.float32)
        legacy_candidate = replace(
            _candidate(),
            ordinary_gate_mode="priority",
        )
        pair_safe_candidate = replace(
            legacy_candidate,
            jmdict_priority_source="pair_safe",
        )

        legacy = ordinary_protected_score(legacy_candidate, raw, parts=parts)
        pair_safe = ordinary_protected_score(pair_safe_candidate, raw, parts=parts)

        self.assertAlmostEqual(float(legacy[0]), 0.58, places=6)
        self.assertAlmostEqual(float(pair_safe[0]), 0.9, places=6)

    def test_pair_leak_ped_trust_floor_only_raises_family_only_pair_leak(
        self,
    ) -> None:
        names = (
            "jlpt_vocab_difficulty",
            "jlpt_vocab_exact_difficulty",
            "jlpt_vocab_exact_known",
            "jlpt_vocab_surface_known",
            "jmdict_pair_priority_leak_risk",
            "jmdict_pair_missing_reading_risk",
            "jmdict_priority",
            "jmdict_pair_safe_priority",
            "tubelex_frequency",
        )
        view = _component_view(
            names=names,
            rows=[
                {
                    "jlpt_vocab_difficulty": 0.08,
                    "jlpt_vocab_surface_known": 1.0,
                    "jmdict_pair_priority_leak_risk": 1.0,
                    "jmdict_pair_missing_reading_risk": 1.0,
                    "jmdict_priority": 0.0,
                    "jmdict_pair_safe_priority": 1.0,
                    "tubelex_frequency": 0.8,
                },
                {
                    "jlpt_vocab_difficulty": 0.08,
                    "jlpt_vocab_exact_difficulty": 0.08,
                    "jlpt_vocab_exact_known": 1.0,
                    "jlpt_vocab_surface_known": 1.0,
                    "jmdict_priority": 0.0,
                    "jmdict_pair_safe_priority": 0.0,
                    "tubelex_frequency": 0.2,
                },
            ],
            lemmas=("外国", "外国"),
            readings=("とつくに", "がいこく"),
            ranks=(np.nan, 413.0),
            frequency=(1.0, 0.55),
        )
        parts = family_parts(view)
        candidate = replace(
            _candidate(),
            pair_leak_ped_gate_mode="pair_missing_family_only",
            pair_leak_ped_adjustment_mode="floor",
            pair_leak_ped_strength=1.0,
            pair_leak_ped_floor=0.42,
            pair_leak_ped_curve="linear",
        )

        values = pedagogical_values_for_candidate(candidate, parts=parts)

        self.assertAlmostEqual(float(values[0]), 0.42, places=6)
        self.assertAlmostEqual(float(values[1]), 0.08, places=6)

    def test_pair_leak_ped_trust_can_raise_toward_pair_safe_native_target(
        self,
    ) -> None:
        names = (
            "jlpt_vocab_difficulty",
            "jlpt_vocab_exact_known",
            "jlpt_vocab_surface_known",
            "jmdict_pair_priority_leak_risk",
            "jmdict_pair_missing_reading_risk",
            "jmdict_priority",
            "jmdict_pair_safe_priority",
            "tubelex_frequency",
        )
        view = _component_view(
            names=names,
            rows=[
                {
                    "jlpt_vocab_difficulty": 0.08,
                    "jlpt_vocab_surface_known": 1.0,
                    "jmdict_pair_priority_leak_risk": 1.0,
                    "jmdict_pair_missing_reading_risk": 1.0,
                    "jmdict_priority": 0.0,
                    "jmdict_pair_safe_priority": 1.0,
                    "tubelex_frequency": 0.8,
                }
            ],
            lemmas=("外国",),
            readings=("とつくに",),
            ranks=(np.nan,),
            frequency=(1.0,),
        )
        parts = family_parts(view)
        candidate = replace(
            _candidate(),
            pair_leak_ped_gate_mode="pair_leak_family_only",
            pair_leak_ped_adjustment_mode="raise_toward_pair_native",
            pair_leak_ped_strength=0.5,
            pair_leak_ped_curve="linear",
        )

        values = pedagogical_values_for_candidate(candidate, parts=parts)

        self.assertAlmostEqual(float(values[0]), 0.5066667, places=6)

    def test_ordinary_cap_can_use_pair_safe_priority_gate(self) -> None:
        names = (
            "jmdict_priority",
            "jmdict_pair_safe_priority",
        )
        view = _component_view(
            names=names,
            rows=[
                {
                    "jmdict_priority": 0.0,
                    "jmdict_pair_safe_priority": 1.0,
                }
            ],
            lemmas=("而して",),
            readings=("しこうして",),
            ranks=(np.nan,),
            frequency=(0.95,),
        )
        parts = family_parts(view)
        raw = np.asarray([0.9], dtype=np.float32)
        legacy_candidate = replace(
            _candidate(),
            ordinary_gate_mode="priority",
            ordinary_cap=0.58,
            ordinary_cap_mode="hard",
        )
        pair_safe_candidate = replace(
            legacy_candidate,
            ordinary_gate_mode="pair_safe_priority",
        )

        legacy = ordinary_protected_score(legacy_candidate, raw, parts=parts)
        pair_safe = ordinary_protected_score(pair_safe_candidate, raw, parts=parts)

        self.assertAlmostEqual(float(legacy[0]), 0.58, places=6)
        self.assertAlmostEqual(float(pair_safe[0]), 0.9, places=6)

    def test_ordinary_cap_pair_leak_exception_can_veto_false_cap(self) -> None:
        names = (
            "jmdict_priority",
            "jmdict_pair_priority_leak_risk",
        )
        view = _component_view(
            names=names,
            rows=[
                {
                    "jmdict_priority": 0.0,
                    "jmdict_pair_priority_leak_risk": 1.0,
                }
            ],
            lemmas=("而して",),
            readings=("しこうして",),
            ranks=(np.nan,),
            frequency=(0.95,),
        )
        parts = family_parts(view)
        raw = np.asarray([0.9], dtype=np.float32)
        current_candidate = replace(
            _candidate(),
            ordinary_gate_mode="priority",
            ordinary_cap=0.58,
            ordinary_cap_mode="hard",
            ordinary_exception_mode="current",
        )
        pair_leak_candidate = replace(
            current_candidate,
            ordinary_exception_mode="current_pair_leak",
        )

        current = ordinary_protected_score(current_candidate, raw, parts=parts)
        pair_leak = ordinary_protected_score(pair_leak_candidate, raw, parts=parts)

        self.assertAlmostEqual(float(current[0]), 0.58, places=6)
        self.assertAlmostEqual(float(pair_leak[0]), 0.9, places=6)

    def test_ordinary_cap_gate_curve_controls_cap_strength(self) -> None:
        names = ("frequency_ease",)
        view = _component_view(
            names=names,
            rows=[
                {
                    "frequency_ease": 0.5,
                }
            ],
            lemmas=("ほどほど",),
            readings=("ほどほど",),
            ranks=(1000.0,),
            frequency=(0.50,),
        )
        parts = family_parts(view)
        raw = np.asarray([0.9], dtype=np.float32)
        linear_candidate = replace(
            _candidate(),
            ordinary_gate_mode="frequency",
            ordinary_cap=0.50,
            ordinary_cap_mode="hard",
            ordinary_gate_curve="linear",
        )
        square_candidate = replace(
            linear_candidate,
            ordinary_gate_curve="square",
        )

        linear = ordinary_protected_score(linear_candidate, raw, parts=parts)
        square = ordinary_protected_score(square_candidate, raw, parts=parts)

        self.assertAlmostEqual(float(linear[0]), 0.75, places=6)
        self.assertAlmostEqual(float(square[0]), 0.875, places=6)


if __name__ == "__main__":
    unittest.main()
