from __future__ import annotations

from typing import Any, Callable, Mapping, Sequence

PREFERENCE_MATRIX_TOP_N = 5
PREFERENCE_MATRIX_FOCUS_LEMMAS = ("dog", "elephant", "falcon", "reptile")

SeedFactory = Callable[..., object]
RerankFunction = Callable[..., tuple[Sequence[object], Mapping[str, Any]]]


def build_preference_matrix(
    *,
    rerank_seed_words_for_profile: RerankFunction,
    seed_factory: SeedFactory,
) -> dict[str, Any]:
    seeds = _build_preference_matrix_seed_pool(seed_factory=seed_factory)
    focus_lemmas = PREFERENCE_MATRIX_FOCUS_LEMMAS
    rows = [
        _build_preference_matrix_row(
            name="neutral",
            description="No profile signals.",
            profile_context={},
            focus_lemmas=focus_lemmas,
            seeds=seeds,
            top_n=PREFERENCE_MATRIX_TOP_N,
            rerank_seed_words_for_profile=rerank_seed_words_for_profile,
        ),
        _build_preference_matrix_row(
            name="animals_light",
            description="Light animals preference at mid proficiency.",
            profile_context={
                "topic_weights": {"animals": 0.25},
                "proficiency": {"estimated_value": 0.45},
            },
            focus_lemmas=focus_lemmas,
            seeds=seeds,
            top_n=PREFERENCE_MATRIX_TOP_N,
            rerank_seed_words_for_profile=rerank_seed_words_for_profile,
        ),
        _build_preference_matrix_row(
            name="animals_medium",
            description="Medium animals preference at mid proficiency.",
            profile_context={
                "topic_weights": {"animals": 0.50},
                "proficiency": {"estimated_value": 0.45},
            },
            focus_lemmas=focus_lemmas,
            seeds=seeds,
            top_n=PREFERENCE_MATRIX_TOP_N,
            rerank_seed_words_for_profile=rerank_seed_words_for_profile,
        ),
        _build_preference_matrix_row(
            name="animals_strong",
            description="Strong animals preference at mid proficiency.",
            profile_context={
                "topic_weights": {"animals": 1.00},
                "proficiency": {"estimated_value": 0.45},
            },
            focus_lemmas=focus_lemmas,
            seeds=seeds,
            top_n=PREFERENCE_MATRIX_TOP_N,
            rerank_seed_words_for_profile=rerank_seed_words_for_profile,
        ),
        _build_preference_matrix_row(
            name="proficiency_low",
            description="Low proficiency without topic preference.",
            profile_context={"proficiency": {"estimated_value": 0.20}},
            focus_lemmas=focus_lemmas,
            seeds=seeds,
            top_n=PREFERENCE_MATRIX_TOP_N,
            rerank_seed_words_for_profile=rerank_seed_words_for_profile,
        ),
        _build_preference_matrix_row(
            name="proficiency_mid",
            description="Mid proficiency without topic preference.",
            profile_context={"proficiency": {"estimated_value": 0.45}},
            focus_lemmas=focus_lemmas,
            seeds=seeds,
            top_n=PREFERENCE_MATRIX_TOP_N,
            rerank_seed_words_for_profile=rerank_seed_words_for_profile,
        ),
        _build_preference_matrix_row(
            name="proficiency_high",
            description="High proficiency without topic preference.",
            profile_context={"proficiency": {"estimated_value": 0.75}},
            focus_lemmas=focus_lemmas,
            seeds=seeds,
            top_n=PREFERENCE_MATRIX_TOP_N,
            rerank_seed_words_for_profile=rerank_seed_words_for_profile,
        ),
        _build_preference_matrix_row(
            name="animals_high_proficiency",
            description="Strong animals preference at high proficiency.",
            profile_context={
                "topic_weights": {"animals": 1.00},
                "proficiency": {"estimated_value": 0.75},
            },
            focus_lemmas=focus_lemmas,
            seeds=seeds,
            top_n=PREFERENCE_MATRIX_TOP_N,
            rerank_seed_words_for_profile=rerank_seed_words_for_profile,
        ),
    ]
    row_by_name = {row["name"]: row for row in rows}
    topic_strength_rows = [
        row_by_name["neutral"],
        row_by_name["animals_light"],
        row_by_name["animals_medium"],
        row_by_name["animals_strong"],
    ]
    topic_top_n_counts = [int(row["focus_top_n_count"]) for row in topic_strength_rows]
    topic_probabilities = [
        float(row["focus_first_draw_probability"]) for row in topic_strength_rows
    ]
    low_difficulty = float(row_by_name["proficiency_low"]["average_top_difficulty"])
    high_difficulty = float(row_by_name["proficiency_high"]["average_top_difficulty"])
    high_topic_count = int(row_by_name["animals_high_proficiency"]["focus_top_n_count"])
    high_neutral_topic_count = int(row_by_name["proficiency_high"]["focus_top_n_count"])
    return {
        "top_n": PREFERENCE_MATRIX_TOP_N,
        "focus_lemmas": list(focus_lemmas),
        "seed_pool": {
            "size": len(seeds),
            "neutral_order": [str(getattr(seed, "lemma", "") or "") for seed in seeds],
        },
        "rows": rows,
        "comparisons": {
            "topic_strength_top_n_counts": topic_top_n_counts,
            "topic_strength_first_draw_probabilities": [
                round(value, 6) for value in topic_probabilities
            ],
            "topic_strength_top_n_monotonic": topic_top_n_counts == sorted(topic_top_n_counts),
            "topic_strength_probability_monotonic": topic_probabilities
            == sorted(topic_probabilities),
            "proficiency_average_top_difficulty_delta": round(
                high_difficulty - low_difficulty,
                6,
            ),
            "high_proficiency_topic_top_n_delta": (high_topic_count - high_neutral_topic_count),
        },
    }


def _build_preference_matrix_seed_pool(*, seed_factory: SeedFactory) -> list[object]:
    return [
        seed_factory(lemma="money", admission_weight=0.90, sense_topics=("finance",)),
        seed_factory(lemma="home", admission_weight=0.84, sense_topics=("daily_life",)),
        seed_factory(lemma="food", admission_weight=0.78, sense_topics=("food_cooking",)),
        seed_factory(lemma="travel", admission_weight=0.66, sense_topics=("travel",)),
        seed_factory(lemma="music", admission_weight=0.62, sense_topics=("music_entertainment",)),
        seed_factory(lemma="dog", admission_weight=0.60, sense_topics=("animals", "pets")),
        seed_factory(lemma="elephant", admission_weight=0.52, sense_topics=("animals",)),
        seed_factory(lemma="falcon", admission_weight=0.40, sense_topics=("animals",)),
        seed_factory(lemma="reptile", admission_weight=0.36, sense_topics=("animals",)),
        seed_factory(lemma="thesis", admission_weight=0.38, sense_topics=("academic",)),
        seed_factory(lemma="hypothesis", admission_weight=0.32, sense_topics=("science",)),
        seed_factory(lemma="algorithm", admission_weight=0.28, sense_topics=("technology",)),
    ]


def _build_preference_matrix_row(
    *,
    name: str,
    description: str,
    profile_context: Mapping[str, object],
    focus_lemmas: Sequence[str],
    seeds: Sequence[object],
    top_n: int,
    rerank_seed_words_for_profile: RerankFunction,
) -> dict[str, Any]:
    ranked, diagnostics = rerank_seed_words_for_profile(
        seeds,
        profile_context=profile_context,
        preview_limit=len(seeds),
    )
    focus_set = {str(lemma or "").strip() for lemma in focus_lemmas if str(lemma or "").strip()}
    top_lemmas = [
        str(getattr(seed, "lemma", "") or "").strip()
        for seed in ranked[:top_n]
        if str(getattr(seed, "lemma", "") or "").strip()
    ]
    full_preview = list(diagnostics["ranking_preview"])
    preview_by_lemma = _preview_by_lemma(full_preview)
    focus_mass = sum(
        _safe_float(preview_by_lemma.get(lemma, {}).get("selection_mass")) for lemma in focus_set
    )
    total_mass = sum(_safe_float(entry.get("selection_mass")) for entry in full_preview)
    focus_first_draw_probability = focus_mass / total_mass if total_mass > 0.0 else 0.0
    rank_map = _rank_map(ranked)
    return {
        "name": name,
        "description": description,
        "profile_context": diagnostics["profile_context"],
        "top_n": top_n,
        "top_lemmas": top_lemmas,
        "focus_lemmas": list(focus_lemmas),
        "focus_top_n_count": sum(1 for lemma in top_lemmas if lemma in focus_set),
        "focus_average_rank": _average_rank(rank_map, focus_lemmas),
        "focus_first_draw_probability": round(focus_first_draw_probability, 6),
        "average_top_difficulty": _average_top_difficulty(ranked, top_n),
        "top_preview": [_compact_matrix_preview_entry(entry) for entry in full_preview[:top_n]],
    }


def _rank_map(ranked: Sequence[object]) -> dict[str, int]:
    return {
        str(getattr(seed, "lemma", "") or "").strip(): index + 1
        for index, seed in enumerate(ranked)
        if str(getattr(seed, "lemma", "") or "").strip()
    }


def _average_rank(rank_map: Mapping[str, int], lemmas: Sequence[str]) -> float | None:
    values = [rank_map[lemma] for lemma in lemmas if lemma in rank_map]
    if not values:
        return None
    return round(sum(values) / len(values), 6)


def _candidate_difficulty(seed: object) -> float:
    weight = getattr(seed, "admission_weight", None)
    try:
        return round(max(0.0, min(1.0, 1.0 - float(weight))), 6)
    except (TypeError, ValueError):
        return 0.0


def _average_top_difficulty(ranked: Sequence[object], top_n: int) -> float:
    top_items = list(ranked[:top_n])
    if not top_items:
        return 0.0
    return round(sum(_candidate_difficulty(item) for item in top_items) / len(top_items), 6)


def _preview_by_lemma(preview: Sequence[Mapping[str, Any]]) -> dict[str, Mapping[str, Any]]:
    result: dict[str, Mapping[str, Any]] = {}
    for entry in preview:
        lemma = str(entry.get("lemma") or "").strip()
        if lemma:
            result[lemma] = entry
    return result


def _compact_matrix_preview_entry(entry: Mapping[str, Any]) -> dict[str, object]:
    signals = entry.get("signals") if isinstance(entry.get("signals"), Mapping) else {}
    return {
        "lemma": str(entry.get("lemma") or "").strip(),
        "profile_score": _safe_float(entry.get("profile_score")),
        "selection_mass": _safe_float(entry.get("selection_mass")),
        "readiness_multiplier": _safe_float(
            signals.get("readiness_multiplier") if isinstance(signals, Mapping) else None
        ),
        "topic_affinity": _safe_float(
            signals.get("topic_affinity") if isinstance(signals, Mapping) else None
        ),
    }


def _safe_float(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0
