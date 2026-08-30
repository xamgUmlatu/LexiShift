from __future__ import annotations

from typing import Mapping, Protocol, Sequence, cast

from lexishift_core.srs.candidate_identity import candidate_identity_key_from_seed
from lexishift_core.srs.profile_bootstrap import ProfileBootstrapScoredEntry
from lexishift_core.srs.selector import (
    SelectorCandidate,
    SelectorConfig,
    SelectorWeights,
)
from lexishift_core.srs.store_ops import build_item_id


class SeedWordLike(Protocol):
    lemma: str
    language_pair: str


def safe_optional_float(value: object) -> float | None:
    if value is None:
        return None
    if isinstance(value, (float, int)):
        return float(value)
    if isinstance(value, (str, bytes, bytearray)):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def build_weight_preview_entry(selected: object) -> Mapping[str, object]:
    base_weight = safe_optional_float(getattr(selected, "base_weight", None))
    pos_weight = safe_optional_float(getattr(selected, "pos_weight", None))
    admission_weight = safe_optional_float(getattr(selected, "admission_weight", None))
    return {
        "candidate_identity_key": candidate_identity_key_from_seed(selected),
        "lemma": str(getattr(selected, "lemma", "")).strip(),
        "pos": getattr(selected, "pos", None),
        "pos_bucket": str(getattr(selected, "pos_bucket", "")),
        "base_weight": round(base_weight, 6) if base_weight is not None else None,
        "pos_weight": round(pos_weight, 6) if pos_weight is not None else None,
        "admission_weight": round(admission_weight, 6) if admission_weight is not None else None,
    }


def dedupe_seed_words(selected_words: Sequence[object]) -> list[SeedWordLike]:
    selected_by_id: dict[str, SeedWordLike] = {}
    order_by_id: dict[str, int] = {}
    for selected in selected_words:
        seed = as_seed_word_like(selected)
        if seed is None:
            continue
        item_id = build_item_id(seed.language_pair, seed.lemma)
        order_by_id.setdefault(item_id, len(order_by_id))
        existing = selected_by_id.get(item_id)
        if existing is None or _seed_choice_key(seed) > _seed_choice_key(existing):
            selected_by_id[item_id] = seed
    return [
        selected_by_id[item_id]
        for item_id, _order in sorted(order_by_id.items(), key=lambda item: item[1])
    ]


def resolve_seed_admission_suitability(seed: object) -> float:
    value = safe_optional_float(getattr(seed, "admission_suitability", None))
    if value is not None:
        return value
    metadata = getattr(seed, "metadata", None)
    if isinstance(metadata, Mapping):
        value = safe_optional_float(metadata.get("admission_suitability"))
        if value is not None:
            return value
    return 1.0


def coerce_seed_words(selected_words: object) -> list[SeedWordLike]:
    if not isinstance(selected_words, Sequence) or isinstance(selected_words, (str, bytes)):
        return []
    coerced: list[SeedWordLike] = []
    for selected in selected_words:
        seed = as_seed_word_like(selected)
        if seed is not None:
            coerced.append(seed)
    return coerced


def dedupe_profile_bootstrap_entries(
    scored_entries: Sequence[ProfileBootstrapScoredEntry],
) -> list[ProfileBootstrapScoredEntry]:
    entry_by_id: dict[str, ProfileBootstrapScoredEntry] = {}
    order_by_id: dict[str, int] = {}
    for entry in scored_entries:
        seed = getattr(entry, "seed", None)
        seed_like = as_seed_word_like(seed)
        if seed_like is None:
            continue
        item_id = build_item_id(seed_like.language_pair, seed_like.lemma)
        order_by_id.setdefault(item_id, len(order_by_id))
        existing = entry_by_id.get(item_id)
        if existing is None or _profile_entry_choice_key(entry) > _profile_entry_choice_key(
            existing
        ):
            entry_by_id[item_id] = entry
    return [
        entry_by_id[item_id]
        for item_id, _order in sorted(order_by_id.items(), key=lambda item: item[1])
    ]


def seed_to_bootstrap_selector_candidates(seeds: Sequence[object]) -> list[SelectorCandidate]:
    candidates: list[SelectorCandidate] = []
    for seed in seeds:
        admission_weight = (
            safe_optional_float(getattr(seed, "admission_weight", None))
            or safe_optional_float(getattr(seed, "base_weight", None))
            or 1.0
        )
        candidates.append(
            SelectorCandidate(
                lemma=str(getattr(seed, "lemma", "") or "").strip(),
                language_pair=str(getattr(seed, "language_pair", "") or "").strip(),
                base_freq=admission_weight,
                admission_suitability=resolve_seed_admission_suitability(seed),
                confidence=0.0,
                pos=str(getattr(seed, "pos_bucket", "") or "").strip() or None,
                metadata={
                    "candidate_identity_key": candidate_identity_key_from_seed(seed),
                    "base_weight": safe_optional_float(getattr(seed, "base_weight", None)),
                    "admission_weight": admission_weight,
                    "pos_bucket": str(getattr(seed, "pos_bucket", "")).strip() or None,
                },
            )
        )
    return candidates


def build_frequency_bootstrap_selector_config(
    *,
    selection_policy: str,
    selection_count: int,
) -> SelectorConfig:
    return SelectorConfig(
        weights=SelectorWeights(
            base_freq=1.0,
            topic_bias=0.0,
            scarcity_bonus=0.0,
            user_pref=0.0,
            confidence=0.0,
            difficulty_target=0.0,
        ),
        selection_policy=selection_policy,
        top_n=max(0, int(selection_count)),
    )


def build_profile_bootstrap_selector_config(
    *,
    selection_policy: str,
    selection_count: int,
) -> SelectorConfig:
    return SelectorConfig(
        selection_policy=selection_policy,
        top_n=max(0, int(selection_count)),
    )


def _seed_choice_key(seed: object) -> tuple[float, float, float, float]:
    rank = safe_optional_float(getattr(seed, "core_rank", None))
    rank_score = -rank if rank is not None else float("-inf")
    return (
        resolve_seed_admission_suitability(seed),
        safe_optional_float(getattr(seed, "admission_weight", None)) or 0.0,
        safe_optional_float(getattr(seed, "base_weight", None)) or 0.0,
        rank_score,
    )


def _profile_entry_choice_key(entry: ProfileBootstrapScoredEntry) -> tuple[float, float, float]:
    return (
        float(entry.scored_candidate.breakdown.final_score),
        float(entry.signal_pack.admission_suitability),
        float(entry.traits.coverage_gain),
    )


def as_seed_word_like(value: object) -> SeedWordLike | None:
    if not hasattr(value, "lemma") or not hasattr(value, "language_pair"):
        return None
    return cast(SeedWordLike, value)
