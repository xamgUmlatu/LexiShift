from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from lexishift_core.srs.admission_features import clamp01, safe_optional_float

LEARNER_DIFFICULTY_MODEL_VERSION = "learner_difficulty_v1"

_EN_JA_EXACT_LEARNER_DIFFICULTY: Mapping[str, tuple[float, str]] = {
    "見る": (0.20, "beginner_core_verb"),
    "行く": (0.22, "beginner_core_verb"),
    "食べる": (0.28, "beginner_core_verb"),
    "飲む": (0.32, "beginner_core_verb"),
    "大きい": (0.28, "beginner_core_adjective"),
    "小さい": (0.28, "beginner_core_adjective"),
    "赤い": (0.32, "beginner_core_color"),
    "青い": (0.32, "beginner_core_color"),
    "水": (0.25, "beginner_core_nature"),
    "火": (0.35, "beginner_core_nature"),
    "山": (0.35, "beginner_core_nature"),
    "川": (0.35, "beginner_core_nature"),
    "犬": (0.20, "beginner_core_animal"),
    "猫": (0.20, "beginner_core_animal"),
    "鳥": (0.30, "beginner_core_animal"),
    "魚": (0.30, "beginner_core_animal"),
    "パン": (0.30, "beginner_core_food"),
    "レタス": (0.30, "beginner_core_food"),
}


@dataclass(frozen=True)
class LearnerDifficultyEstimate:
    value: float
    proxy: str
    sources: Sequence[str]
    frequency_proxy: float

    def to_dict(self) -> dict[str, object]:
        return {
            "version": LEARNER_DIFFICULTY_MODEL_VERSION,
            "value": round(float(self.value), 6),
            "proxy": self.proxy,
            "sources": list(self.sources),
            "frequency_proxy": round(float(self.frequency_proxy), 6),
        }


def estimate_learner_difficulty(
    *,
    language_pair: object,
    lemma: object,
    frequency_proxy: object,
    candidate_state: object = None,
    presentation_mode: object = None,
    problem_class: object = None,
) -> LearnerDifficultyEstimate:
    del candidate_state, presentation_mode, problem_class
    base = clamp01(safe_optional_float(frequency_proxy)) or 0.0
    pair = str(language_pair or "").strip().lower()
    surface = str(lemma or "").strip()
    if pair == "en-ja":
        exact = _EN_JA_EXACT_LEARNER_DIFFICULTY.get(surface)
        if exact is not None:
            value, source = exact
            return LearnerDifficultyEstimate(
                value=clamp01(value) or 0.0,
                proxy=f"{LEARNER_DIFFICULTY_MODEL_VERSION}:en_ja_exact_overlay",
                sources=("frequency_proxy", source),
                frequency_proxy=base,
            )
    return LearnerDifficultyEstimate(
        value=base,
        proxy="1_minus_base_weight",
        sources=("frequency_proxy",),
        frequency_proxy=base,
    )
