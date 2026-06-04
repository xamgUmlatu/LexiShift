from __future__ import annotations

from pathlib import Path
from typing import Mapping, Sequence

from semantic_veto_difficulty_stratification_common import (
    RANK_BINS,
    _has_value,
    _optional_float,
    _optional_int,
    _round4,
    _string_list,
)
from semantic_veto_difficulty_stratification_frequency import (
    FrequencyLookup,
    _normalize_lemma_key,
    _source_zipf_band,
    _source_zipf_frequency,
    _source_zipf_match_kind,
)
from semantic_veto_product_quality_en_es import (
    _as_mapping,
    _load_json,
    _repo_path,
    _resolve_repo_path,
)
from semantic_veto_veto_only_probe_en_es import _mapping_rows


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LLM_SCORING = (
    PROJECT_ROOT / "docs" / "test_outputs" / "semantic_veto_llm_pilot_scoring_en_es_latest.json"
)


def _default_report_id(path: Path | None, index: int) -> str:
    if path is None:
        return f"inline_report_{index}"
    return path.stem


def _policy_case_rows(
    *,
    policy_payload: Mapping[str, object],
    family_index: Mapping[str, object],
    source_frequency: FrequencyLookup,
    target_frequency: FrequencyLookup,
    source_zipf_by_trigger: Mapping[str, float] | None,
    source_zipf_status: str,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    rows: list[dict[str, object]] = []
    sources: list[dict[str, object]] = []
    for lane in _mapping_rows(policy_payload.get("lanes")):
        lane_id = str(lane.get("lane_id") or "").strip()
        lane_type = str(lane.get("lane_type") or "").strip()
        for index, source in enumerate(_mapping_rows(lane.get("reports"))):
            payload, path = _source_report(source)
            source_id = str(source.get("source_id") or _default_report_id(path, index))
            suite_id = str(source.get("suite_id") or source_id)
            case_rows = _case_rows(payload)
            for row in case_rows:
                rows.append(
                    _normalize_case_trace(
                        row=row,
                        lane_id=lane_id,
                        lane_type=lane_type,
                        source_id=source_id,
                        suite_id=suite_id,
                        report_path=path,
                        family_index=family_index,
                        source_frequency=source_frequency,
                        target_frequency=target_frequency,
                        source_zipf_by_trigger=source_zipf_by_trigger,
                        source_zipf_status=source_zipf_status,
                    )
                )
            sources.append(
                {
                    "lane_id": lane_id,
                    "source_id": source_id,
                    "suite_id": suite_id,
                    "path": _repo_path(path),
                    "status": str(payload.get("status") or ""),
                    "decision": str(payload.get("decision") or ""),
                    "case_count": len(case_rows),
                }
            )
    return rows, sources


def _llm_case_rows(
    *,
    llm_scoring_payload: Mapping[str, object],
    family_index: Mapping[str, object],
    source_frequency: FrequencyLookup,
    target_frequency: FrequencyLookup,
    source_zipf_by_trigger: Mapping[str, float] | None,
    source_zipf_status: str,
) -> list[dict[str, object]]:
    rows = []
    for row in _mapping_rows(llm_scoring_payload.get("case_results")):
        split = str(row.get("split") or "unknown").strip() or "unknown"
        rows.append(
            _normalize_case_trace(
                row=row,
                lane_id="semantic_veto_llm_pilot_en_es_v1",
                lane_type="llm_pilot",
                source_id="llm_pilot_scoring",
                suite_id=f"llm_{split}",
                report_path=DEFAULT_LLM_SCORING,
                family_index=family_index,
                source_frequency=source_frequency,
                target_frequency=target_frequency,
                source_zipf_by_trigger=source_zipf_by_trigger,
                source_zipf_status=source_zipf_status,
            )
        )
    return rows


def _normalize_case_trace(
    *,
    row: Mapping[str, object],
    lane_id: str,
    lane_type: str,
    source_id: str,
    suite_id: str,
    report_path: Path | None,
    family_index: Mapping[str, object],
    source_frequency: FrequencyLookup,
    target_frequency: FrequencyLookup,
    source_zipf_by_trigger: Mapping[str, float] | None,
    source_zipf_status: str,
) -> dict[str, object]:
    family_id = str(row.get("family_id") or row.get("original_family_id") or "").strip()
    trigger = str(row.get("trigger") or row.get("source_phrase") or "").strip()
    metadata = _metadata_for_row(row=row, family_id=family_id, trigger=trigger, index=family_index)
    if not trigger:
        trigger = str(metadata.get("trigger") or "").strip()
    target = _target_lemma(row=row, metadata=metadata, family_id=family_id)
    source_match = source_frequency.lookup(trigger)
    source_zipf = _source_zipf_frequency(
        trigger=trigger,
        source_zipf_by_trigger=source_zipf_by_trigger,
        source_zipf_status=source_zipf_status,
    )
    target_match = target_frequency.lookup(target)
    gold = _normalize_decision(row.get("gold_decision"))
    predicted = _normalize_decision(row.get("predicted_decision"))
    product_outcome = _product_outcome(gold=gold, predicted=predicted)
    active = _optional_float(row.get("active_score"))
    shadow = _optional_float(row.get("strongest_shadow_score"))
    phrase = _optional_float(row.get("phrase_control_score"))
    shadow_lead = _optional_float(row.get("shadow_lead"))
    if shadow_lead is None and active is not None and shadow is not None:
        shadow_lead = _round4(shadow - active)
    phrase_lead = _optional_float(row.get("phrase_lead_to_best"))
    if phrase_lead is None and phrase is not None and active is not None:
        phrase_lead = _round4(phrase - max(active, shadow or 0.0))
    wordnet_sense_count = _optional_int(metadata.get("wordnet_sense_count"))
    translation_candidate_count = _optional_int(metadata.get("translation_candidate_count"))
    source_rank = source_match.rank
    target_rank = target_match.rank
    trace = {
        "case_id": str(row.get("case_id") or row.get("original_case_id") or "").strip(),
        "lane_id": lane_id,
        "lane_type": lane_type,
        "source_id": source_id,
        "suite_id": suite_id,
        "report_path": _repo_path(report_path),
        "split": str(row.get("split") or "").strip(),
        "context_source": str(row.get("context_source") or "").strip(),
        "review_state": str(row.get("review_state") or "").strip(),
        "source_frame_id": str(row.get("source_frame_id") or "").strip(),
        "frame_row_id": str(row.get("frame_row_id") or "").strip(),
        "selected_for_locked_eval": bool(row.get("selected_for_locked_eval")),
        "family_id": family_id,
        "pilot_family_id": str(row.get("pilot_family_id") or "").strip(),
        "trigger": trigger,
        "target_lemma": target,
        "sentence": str(row.get("sentence") or "").strip(),
        "gold_decision": gold,
        "predicted_decision": predicted,
        "product_outcome": product_outcome,
        "error_type": _error_type(gold=gold, predicted=predicted),
        "gold_winner_type": str(row.get("gold_winner_type") or "").strip(),
        "predicted_winner_type": str(row.get("predicted_winner_type") or "").strip(),
        "active_score": active,
        "strongest_shadow_score": shadow,
        "phrase_control_score": phrase,
        "shadow_lead": shadow_lead,
        "phrase_lead_to_best": phrase_lead,
        "shadow_lead_bin": _signed_margin_bin(shadow_lead, positive_label="shadow"),
        "phrase_lead_bin": _signed_margin_bin(phrase_lead, positive_label="phrase"),
        "phrase_preemption_hit": bool(row.get("phrase_preemption_hit")),
        "veto_reason": str(row.get("veto_reason") or row.get("phrase_reason_code") or "").strip(),
        "source_trigger_rank_en": source_rank,
        "source_trigger_frequency_en": source_match.frequency,
        "source_trigger_rank_bin_en": _rank_bin(source_rank),
        "source_trigger_frequency_match_kind": source_match.match_kind,
        "source_trigger_frequency_matched_lemma": source_match.matched_lemma,
        "source_zipf_frequency_en": source_zipf,
        "source_zipf_band_en": _source_zipf_band(source_zipf),
        "source_zipf_match_kind": _source_zipf_match_kind(
            source_zipf=source_zipf,
            source_zipf_status=source_zipf_status,
        ),
        "target_lemma_rank_es": target_rank,
        "target_lemma_frequency_es": target_match.frequency,
        "target_lemma_rank_bin_es": _rank_bin(target_rank),
        "target_lemma_frequency_match_kind": target_match.match_kind,
        "target_lemma_frequency_matched_lemma": target_match.matched_lemma,
        "target_translation_rank": _optional_int(metadata.get("target_translation_rank")),
        "declared_frequency_band": str(metadata.get("declared_frequency_band") or "missing"),
        "declared_ambiguity_class": str(metadata.get("declared_ambiguity_class") or "missing"),
        "source_complexity_band": str(metadata.get("source_complexity_band") or "missing"),
        "wordnet_sense_count": wordnet_sense_count,
        "wordnet_sense_count_bin": _count_bin(wordnet_sense_count),
        "wordnet_pos_count": _optional_int(metadata.get("wordnet_pos_count")),
        "translation_candidate_count": translation_candidate_count,
        "translation_candidate_count_bin": _count_bin(translation_candidate_count),
        "active_evidence_count": _optional_int(metadata.get("active_evidence_count")),
        "shadow_evidence_count": _optional_int(metadata.get("shadow_evidence_count")),
        "phrase_control_evidence_count": _optional_int(
            metadata.get("phrase_control_evidence_count")
        ),
        "admitted_shadow_count": _optional_int(metadata.get("admitted_shadow_count")),
        "metadata_sources": _string_list(metadata.get("metadata_sources")),
        "difficulty_tags": _string_list(row.get("difficulty_tags")),
        "slice_tags": _string_list(row.get("slice_tags")),
    }
    trace["metadata_gap_flags"] = _metadata_gap_flags(trace)
    return trace


def _build_family_index(
    *,
    llm_plan_payload: Mapping[str, object],
    llm_scoring_payload: Mapping[str, object],
    v10_dataset_payload: Mapping[str, object],
    wave7_dataset_payload: Mapping[str, object],
) -> dict[str, object]:
    by_family_id: dict[str, dict[str, object]] = {}
    by_pilot_family_id: dict[str, dict[str, object]] = {}
    by_trigger_target: dict[tuple[str, str], dict[str, object]] = {}
    index: dict[str, object] = {
        "by_family_id": by_family_id,
        "by_pilot_family_id": by_pilot_family_id,
        "by_trigger_target": by_trigger_target,
    }
    for payload, source_id in (
        (v10_dataset_payload, "sentence_veto_v10_dataset"),
        (wave7_dataset_payload, "wave7_dataset"),
    ):
        for family in _mapping_rows(payload.get("families")):
            metadata = _family_metadata(family, source_id=source_id)
            _index_metadata(metadata, by_family_id, by_trigger_target)
    for family in _mapping_rows(llm_plan_payload.get("pilot_families")):
        metadata = _llm_plan_family_metadata(family)
        pilot_family_id = str(family.get("family_id") or "").strip()
        if pilot_family_id:
            by_pilot_family_id[pilot_family_id] = _merge_metadata(
                by_pilot_family_id.get(pilot_family_id),
                metadata,
            )
        trigger = str(metadata.get("trigger") or "").strip()
        target = str(metadata.get("active_target") or "").strip()
        if trigger and target:
            key = (_normalize_lemma_key(trigger), _normalize_lemma_key(target))
            by_trigger_target[key] = _merge_metadata(by_trigger_target.get(key), metadata)
    for coverage in _mapping_rows(llm_scoring_payload.get("coverage_rows")):
        metadata = _llm_coverage_metadata(coverage)
        _index_metadata(metadata, by_family_id, by_trigger_target)
    return index


def _index_metadata(
    metadata: Mapping[str, object],
    by_family_id: dict[str, dict[str, object]],
    by_trigger_target: dict[tuple[str, str], dict[str, object]],
) -> None:
    family_id = str(metadata.get("family_id") or "").strip()
    if family_id:
        by_family_id[family_id] = _merge_metadata(by_family_id.get(family_id), metadata)
    trigger = str(metadata.get("trigger") or "").strip()
    target = str(metadata.get("active_target") or "").strip()
    if trigger and target:
        key = (_normalize_lemma_key(trigger), _normalize_lemma_key(target))
        by_trigger_target[key] = _merge_metadata(by_trigger_target.get(key), metadata)


def _family_metadata(family: Mapping[str, object], *, source_id: str) -> dict[str, object]:
    active = _as_mapping(family.get("active"))
    raw_metadata = _as_mapping(family.get("metadata"))
    source_candidate = _as_mapping(raw_metadata.get("source_candidate"))
    active_metadata = _as_mapping(active.get("metadata"))
    shadows = _mapping_rows(family.get("shadows"))
    translation_candidates = _mapping_rows(raw_metadata.get("translation_candidates"))
    pos_counts = _as_mapping(source_candidate.get("pos_counts"))
    return {
        "metadata_sources": [source_id],
        "family_id": str(family.get("family_id") or "").strip(),
        "trigger": str(family.get("trigger") or "").strip(),
        "active_target": str(active.get("target_lemma") or "").strip(),
        "target_translation_rank": _optional_int(active_metadata.get("translation_rank")),
        "active_evidence_count": _evidence_view_count(active),
        "admitted_shadow_count": len(shadows),
        "shadow_evidence_count": sum(_evidence_view_count(shadow) for shadow in shadows),
        "phrase_control_evidence_count": _phrase_case_count(family),
        "wordnet_sense_count": _optional_int(source_candidate.get("sense_count")),
        "wordnet_pos_count": len(pos_counts) if pos_counts else None,
        "translation_candidate_count": (
            len(translation_candidates) if translation_candidates else None
        ),
        "source_complexity_band": str(source_candidate.get("complexity_band") or "").strip(),
    }


def _llm_plan_family_metadata(family: Mapping[str, object]) -> dict[str, object]:
    return {
        "metadata_sources": ["llm_pilot_plan"],
        "pilot_family_id": str(family.get("family_id") or "").strip(),
        "trigger": str(family.get("trigger") or "").strip(),
        "active_target": str(family.get("candidate_replacement") or "").strip(),
        "declared_frequency_band": str(family.get("frequency_band") or "").strip(),
        "declared_ambiguity_class": str(family.get("ambiguity_class") or "").strip(),
    }


def _llm_coverage_metadata(coverage: Mapping[str, object]) -> dict[str, object]:
    return {
        "metadata_sources": ["llm_pilot_scoring_coverage"],
        "family_id": str(coverage.get("family_id") or "").strip(),
        "trigger": str(coverage.get("trigger") or "").strip(),
        "active_target": str(coverage.get("active_target") or "").strip(),
        "active_evidence_count": _optional_int(coverage.get("active_example_count")),
        "shadow_evidence_count": _optional_int(coverage.get("shadow_example_count")),
        "phrase_control_evidence_count": _optional_int(
            coverage.get("phrase_control_example_count")
        ),
        "admitted_shadow_count": len(_string_list(coverage.get("shadow_targets"))),
    }


def _metadata_for_row(
    *,
    row: Mapping[str, object],
    family_id: str,
    trigger: str,
    index: Mapping[str, object],
) -> Mapping[str, object]:
    by_family_id = _as_mapping(index.get("by_family_id"))
    by_pilot_family_id = _as_mapping(index.get("by_pilot_family_id"))
    by_trigger_target = _as_mapping(index.get("by_trigger_target"))
    metadata: dict[str, object] = {}
    if family_id and family_id in by_family_id:
        metadata = _merge_metadata(metadata, _as_mapping(by_family_id[family_id]))
    pilot_family_id = str(row.get("pilot_family_id") or "").strip()
    if pilot_family_id and pilot_family_id in by_pilot_family_id:
        metadata = _merge_metadata(metadata, _as_mapping(by_pilot_family_id[pilot_family_id]))
    target = str(row.get("candidate_replacement") or metadata.get("active_target") or "").strip()
    if trigger and target:
        key = (_normalize_lemma_key(trigger), _normalize_lemma_key(target))
        if key in by_trigger_target:
            metadata = _merge_metadata(metadata, _as_mapping(by_trigger_target[key]))
    return metadata


def _merge_metadata(
    current: Mapping[str, object] | None,
    incoming: Mapping[str, object],
) -> dict[str, object]:
    merged = dict(current or {})
    sources = set(_string_list(merged.get("metadata_sources")))
    sources.update(_string_list(incoming.get("metadata_sources")))
    for key, value in incoming.items():
        if key == "metadata_sources":
            continue
        if _has_value(value) and not _has_value(merged.get(key)):
            merged[key] = value
    merged["metadata_sources"] = sorted(sources)
    return merged


def _source_report(source: Mapping[str, object]) -> tuple[Mapping[str, object], Path | None]:
    inline = source.get("report")
    if isinstance(inline, Mapping):
        return inline, None
    path_text = str(source.get("path") or "").strip()
    if not path_text:
        raise ValueError("Policy report source needs path or inline report.")
    path = _resolve_repo_path(path_text)
    return _load_json(path), path


def _case_rows(payload: Mapping[str, object]) -> list[Mapping[str, object]]:
    for key in ("configured_case_results", "row_results", "case_results"):
        rows = _mapping_rows(payload.get(key))
        if rows:
            return rows
    return []


def _target_lemma(
    *,
    row: Mapping[str, object],
    metadata: Mapping[str, object],
    family_id: str,
) -> str:
    explicit = str(row.get("candidate_replacement") or "").strip()
    if explicit:
        return explicit
    active_target = str(metadata.get("active_target") or "").strip()
    if active_target:
        return active_target
    parts = family_id.split(":")
    return parts[-1].strip() if parts else ""


def _metadata_gap_flags(row: Mapping[str, object]) -> list[str]:
    flags = []
    if row.get("source_trigger_rank_en") is None:
        flags.append("missing_source_trigger_rank_en")
    if row.get("source_zipf_frequency_en") is None:
        flags.append("missing_source_zipf_frequency_en")
    if row.get("target_lemma_rank_es") is None:
        flags.append("missing_target_lemma_rank_es")
    if row.get("wordnet_sense_count") is None:
        flags.append("missing_wordnet_sense_count")
    if row.get("translation_candidate_count") is None:
        flags.append("missing_translation_candidate_count")
    return flags


def _evidence_view_count(sense: Mapping[str, object]) -> int:
    views = _as_mapping(sense.get("evidence_views"))
    return sum(1 for value in views.values() if str(value or "").strip())


def _phrase_case_count(family: Mapping[str, object]) -> int:
    count = 0
    for case in _mapping_rows(family.get("cases")):
        if str(case.get("gold_winner") or "").strip().lower() in {"none", ""}:
            count += 1
        elif "phrase_no_winner" in _string_list(case.get("slice_tags")):
            count += 1
    return count


def _normalize_decision(value: object) -> str:
    text = str(value or "").strip().lower()
    if text in {"replace", "allow", "yes"}:
        return "replace"
    if text in {"abstain", "no_replace", "no-replace", "no", "none"}:
        return "abstain"
    return ""


def _product_outcome(*, gold: str, predicted: str) -> str:
    product_class = "positive" if gold == "replace" else "negative"
    user_outcome = "allow" if predicted == "replace" else "abstain"
    return f"{product_class}_{user_outcome}"


def _error_type(*, gold: str, predicted: str) -> str:
    if gold == predicted:
        return ""
    if gold == "replace" and predicted != "replace":
        return "false_abstain"
    if gold != "replace" and predicted == "replace":
        return "harmful_replace"
    return "other_mismatch"


def _rank_bin(rank: object) -> str:
    value = _optional_float(rank)
    if value is None or value <= 0:
        return "missing"
    for lower, upper, label in RANK_BINS:
        if lower <= value <= upper:
            return label
    return ">5000"


def _count_bin(value: object) -> str:
    count = _optional_int(value)
    if count is None:
        return "missing"
    if count <= 0:
        return "0"
    if count == 1:
        return "1"
    if count <= 4:
        return "2-4"
    if count <= 9:
        return "5-9"
    return "10+"


def _positive_allow_rate(rows: Sequence[Mapping[str, object]]) -> float | None:
    positives = [
        row
        for row in rows
        if str(row.get("product_outcome") or "") in {"positive_allow", "positive_abstain"}
    ]
    if not positives:
        return None
    allowed = sum(
        1 for row in positives if str(row.get("product_outcome") or "") == "positive_allow"
    )
    return _round4(allowed / len(positives))


def _signed_margin_bin(value: object, *, positive_label: str) -> str:
    margin = _optional_float(value)
    if margin is None:
        return "missing"
    if margin >= 0.1:
        return f"{positive_label}_clear_0.10+"
    if margin >= 0.05:
        return f"{positive_label}_blocker_0.05_0.10"
    if margin >= 0.0:
        return f"{positive_label}_near_tie_0_0.05"
    if margin >= -0.05:
        return "active_near_tie_0_0.05"
    return "active_clear_0.05+"
