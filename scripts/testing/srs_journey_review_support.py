from __future__ import annotations

from pathlib import Path
from typing import Callable, Mapping, Optional, Sequence

from lexishift_core.helper.lp_capabilities import resolve_pair_capability
from lexishift_core.helper.pair_resources import resolve_stopwords_path
from lexishift_core.helper.paths import HelperPaths
from lexishift_core.lexicon.word_package import normalize_word_package
from lexishift_core.srs import SrsStore
from lexishift_core.srs.admission_refresh import AdmissionRefreshPolicy
from lexishift_core.srs.seed import (
    SeedSelectionConfig,
    build_seed_candidates as build_real_seed_candidates,
    seed_to_selector_candidates,
)
from lexishift_core.srs.selector import filter_candidates, rank_candidates
from lexishift_core.srs.signal_queue import SrsSignalEvent


SeedBuilder = Callable[..., Sequence[object]]


def word_package_preview(value: object) -> dict[str, object] | None:
    package = normalize_word_package(value)
    if package is None:
        return None
    source = package.get("source") if isinstance(package.get("source"), Mapping) else {}
    script_forms = (
        dict(package.get("script_forms"))
        if isinstance(package.get("script_forms"), Mapping)
        else None
    )
    preview = {
        "surface": str(package.get("surface") or "").strip(),
        "reading": str(package.get("reading") or "").strip(),
        "language_tag": str(package.get("language_tag") or "").strip(),
        "pos_canonical": str(package.get("pos_canonical") or "").strip() or None,
        "provider": str(source.get("provider") or "").strip() or None,
        "script_forms": script_forms,
    }
    return preview


def build_bootstrap_candidate_audit(
    paths: HelperPaths,
    *,
    pair: str,
    jmdict_path: Optional[Path],
    set_source_db: Path,
    set_top_n: int,
    initial_active_count: int,
    cohort_by_lemma: Mapping[str, str],
) -> dict[str, object]:
    stopwords_path = resolve_stopwords_path(paths, pair=pair)
    seeds = list(
        build_real_seed_candidates(
            frequency_db=set_source_db,
            config=_seed_selection_config(
                pair=pair,
                top_n=set_top_n,
                jmdict_path=jmdict_path,
                stopwords_path=stopwords_path,
            ),
        )
    )
    total_admission_weight = sum(
        _safe_float(getattr(seed, "admission_weight", None)) for seed in seeds
    )
    candidates = []
    for index, seed in enumerate(seeds, start=1):
        admission_weight = _safe_float(getattr(seed, "admission_weight", None))
        candidate = _base_candidate_payload(
            seed,
            seed_rank=index,
            cohort_by_lemma=cohort_by_lemma,
        )
        candidate.update(
            {
                "selected": index <= max(0, int(initial_active_count)),
                "selected_order": index if index <= max(0, int(initial_active_count)) else None,
                "admission_weight_share": _share(admission_weight, total_admission_weight),
            }
        )
        candidates.append(candidate)
    return {
        "candidate_count": len(candidates),
        "admitted_count": max(0, int(initial_active_count)),
        "admission_weight_sum": round(total_admission_weight, 6),
        "stopwords_path": str(stopwords_path) if stopwords_path else None,
        "candidates": candidates,
    }


def build_refresh_candidate_audit(
    paths: HelperPaths,
    *,
    pair: str,
    set_source_db: Path,
    jmdict_path: Optional[Path],
    set_top_n: int,
    feedback_window_size: int,
    allowed_pos: Sequence[str] | None,
    store_before: SrsStore,
    events: Sequence[SrsSignalEvent],
    cohort_by_lemma: Mapping[str, str],
    seed_builder: SeedBuilder,
) -> dict[str, object]:
    stopwords_path = resolve_stopwords_path(paths, pair=pair)
    seeds = list(
        seed_builder(
            frequency_db=set_source_db,
            config=_seed_selection_config(
                pair=pair,
                top_n=set_top_n,
                jmdict_path=jmdict_path,
                stopwords_path=stopwords_path,
            ),
        )
    )
    selector_candidates = seed_to_selector_candidates(seeds)
    existing_lemmas = {
        str(item.lemma or "").strip()
        for item in store_before.items
        if str(item.language_pair or "").strip() == pair and str(item.lemma or "").strip()
    }
    normalized_allowed_pos = _normalize_allowed_pos(allowed_pos)
    policy = AdmissionRefreshPolicy(
        feedback_window_size=max(1, int(feedback_window_size)),
        allowed_pos=normalized_allowed_pos or None,
    )
    eligible = filter_candidates(
        selector_candidates,
        in_s=existing_lemmas,
        allowed_pairs=[pair],
        allowed_pos=normalized_allowed_pos or None,
    )
    ranked = rank_candidates(eligible, config=policy.selector_config)
    score_sum = sum(entry.breakdown.final_score for entry in ranked)
    eligible_lookup = {
        entry.candidate.lemma: {
            "eligible_rank": index,
            "selector_score": round(float(entry.breakdown.final_score), 6),
            "selector_score_share": _share(entry.breakdown.final_score, score_sum),
            "selector_components": {
                key: round(float(value), 6)
                for key, value in dict(entry.breakdown.components).items()
            },
            "selector_penalties": list(entry.breakdown.penalties),
        }
        for index, entry in enumerate(ranked, start=1)
    }
    total_admission_weight = sum(
        _safe_float(getattr(seed, "admission_weight", None)) for seed in seeds
    )
    candidates = []
    for index, seed in enumerate(seeds, start=1):
        lemma = str(getattr(seed, "lemma", "") or "").strip()
        pos_bucket = str(getattr(seed, "pos_bucket", "") or "").strip().lower()
        existing = lemma in existing_lemmas
        entry = _base_candidate_payload(
            seed,
            seed_rank=index,
            cohort_by_lemma=cohort_by_lemma,
        )
        eligible_state = eligible_lookup.get(lemma)
        filtered_reason = None
        if existing:
            filtered_reason = "already_in_store"
        elif normalized_allowed_pos and pos_bucket and pos_bucket not in normalized_allowed_pos:
            filtered_reason = "pos_filtered"
        elif eligible_state is None:
            filtered_reason = "not_ranked"
        entry.update(
            {
                "in_store_before": existing,
                "eligible": eligible_state is not None,
                "filtered_reason": filtered_reason,
                "admission_weight_share": _share(
                    _safe_float(getattr(seed, "admission_weight", None)),
                    total_admission_weight,
                ),
                "selected": False,
                "selected_order": None,
                "eligible_rank": eligible_state.get("eligible_rank") if eligible_state else None,
                "selector_score": eligible_state.get("selector_score") if eligible_state else None,
                "selector_score_share": (
                    eligible_state.get("selector_score_share") if eligible_state else None
                ),
                "selector_components": (
                    eligible_state.get("selector_components") if eligible_state else {}
                ),
                "selector_penalties": (
                    eligible_state.get("selector_penalties") if eligible_state else []
                ),
            }
        )
        candidates.append(entry)
    return {
        "candidate_count": len(candidates),
        "existing_count": len(existing_lemmas),
        "eligible_count": len(ranked),
        "score_sum": round(score_sum, 6),
        "selector_config": {
            "weights": {
                "base_freq": round(float(policy.selector_config.weights.base_freq), 6),
                "topic_bias": round(float(policy.selector_config.weights.topic_bias), 6),
                "user_pref": round(float(policy.selector_config.weights.user_pref), 6),
                "confidence": round(float(policy.selector_config.weights.confidence), 6),
                "difficulty_target": round(
                    float(policy.selector_config.weights.difficulty_target),
                    6,
                ),
            },
            "penalties": {
                "recency_threshold": round(
                    float(policy.selector_config.penalties.recency_threshold),
                    6,
                ),
                "recency_multiplier": round(
                    float(policy.selector_config.penalties.recency_multiplier),
                    6,
                ),
                "mastered_multiplier": round(
                    float(policy.selector_config.penalties.mastered_multiplier),
                    6,
                ),
                "oversubscribed_multiplier": round(
                    float(policy.selector_config.penalties.oversubscribed_multiplier),
                    6,
                ),
            },
            "selection_policy": policy.selector_config.selection_policy,
            "top_n": int(policy.selector_config.top_n),
        },
        "feedback_event_count": sum(
            1 for event in events if str(getattr(event, "pair", "") or "").strip() == pair
        ),
        "allowed_pos": sorted(normalized_allowed_pos),
        "stopwords_path": str(stopwords_path) if stopwords_path else None,
        "existing_lemmas": sorted(existing_lemmas),
        "candidates": candidates,
    }


def apply_selected_lemmas_to_refresh_audit(
    audit: dict[str, object] | None,
    *,
    selected_lemmas: Sequence[str],
) -> dict[str, object] | None:
    if audit is None:
        return None
    selected_order = {
        str(lemma or "").strip(): index
        for index, lemma in enumerate(selected_lemmas, start=1)
        if str(lemma or "").strip()
    }
    candidates = audit.get("candidates")
    if isinstance(candidates, list):
        for entry in candidates:
            if not isinstance(entry, dict):
                continue
            lemma = str(entry.get("lemma") or "").strip()
            order = selected_order.get(lemma)
            entry["selected"] = order is not None
            entry["selected_order"] = order
    audit["selected_lemmas"] = [lemma for lemma in selected_lemmas if str(lemma or "").strip()]
    audit["selected_count"] = len(audit["selected_lemmas"])
    return audit


def _seed_selection_config(
    *,
    pair: str,
    top_n: int,
    jmdict_path: Optional[Path],
    stopwords_path: Optional[Path],
) -> SeedSelectionConfig:
    capability = resolve_pair_capability(pair)
    return SeedSelectionConfig(
        language_pair=pair,
        top_n=max(1, int(top_n)),
        jmdict_path=jmdict_path,
        stopwords_path=stopwords_path,
        require_jmdict=capability.requires_jmdict_for_seed,
    )


def _base_candidate_payload(
    seed: object,
    *,
    seed_rank: int,
    cohort_by_lemma: Mapping[str, str],
) -> dict[str, object]:
    lemma = str(getattr(seed, "lemma", "") or "").strip()
    return {
        "seed_rank": seed_rank,
        "lemma": lemma,
        "cohort": cohort_by_lemma.get(lemma, "frontier"),
        "core_rank": _safe_float(getattr(seed, "core_rank", None)),
        "pmw": _safe_float(getattr(seed, "pmw", None)),
        "pos": str(getattr(seed, "pos", "") or "").strip() or None,
        "pos_bucket": str(getattr(seed, "pos_bucket", "") or "").strip() or None,
        "pos_weight": _safe_float(getattr(seed, "pos_weight", None)),
        "base_weight": _safe_float(getattr(seed, "base_weight", None)),
        "admission_weight": _safe_float(getattr(seed, "admission_weight", None)),
        "word_package_present": word_package_preview(getattr(seed, "word_package", None))
        is not None,
        "word_package": word_package_preview(getattr(seed, "word_package", None)),
    }


def _normalize_allowed_pos(value: Sequence[str] | None) -> set[str]:
    if not value:
        return set()
    return {str(item).strip().lower() for item in value if str(item).strip()}


def _safe_float(value: object) -> float:
    if value is None:
        return 0.0
    try:
        return round(float(value), 6)
    except (TypeError, ValueError):
        return 0.0


def _share(value: float | None, total: float) -> float | None:
    if value is None or total <= 0:
        return None
    return round(float(value) / float(total), 6)
