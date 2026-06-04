from __future__ import annotations

from typing import Callable, Mapping, Sequence

from lexishift_core.resources.dict_loaders import TranslationGlossRecord
from lexishift_core.rulegen.utils import sanitize_dictionary_gloss


def build_target_trigger_family_terms(
    benchmark_targets: Sequence[object],
) -> dict[str, tuple[str, ...]]:
    trigger_families: dict[str, tuple[str, ...]] = {}
    for benchmark_target in benchmark_targets:
        target = str(getattr(benchmark_target, "target", "") or "").strip()
        if not target:
            continue
        terms = _normalize_string_list(getattr(benchmark_target, "reviewed_triggers", ()))
        if terms:
            trigger_families[target] = tuple(terms)
    return trigger_families


def build_target_forward_neighborhood_terms(
    *,
    forward_records_by_target: Mapping[str, Sequence[TranslationGlossRecord]],
    collect_records: Callable[[Sequence[TranslationGlossRecord]], Sequence[TranslationGlossRecord]],
) -> dict[str, tuple[str, ...]]:
    neighborhoods: dict[str, tuple[str, ...]] = {}
    for target, raw_records in forward_records_by_target.items():
        normalized_target = str(target or "").strip()
        if not normalized_target:
            continue
        terms: list[str] = []
        for record in collect_records(raw_records):
            term = sanitize_dictionary_gloss(record.translation)
            if term and term not in terms:
                terms.append(term)
        if terms:
            neighborhoods[normalized_target] = tuple(terms)
    return neighborhoods


def attach_target_forward_neighborhood_terms(
    candidate: dict[str, object],
    *,
    neighborhoods_by_target: Mapping[str, Sequence[str]],
) -> None:
    target = str(candidate.get("target") or "").strip()
    terms = neighborhoods_by_target.get(target, ())
    if terms:
        candidate["forward_neighborhood_terms"] = list(terms)


def attach_target_trigger_family_terms(
    candidate: dict[str, object],
    *,
    trigger_families_by_target: Mapping[str, Sequence[str]],
) -> None:
    target = str(candidate.get("target") or "").strip()
    terms = trigger_families_by_target.get(target, ())
    if terms:
        candidate["target_trigger_family_terms"] = list(terms)


def build_forward_neighborhood_overlap_details(
    *,
    candidate: Mapping[str, object],
    active_candidates: Sequence[Mapping[str, object]],
    active_profile_forward_neighborhood_terms: Sequence[str] = (),
) -> dict[str, object]:
    active_terms = _normalize_string_list(
        *(
            active_candidate.get("forward_neighborhood_terms")
            for active_candidate in active_candidates
        ),
    )
    if not active_terms:
        active_terms = _normalize_string_list(active_profile_forward_neighborhood_terms)
    candidate_terms = _normalize_string_list(candidate.get("forward_neighborhood_terms"))
    if not active_terms or not candidate_terms:
        return {
            "forward_neighborhood_overlap_present": False,
            "forward_neighborhood_overlap_score": 0.0,
            "forward_neighborhood_overlap_terms": [],
        }
    active_set = set(active_terms)
    candidate_set = set(candidate_terms)
    shared_terms = sorted(active_set & candidate_set)
    union_terms = active_set | candidate_set
    return {
        "forward_neighborhood_overlap_present": bool(shared_terms),
        "forward_neighborhood_overlap_score": (
            float(len(shared_terms)) / float(len(union_terms)) if union_terms else 0.0
        ),
        "forward_neighborhood_overlap_terms": shared_terms[:5],
    }


def build_trigger_family_reentry_details(
    *,
    candidate: Mapping[str, object],
    active_candidates: Sequence[Mapping[str, object]],
    active_trigger: str = "",
    active_profile_forward_neighborhood_terms: Sequence[str] = (),
    active_profile_trigger_family_terms: Sequence[str] = (),
) -> dict[str, object]:
    active_terms = _normalize_string_list(
        *(
            active_candidate.get("target_trigger_family_terms")
            for active_candidate in active_candidates
        ),
        *(
            active_candidate.get("forward_neighborhood_terms")
            for active_candidate in active_candidates
        ),
    )
    if not active_terms:
        active_terms = _normalize_string_list(
            active_profile_trigger_family_terms,
            active_profile_forward_neighborhood_terms,
        )
    candidate_terms = _normalize_string_list(
        candidate.get("target_trigger_family_terms"),
        candidate.get("forward_neighborhood_terms"),
    )
    excluded_trigger = _normalize_string_list(active_trigger)
    if excluded_trigger:
        excluded = set(excluded_trigger)
        active_terms = [term for term in active_terms if term not in excluded]
        candidate_terms = [term for term in candidate_terms if term not in excluded]
    if not active_terms or not candidate_terms:
        return {
            "trigger_family_reentry_present": False,
            "trigger_family_reentry_score": 0.0,
            "trigger_family_reentry_terms": [],
            "trigger_family_reentry_shared_alias_count": 0,
        }
    active_set = set(active_terms)
    candidate_set = set(candidate_terms)
    shared_terms = sorted(active_set & candidate_set)
    union_terms = active_set | candidate_set
    return {
        "trigger_family_reentry_present": bool(shared_terms),
        "trigger_family_reentry_score": (
            float(len(shared_terms)) / float(len(union_terms)) if union_terms else 0.0
        ),
        "trigger_family_reentry_terms": shared_terms[:5],
        "trigger_family_reentry_shared_alias_count": len(shared_terms),
    }


def _normalize_string_list(*values: object) -> list[str]:
    normalized: list[str] = []
    for value in values:
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
            for item in value:
                text = str(item or "").strip()
                if text and text not in normalized:
                    normalized.append(text)
        else:
            text = str(value or "").strip()
            if text and text not in normalized:
                normalized.append(text)
    return normalized
