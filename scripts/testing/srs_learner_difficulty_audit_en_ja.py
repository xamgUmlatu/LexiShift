#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import random
import sys
from typing import Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / "core"
sys.path.insert(0, str(CORE_ROOT))

from lexishift_core.helper.lp_capabilities import (  # noqa: E402
    default_frequency_db_path,
    default_jmdict_path,
    default_jmnedict_path,
    default_kanjidic2_path,
    default_kanjivg_path,
)
from lexishift_core.helper.paths import build_helper_paths  # noqa: E402
from lexishift_core.srs.profile_bootstrap import (  # noqa: E402
    extract_profile_bootstrap_candidate_traits,
    score_seed_words_for_profile,
)
from lexishift_core.srs.candidate_classification import (  # noqa: E402
    CandidateClassification,
    classify_srs_candidate,
)
from lexishift_core.srs.seed import SeedSelectionConfig, build_seed_candidates  # noqa: E402
from lexishift_core.srs.selector import (  # noqa: E402
    SELECTION_POLICY_RESERVED_TOPIC_LANE,
    SELECTION_POLICY_TOP_N,
    SELECTION_POLICY_WEIGHTED_WITHOUT_REPLACEMENT,
    SelectorConfig,
    select_scored_candidates,
)


PAIR = "en-ja"
DEFAULT_INITIAL_ACTIVE_COUNT = 40
DEFAULT_PREVIEW_COUNT = 10
DEFAULT_SAMPLE_SEED = 101
DEFAULT_PROFICIENCY_LEVELS = (0.0, 0.25, 0.5, 0.75, 1.0)
DEFAULT_CHALLENGE_TARGETS = (0.2, 0.45, 0.7, 0.9)
DEFAULT_CHALLENGE_FIXED_PROFICIENCY = 0.55
DEFAULT_CALIBRATION_JSON = (
    PROJECT_ROOT / "docs" / "test_inputs" / "srs_learner_difficulty_calibration_en_ja.json"
)
DEFAULT_JSON_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "srs_learner_difficulty_audit_en_ja_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "srs_learner_difficulty_audit_en_ja_latest.md"
)
MAX_MARKDOWN_SAMPLE_ROWS = 12
MAX_EXAMPLES_PER_BUCKET = 12
DIFFICULTY_BAND_BEGINNER_MAX = 0.55
DIFFICULTY_BAND_INTERMEDIATE_MAX = 0.80
VOCAB_LANE_STATES = frozenset({"normal_vocab", "deprioritized_vocab"})


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Research-only en-ja SRS learner-difficulty audit. The audit separates "
            "frequency/commonness, admission suitability, and obvious presentation "
            "classes without changing runtime admission behavior."
        )
    )
    parser.add_argument("--frequency-db", type=Path)
    parser.add_argument("--jmdict", type=Path)
    parser.add_argument("--jmnedict", type=Path)
    parser.add_argument("--kanjidic2", type=Path)
    parser.add_argument("--kanjivg", type=Path)
    parser.add_argument(
        "--top-n",
        type=int,
        default=None,
        help="Optional finite seed frontier. Omit to audit all available seed rows.",
    )
    parser.add_argument("--initial-active-count", type=int, default=DEFAULT_INITIAL_ACTIVE_COUNT)
    parser.add_argument("--preview-count", type=int, default=DEFAULT_PREVIEW_COUNT)
    parser.add_argument("--sample-seed", type=int, default=DEFAULT_SAMPLE_SEED)
    parser.add_argument(
        "--selection-policy",
        choices=(
            SELECTION_POLICY_TOP_N,
            SELECTION_POLICY_RESERVED_TOPIC_LANE,
            SELECTION_POLICY_WEIGHTED_WITHOUT_REPLACEMENT,
        ),
        default=SELECTION_POLICY_RESERVED_TOPIC_LANE,
    )
    parser.add_argument(
        "--proficiency-levels",
        default=",".join(f"{value:.2f}" for value in DEFAULT_PROFICIENCY_LEVELS),
        help="Comma-separated proficiency levels to audit.",
    )
    parser.add_argument("--calibration-json", type=Path, default=DEFAULT_CALIBRATION_JSON)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_report(
        frequency_db=args.frequency_db,
        jmdict_path=args.jmdict,
        jmnedict_path=args.jmnedict,
        kanjidic2_path=args.kanjidic2,
        kanjivg_path=args.kanjivg,
        top_n=max(1, int(args.top_n)) if args.top_n is not None else None,
        initial_active_count=max(1, int(args.initial_active_count)),
        preview_count=max(1, int(args.preview_count)),
        sample_seed=int(args.sample_seed),
        selection_policy=str(args.selection_policy),
        proficiency_levels=_parse_proficiency_levels(args.proficiency_levels),
        calibration_json=_resolve_path(args.calibration_json),
    )
    json_out = _resolve_path(args.json_out)
    markdown_out = _resolve_path(args.markdown_out)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown_out.write_text(render_markdown(report), encoding="utf-8")
    print(f"Wrote JSON artifact to {json_out}")
    print(f"Wrote Markdown artifact to {markdown_out}")
    return 0


def build_report(
    *,
    frequency_db: Path | None,
    jmdict_path: Path | None,
    jmnedict_path: Path | None,
    kanjidic2_path: Path | None,
    kanjivg_path: Path | None,
    top_n: int | None,
    initial_active_count: int,
    preview_count: int,
    sample_seed: int,
    selection_policy: str,
    proficiency_levels: Sequence[float],
    calibration_json: Path,
) -> dict[str, object]:
    paths = build_helper_paths()
    resolved_frequency_db = _resolve_frequency_db(frequency_db, paths.frequency_packs_dir)
    resolved_jmdict_path = _resolve_jmdict_path(jmdict_path, paths.language_packs_dir)
    resolved_jmnedict_path = _resolve_jmnedict_path(jmnedict_path, paths.language_packs_dir)
    resolved_kanjidic2_path = _resolve_kanjidic2_path(kanjidic2_path, paths.language_packs_dir)
    resolved_kanjivg_path = _resolve_kanjivg_path(kanjivg_path, paths.language_packs_dir)
    stopwords_path = _resolve_stopwords_path(paths.srs_dir)
    seeds = build_seed_candidates(
        frequency_db=resolved_frequency_db,
        config=SeedSelectionConfig(
            language_pair=PAIR,
            top_n=max(1, int(top_n)) if top_n is not None else None,
            jmdict_path=resolved_jmdict_path,
            jmnedict_path=resolved_jmnedict_path,
            kanjidic2_path=resolved_kanjidic2_path,
            kanjivg_path=resolved_kanjivg_path,
            stopwords_path=stopwords_path,
            require_jmdict=True,
            source_label="freq-ja-bccwj",
        ),
    )
    unique_seeds = _dedupe_seeds(seeds)
    seed_rows = [_seed_row(seed) for seed in unique_seeds]
    calibration_rows = _build_calibration_rows(
        calibration_json=calibration_json,
        seed_rows=seed_rows,
    )
    calibration_metrics = _calibration_metrics(calibration_rows)
    proficiency_reports = [
        _build_proficiency_report(
            unique_seeds,
            proficiency=value,
            initial_active_count=initial_active_count,
            preview_count=preview_count,
            sample_seed=sample_seed,
            selection_policy=selection_policy,
        )
        for value in proficiency_levels
    ]
    challenge_target_reports = [
        _build_challenge_target_report(
            unique_seeds,
            challenge_target=value,
            fixed_proficiency=DEFAULT_CHALLENGE_FIXED_PROFICIENCY,
            initial_active_count=initial_active_count,
            preview_count=preview_count,
            sample_seed=sample_seed,
            selection_policy=selection_policy,
        )
        for value in DEFAULT_CHALLENGE_TARGETS
    ]
    findings = _build_findings(
        frequency_db=resolved_frequency_db,
        jmdict_path=resolved_jmdict_path,
        seed_rows=seed_rows,
        calibration_rows=calibration_rows,
        calibration_metrics=calibration_metrics,
        proficiency_reports=proficiency_reports,
        challenge_target_reports=challenge_target_reports,
    )
    status = "review" if any(row["level"] == "WARN" for row in findings) else "ok"
    return {
        "schema_version": 1,
        "status": status,
        "decision": "shared_classifier_profile_bootstrap_suitability_enabled",
        "generated_at": _utc_now(),
        "language_pair": PAIR,
        "inputs": {
            "frequency_db": _repo_or_home_path(resolved_frequency_db),
            "jmdict": _repo_or_home_path(resolved_jmdict_path),
            "jmnedict": (
                _repo_or_home_path(resolved_jmnedict_path) if resolved_jmnedict_path else None
            ),
            "kanjidic2": (
                _repo_or_home_path(resolved_kanjidic2_path) if resolved_kanjidic2_path else None
            ),
            "kanjivg": (
                _repo_or_home_path(resolved_kanjivg_path) if resolved_kanjivg_path else None
            ),
            "stopwords_path": _repo_or_home_path(stopwords_path) if stopwords_path else None,
            "calibration_json": _repo_or_home_path(calibration_json),
            "top_n": int(top_n) if top_n is not None else None,
            "candidate_frontier": "limited" if top_n is not None else "all",
            "initial_active_count": int(initial_active_count),
            "preview_count": int(preview_count),
            "sample_seed": int(sample_seed),
            "selection_policy": selection_policy,
            "proficiency_levels": [round(float(value), 4) for value in proficiency_levels],
        },
        "method": {
            "candidate_source": "BCCWJ seed candidates filtered by installed JMDict lemmas",
            "difficulty_current_proxy": "1 - base_weight",
            "classification_posture": (
                "shared production classifier for obvious classes plus review-confidence "
                "POS classes; not a general compositional parser"
            ),
            "runtime_behavior_changed": True,
            "runtime_behavior": "profile_bootstrap applies admission_suitability to selection",
        },
        "frontier_summary": _frontier_summary(seed_rows),
        "calibration": {
            "calibration_json": _repo_or_home_path(calibration_json),
            "row_count": len(calibration_rows),
            "match_count": sum(1 for row in calibration_rows if row["status"] == "match"),
            "missing_count": sum(1 for row in calibration_rows if row["status"] == "missing"),
            "mismatch_count": sum(1 for row in calibration_rows if row["status"] == "mismatch"),
            "metrics": calibration_metrics,
            "rows": calibration_rows,
        },
        "proficiency_reports": proficiency_reports,
        "challenge_target_reports": challenge_target_reports,
        "findings": findings,
    }


def _resolve_frequency_db(value: Path | None, frequency_packs_dir: Path) -> Path:
    if value is not None:
        return _resolve_path(value)
    resolved = default_frequency_db_path(PAIR, frequency_packs_dir=frequency_packs_dir)
    if resolved is None:
        raise FileNotFoundError("Could not resolve default en-ja frequency DB.")
    return resolved


def _resolve_jmdict_path(value: Path | None, language_packs_dir: Path) -> Path:
    if value is not None:
        return _resolve_path(value)
    resolved = default_jmdict_path(PAIR, language_packs_dir=language_packs_dir)
    if resolved is None:
        raise FileNotFoundError("Could not resolve default en-ja JMDict path.")
    return resolved


def _resolve_kanjidic2_path(value: Path | None, language_packs_dir: Path) -> Path | None:
    if value is not None:
        return _resolve_path(value)
    resolved = default_kanjidic2_path(PAIR, language_packs_dir=language_packs_dir)
    return resolved if resolved and resolved.exists() else None


def _resolve_jmnedict_path(value: Path | None, language_packs_dir: Path) -> Path | None:
    if value is not None:
        return _resolve_path(value)
    resolved = default_jmnedict_path(PAIR, language_packs_dir=language_packs_dir)
    return resolved if resolved and resolved.exists() else None


def _resolve_kanjivg_path(value: Path | None, language_packs_dir: Path) -> Path | None:
    if value is not None:
        return _resolve_path(value)
    resolved = default_kanjivg_path(PAIR, language_packs_dir=language_packs_dir)
    return resolved if resolved and resolved.exists() else None


def _resolve_stopwords_path(srs_dir: Path) -> Path | None:
    path = srs_dir / "stopwords" / "stopwords-ja.json"
    return path if path.exists() else None


def _dedupe_seeds(seeds: Sequence[object]) -> list[object]:
    seen: set[str] = set()
    deduped: list[object] = []
    for seed in seeds:
        row = _seed_row(seed)
        key = str(row.get("candidate_identity_key") or "").strip()
        if not key:
            key = "|".join(
                (
                    str(row.get("language_pair") or "").strip(),
                    str(row.get("lemma") or "").strip(),
                    str(row.get("reading") or "").strip(),
                    str(row.get("pos") or "").strip(),
                )
            )
        if not key.strip("|") or key in seen:
            continue
        seen.add(key)
        deduped.append(seed)
    return deduped


def _seed_row(seed: object) -> dict[str, object]:
    classification = _classification_for_seed(seed)
    traits = extract_profile_bootstrap_candidate_traits(seed)
    word_package = getattr(seed, "word_package", None)
    word_package_payload = _as_mapping(word_package)
    source_payload = _as_mapping(
        word_package.get("source") if isinstance(word_package, Mapping) else None
    )
    row = {
        "candidate_identity_key": str(getattr(seed, "identity_key", "") or "")
        or str(_as_mapping(getattr(seed, "metadata", None)).get("candidate_identity_key") or ""),
        "candidate_identity": _as_mapping(
            _as_mapping(getattr(seed, "metadata", None)).get("candidate_identity")
        ),
        "lemma": str(getattr(seed, "lemma", "") or "").strip(),
        "language_pair": str(getattr(seed, "language_pair", "") or "").strip(),
        "core_rank": _rounded_or_none(getattr(seed, "core_rank", None)),
        "pmw": _rounded_or_none(getattr(seed, "pmw", None)),
        "base_weight": _rounded_or_none(getattr(seed, "base_weight", None)),
        "admission_weight": _rounded_or_none(getattr(seed, "admission_weight", None)),
        "pos": _optional_str(getattr(seed, "pos", None)),
        "pos_bucket": _optional_str(getattr(seed, "pos_bucket", None)),
        "pos_weight": _rounded_or_none(getattr(seed, "pos_weight", None)),
        "pos_canonical": _optional_str(getattr(seed, "pos_canonical", None)),
        "pos_matched_rule": _optional_str(getattr(seed, "pos_matched_rule", None)),
        "reading": _optional_str(
            word_package_payload.get("reading") if isinstance(word_package, Mapping) else None
        ),
        "sublemma": _optional_str(source_payload.get("sublemma")),
        "wtype": _optional_str(word_package_payload.get("wtype") or source_payload.get("wtype")),
        "candidate_state": classification.candidate_state,
        "presentation_mode": classification.presentation_mode,
        "problem_class": classification.problem_class,
        "classification_confidence": classification.confidence,
        "classification_reasons": list(classification.reasons),
        "admission_suitability": _rounded_or_none(classification.admission_suitability),
    }
    row["frequency_difficulty_proxy"] = _rounded_or_none(1.0 - float(row["base_weight"] or 0.0))
    row["current_difficulty_proxy"] = _rounded_or_none(traits.difficulty_estimate)
    row["difficulty_proxy"] = traits.difficulty_proxy
    row["difficulty_sources"] = list(traits.difficulty_sources)
    row["learner_signal_sources"] = list(traits.learner_signals.get("sources", ()) or ())
    row["learner_signals"] = traits.learner_signals
    row["source_frequency_profile"] = _as_mapping(
        _as_mapping(getattr(seed, "metadata", None)).get("source_frequency_profile")
    )
    return row


def _classification_for_seed(seed: object) -> CandidateClassification:
    lemma = str(getattr(seed, "lemma", "") or "").strip()
    metadata = _as_mapping(getattr(seed, "metadata", None))
    fallback = classify_srs_candidate(
        language_pair=str(getattr(seed, "language_pair", "") or "").strip() or PAIR,
        lemma=lemma,
        raw_pos=getattr(seed, "pos_raw", None) or getattr(seed, "pos", None),
    )
    suitability = _safe_float(getattr(seed, "admission_suitability", None))
    if suitability is None:
        suitability = _safe_float(metadata.get("admission_suitability"))
    if suitability is None:
        suitability = fallback.admission_suitability
    return CandidateClassification(
        candidate_state=_string_attr_or_metadata(
            seed,
            metadata,
            attr="candidate_state",
            fallback=fallback.candidate_state,
        ),
        presentation_mode=_string_attr_or_metadata(
            seed,
            metadata,
            attr="presentation_mode",
            fallback=fallback.presentation_mode,
        ),
        problem_class=_string_attr_or_metadata(
            seed,
            metadata,
            attr="problem_class",
            fallback=fallback.problem_class,
        ),
        confidence=_string_attr_or_metadata(
            seed,
            metadata,
            attr="classification_confidence",
            fallback=fallback.confidence,
        ),
        reasons=_sequence_attr_or_metadata(
            seed,
            metadata,
            attr="classification_reasons",
            fallback=tuple(fallback.reasons),
        ),
        admission_suitability=suitability,
    )


def _build_proficiency_report(
    seeds: Sequence[object],
    *,
    proficiency: float,
    initial_active_count: int,
    preview_count: int,
    sample_seed: int,
    selection_policy: str,
) -> dict[str, object]:
    profile_context = {"proficiency": {"estimated_value": float(proficiency)}}
    scored_entries, diagnostics = score_seed_words_for_profile(
        seeds,
        profile_context=profile_context,
        preview_limit=0,
    )
    unique_entries = _dedupe_scored_entries(scored_entries)
    selector_config = SelectorConfig(
        selection_policy=selection_policy,
        top_n=max(1, int(initial_active_count)),
    )
    selected_candidates = select_scored_candidates(
        [entry.scored_candidate for entry in unique_entries],
        config=selector_config,
        selection_count=max(1, int(initial_active_count)),
        seed=sample_seed,
    )
    entries_by_identity = {
        str(entry.scored_candidate.candidate.metadata.get("candidate_identity_key") or ""): entry
        for entry in unique_entries
        if str(entry.scored_candidate.candidate.metadata.get("candidate_identity_key") or "")
    }
    active_rows = [
        _scored_entry_row(
            entries_by_identity[
                str(candidate.candidate.metadata.get("candidate_identity_key") or "")
            ]
        )
        for candidate in selected_candidates
        if str(candidate.candidate.metadata.get("candidate_identity_key") or "")
        in entries_by_identity
    ]
    sampled_rows = _sample_active_rows(
        active_rows,
        preview_count=preview_count,
        sample_seed=sample_seed,
    )
    return {
        "proficiency": round(float(proficiency), 4),
        "active_count": len(active_rows),
        "sample_count": len(sampled_rows),
        "difficulty_summary_active": _difficulty_summary(active_rows),
        "difficulty_summary_sample": _difficulty_summary(sampled_rows),
        "candidate_state_counts_active": _counter_dict(
            row["candidate_state"] for row in active_rows
        ),
        "candidate_state_counts_sample": _counter_dict(
            row["candidate_state"] for row in sampled_rows
        ),
        "classification_confidence_counts_active": _counter_dict(
            row["classification_confidence"] for row in active_rows
        ),
        "classification_confidence_counts_sample": _counter_dict(
            row["classification_confidence"] for row in sampled_rows
        ),
        "problem_class_counts_active": _counter_dict(row["problem_class"] for row in active_rows),
        "problem_class_counts_sample": _counter_dict(row["problem_class"] for row in sampled_rows),
        "selector_policy_version": diagnostics.get("selector_policy_version"),
        "selection_weights": diagnostics.get("selection_weights"),
        "sample_rows": sampled_rows,
        "active_rows": active_rows,
    }


def _build_challenge_target_report(
    seeds: Sequence[object],
    *,
    challenge_target: float,
    fixed_proficiency: float,
    initial_active_count: int,
    preview_count: int,
    sample_seed: int,
    selection_policy: str,
) -> dict[str, object]:
    profile_context = {
        "proficiency": {"estimated_value": float(fixed_proficiency)},
        "difficulty_preferences": {
            "target_challenge_center": float(challenge_target),
            "target_challenge_spread": 0.12,
        },
    }
    scored_entries, diagnostics = score_seed_words_for_profile(
        seeds,
        profile_context=profile_context,
        preview_limit=0,
    )
    unique_entries = _dedupe_scored_entries(scored_entries)
    selector_config = SelectorConfig(
        selection_policy=selection_policy,
        top_n=max(1, int(initial_active_count)),
    )
    selected_candidates = select_scored_candidates(
        [entry.scored_candidate for entry in unique_entries],
        config=selector_config,
        selection_count=max(1, int(initial_active_count)),
        seed=sample_seed,
    )
    entries_by_identity = {
        str(entry.scored_candidate.candidate.metadata.get("candidate_identity_key") or ""): entry
        for entry in unique_entries
        if str(entry.scored_candidate.candidate.metadata.get("candidate_identity_key") or "")
    }
    active_rows = [
        _scored_entry_row(
            entries_by_identity[
                str(candidate.candidate.metadata.get("candidate_identity_key") or "")
            ]
        )
        for candidate in selected_candidates
        if str(candidate.candidate.metadata.get("candidate_identity_key") or "")
        in entries_by_identity
    ]
    sampled_rows = _sample_active_rows(
        active_rows,
        preview_count=preview_count,
        sample_seed=sample_seed,
    )
    return {
        "challenge_target": round(float(challenge_target), 4),
        "fixed_proficiency": round(float(fixed_proficiency), 4),
        "active_count": len(active_rows),
        "sample_count": len(sampled_rows),
        "difficulty_summary_active": _difficulty_summary(active_rows),
        "difficulty_summary_sample": _difficulty_summary(sampled_rows),
        "readiness_center_source_counts_active": _counter_dict(
            row.get("readiness_center_source") for row in active_rows
        ),
        "selector_policy_version": diagnostics.get("selector_policy_version"),
        "selection_weights": diagnostics.get("selection_weights"),
        "sample_rows": sampled_rows,
        "active_rows": active_rows,
    }


def _dedupe_scored_entries(scored_entries: Sequence[object]) -> list[object]:
    seen: set[str] = set()
    unique_entries: list[object] = []
    for entry in scored_entries:
        candidate = entry.scored_candidate.candidate
        key = str(candidate.metadata.get("candidate_identity_key") or "").strip()
        if not key:
            key = "|".join(
                (
                    str(candidate.language_pair or "").strip(),
                    str(candidate.lemma or "").strip(),
                )
            )
        if not key.strip("|") or key in seen:
            continue
        seen.add(key)
        unique_entries.append(entry)
    return unique_entries


def _scored_entry_row(entry: object) -> dict[str, object]:
    seed_row = _seed_row(entry.seed)
    signal_pack = entry.signal_pack
    breakdown = entry.scored_candidate.breakdown
    components = dict(breakdown.components)
    seed_row.update(
        {
            "profile_score": _rounded_or_none(breakdown.final_score),
            "score_components": {
                key: _rounded_or_none(value) for key, value in sorted(components.items())
            },
            "score_penalties": list(breakdown.penalties),
            "difficulty_estimate": _rounded_or_none(signal_pack.difficulty_estimate),
            "proficiency_fit": _rounded_or_none(signal_pack.proficiency_fit),
            "challenge_fit": _rounded_or_none(signal_pack.challenge_fit),
            "readiness_multiplier": _rounded_or_none(signal_pack.readiness_multiplier),
            "readiness_center": _rounded_or_none(signal_pack.readiness_center),
            "readiness_center_source": signal_pack.readiness_center_source,
            "readiness_lower_bound": _rounded_or_none(signal_pack.readiness_lower_bound),
            "readiness_upper_bound": _rounded_or_none(signal_pack.readiness_upper_bound),
            "readiness_too_easy_gap": _rounded_or_none(signal_pack.readiness_too_easy_gap),
            "readiness_too_hard_gap": _rounded_or_none(signal_pack.readiness_too_hard_gap),
        }
    )
    return seed_row


def _sample_active_rows(
    active_rows: Sequence[Mapping[str, object]],
    *,
    preview_count: int,
    sample_seed: int,
) -> list[dict[str, object]]:
    target = min(max(0, int(preview_count)), len(active_rows))
    if target <= 0:
        return []
    if target >= len(active_rows):
        return [dict(row) for row in active_rows]
    rng = random.Random(sample_seed)
    pool = [(dict(row), _sample_weight(row)) for row in active_rows]
    sampled: list[dict[str, object]] = []
    while len(sampled) < target and pool:
        total = sum(max(0.0, weight) for _row, weight in pool)
        if total <= 0.0:
            index = rng.randrange(len(pool))
        else:
            roll = rng.random() * total
            index = len(pool) - 1
            for candidate_index, (_row, weight) in enumerate(pool):
                roll -= max(0.0, weight)
                if roll <= 0.0:
                    index = candidate_index
                    break
        row, _weight = pool.pop(index)
        sampled.append(row)
    return sampled


def _sample_weight(row: Mapping[str, object]) -> float:
    for key in ("profile_score", "admission_weight", "base_weight"):
        value = _safe_float(row.get(key))
        if value is not None and value > 0.0:
            return max(0.001, value)
    return 1.0


def _build_calibration_rows(
    *,
    calibration_json: Path,
    seed_rows: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    payload = _load_json(calibration_json) if calibration_json.exists() else {}
    labels = payload.get("labels") if isinstance(payload, Mapping) else None
    if not isinstance(labels, Sequence) or isinstance(labels, (str, bytes)):
        return []
    rows: list[dict[str, object]] = []
    for label in labels:
        if not isinstance(label, Mapping):
            continue
        lemma = str(label.get("lemma") or "").strip()
        expected_reading = str(label.get("expected_reading") or "").strip()
        expected_pos_contains = str(label.get("expected_pos_contains") or "").strip()
        expected_state = str(label.get("expected_candidate_state") or "").strip()
        expected_mode = str(label.get("expected_presentation_mode") or "").strip()
        expected_problem_class = str(label.get("expected_problem_class") or "").strip()
        expected_difficulty_band = str(label.get("expected_difficulty_band") or "").strip()
        expected_learner_difficulty = _safe_float(label.get("expected_learner_difficulty"))
        observed = _select_calibration_seed_row(
            label,
            [row for row in seed_rows if str(row.get("lemma") or "").strip() == lemma],
        )
        if observed is None:
            status = "missing"
            observed_state = ""
            observed_mode = ""
            observed_problem_class = ""
            observed_difficulty_proxy = None
            observed_difficulty_band = ""
            observed_reading = ""
            observed_pos = ""
            candidate_identity_key = ""
        else:
            observed_state = str(observed.get("candidate_state") or "")
            observed_mode = str(observed.get("presentation_mode") or "")
            observed_problem_class = str(observed.get("problem_class") or "")
            observed_difficulty_proxy = _safe_float(observed.get("current_difficulty_proxy"))
            observed_difficulty_band = _difficulty_band_for_value(observed_difficulty_proxy)
            observed_reading = str(observed.get("reading") or "")
            observed_pos = str(observed.get("pos") or "")
            candidate_identity_key = str(observed.get("candidate_identity_key") or "")
            problem_class_matches = (
                not expected_problem_class or observed_problem_class == expected_problem_class
            )
            reading_matches = not expected_reading or observed_reading == expected_reading
            pos_matches = not expected_pos_contains or expected_pos_contains in observed_pos
            status = (
                "match"
                if (
                    observed_state == expected_state
                    and observed_mode == expected_mode
                    and problem_class_matches
                    and reading_matches
                    and pos_matches
                )
                else "mismatch"
            )
        if not expected_difficulty_band:
            difficulty_status = "not_labeled"
        elif observed is None:
            difficulty_status = "missing"
        elif observed_difficulty_band == expected_difficulty_band:
            difficulty_status = "match"
        else:
            difficulty_status = "mismatch"
        rows.append(
            {
                "lemma": lemma,
                "candidate_identity_key": candidate_identity_key,
                "status": status,
                "expected_reading": expected_reading,
                "observed_reading": observed_reading,
                "expected_pos_contains": expected_pos_contains,
                "observed_pos": observed_pos,
                "expected_candidate_state": expected_state,
                "observed_candidate_state": observed_state,
                "expected_presentation_mode": expected_mode,
                "observed_presentation_mode": observed_mode,
                "expected_problem_class": expected_problem_class,
                "observed_problem_class": observed_problem_class,
                "expected_difficulty_band": expected_difficulty_band,
                "observed_difficulty_band": observed_difficulty_band,
                "expected_learner_difficulty": _rounded_or_none(expected_learner_difficulty),
                "observed_current_difficulty_proxy": _rounded_or_none(observed_difficulty_proxy),
                "difficulty_absolute_error": _difficulty_absolute_error(
                    expected_learner_difficulty,
                    observed_difficulty_proxy,
                ),
                "difficulty_status": difficulty_status,
                "rationale": str(label.get("rationale") or "").strip(),
            }
        )
    return rows


def _select_calibration_seed_row(
    label: Mapping[str, object],
    candidates: Sequence[Mapping[str, object]],
) -> Mapping[str, object] | None:
    if not candidates:
        return None
    expected_reading = str(label.get("expected_reading") or "").strip()
    expected_pos_contains = str(label.get("expected_pos_contains") or "").strip()
    filtered = list(candidates)
    if expected_reading:
        reading_filtered = [
            row for row in filtered if str(row.get("reading") or "").strip() == expected_reading
        ]
        if not reading_filtered:
            return None
        filtered = reading_filtered
    if expected_pos_contains:
        pos_filtered = [
            row for row in filtered if expected_pos_contains in str(row.get("pos") or "").strip()
        ]
        if not pos_filtered:
            return None
        filtered = pos_filtered
    return filtered[0]


def _calibration_metrics(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    return {
        "classification": _classification_alignment_metrics(rows),
        "candidate_state": _label_precision_recall(
            rows,
            expected_key="expected_candidate_state",
            observed_key="observed_candidate_state",
        ),
        "presentation_mode": _label_precision_recall(
            rows,
            expected_key="expected_presentation_mode",
            observed_key="observed_presentation_mode",
        ),
        "problem_class": _label_precision_recall(
            rows,
            expected_key="expected_problem_class",
            observed_key="observed_problem_class",
        ),
        "default_vocab_decision": _default_vocab_decision_metrics(rows),
        "difficulty_bucket": _difficulty_bucket_metrics(rows),
        "difficulty_value": _difficulty_value_metrics(rows),
    }


def _classification_alignment_metrics(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    row_count = len(rows)
    missing_count = sum(1 for row in rows if row.get("status") == "missing")
    mismatch_count = sum(1 for row in rows if row.get("status") == "mismatch")
    match_count = sum(1 for row in rows if row.get("status") == "match")
    return {
        "row_count": row_count,
        "match_count": match_count,
        "missing_count": missing_count,
        "mismatch_count": mismatch_count,
        "exact_accuracy": _ratio(match_count, row_count),
    }


def _label_precision_recall(
    rows: Sequence[Mapping[str, object]],
    *,
    expected_key: str,
    observed_key: str,
) -> dict[str, object]:
    labeled_rows = [row for row in rows if str(row.get(expected_key) or "").strip()]
    labels = sorted(
        {
            str(row.get(expected_key) or "").strip()
            for row in labeled_rows
            if str(row.get(expected_key) or "").strip()
        }
        | {
            str(row.get(observed_key) or "").strip()
            for row in labeled_rows
            if str(row.get(observed_key) or "").strip()
        }
    )
    by_label: dict[str, dict[str, object]] = {}
    for label in labels:
        true_positive = sum(
            1
            for row in labeled_rows
            if str(row.get(expected_key) or "").strip() == label
            and str(row.get(observed_key) or "").strip() == label
        )
        false_positive = sum(
            1
            for row in labeled_rows
            if str(row.get(expected_key) or "").strip() != label
            and str(row.get(observed_key) or "").strip() == label
        )
        false_negative = sum(
            1
            for row in labeled_rows
            if str(row.get(expected_key) or "").strip() == label
            and str(row.get(observed_key) or "").strip() != label
        )
        by_label[label] = {
            "true_positive": true_positive,
            "false_positive": false_positive,
            "false_negative": false_negative,
            "precision": _ratio(true_positive, true_positive + false_positive),
            "recall": _ratio(true_positive, true_positive + false_negative),
        }
    match_count = sum(
        1
        for row in labeled_rows
        if str(row.get(expected_key) or "").strip() == str(row.get(observed_key) or "").strip()
    )
    return {
        "labeled_count": len(labeled_rows),
        "match_count": match_count,
        "accuracy": _ratio(match_count, len(labeled_rows)),
        "by_label": by_label,
        "confusion": _confusion_counts(
            labeled_rows,
            expected_key=expected_key,
            observed_key=observed_key,
        ),
    }


def _default_vocab_decision_metrics(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    present_rows = [row for row in rows if row.get("status") != "missing"]
    true_default_accept = 0
    false_default_admit = 0
    false_default_suppress = 0
    true_default_block = 0
    for row in present_rows:
        expected_default = str(row.get("expected_candidate_state") or "") in VOCAB_LANE_STATES
        observed_default = str(row.get("observed_candidate_state") or "") in VOCAB_LANE_STATES
        if expected_default and observed_default:
            true_default_accept += 1
        elif expected_default and not observed_default:
            false_default_suppress += 1
        elif not expected_default and observed_default:
            false_default_admit += 1
        else:
            true_default_block += 1
    correct = true_default_accept + true_default_block
    return {
        "evaluated_count": len(present_rows),
        "true_default_accept": true_default_accept,
        "true_default_block": true_default_block,
        "false_default_admit": false_default_admit,
        "false_default_suppress": false_default_suppress,
        "accuracy": _ratio(correct, len(present_rows)),
    }


def _difficulty_bucket_metrics(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    labeled_rows = [row for row in rows if str(row.get("expected_difficulty_band") or "").strip()]
    match_count = sum(1 for row in labeled_rows if row.get("difficulty_status") == "match")
    missing_count = sum(1 for row in labeled_rows if row.get("difficulty_status") == "missing")
    mismatch_count = sum(1 for row in labeled_rows if row.get("difficulty_status") == "mismatch")
    mismatches = [
        {
            "lemma": row.get("lemma"),
            "expected_difficulty_band": row.get("expected_difficulty_band"),
            "observed_difficulty_band": row.get("observed_difficulty_band"),
            "observed_current_difficulty_proxy": row.get("observed_current_difficulty_proxy"),
        }
        for row in labeled_rows
        if row.get("difficulty_status") == "mismatch"
    ]
    return {
        "labeled_count": len(labeled_rows),
        "match_count": match_count,
        "missing_count": missing_count,
        "mismatch_count": mismatch_count,
        "accuracy": _ratio(match_count, len(labeled_rows)),
        "confusion": _confusion_counts(
            labeled_rows,
            expected_key="expected_difficulty_band",
            observed_key="observed_difficulty_band",
        ),
        "mismatches": mismatches,
    }


def _difficulty_value_metrics(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    labeled_rows = [
        row for row in rows if _safe_float(row.get("expected_learner_difficulty")) is not None
    ]
    present_rows = [row for row in labeled_rows if row.get("status") != "missing"]
    errors = [
        float(error)
        for row in present_rows
        for error in [_safe_float(row.get("difficulty_absolute_error"))]
        if error is not None
    ]
    worst_errors = sorted(
        (
            {
                "lemma": row.get("lemma"),
                "expected_learner_difficulty": row.get("expected_learner_difficulty"),
                "observed_current_difficulty_proxy": row.get("observed_current_difficulty_proxy"),
                "absolute_error": row.get("difficulty_absolute_error"),
                "expected_difficulty_band": row.get("expected_difficulty_band"),
                "observed_difficulty_band": row.get("observed_difficulty_band"),
            }
            for row in present_rows
            if _safe_float(row.get("difficulty_absolute_error")) is not None
        ),
        key=lambda row: float(row.get("absolute_error") or 0.0),
        reverse=True,
    )[:20]
    return {
        "labeled_count": len(labeled_rows),
        "evaluated_count": len(errors),
        "missing_count": len(labeled_rows) - len(present_rows),
        "mae": _rounded_or_none(_mean(errors)),
        "rmse": _rounded_or_none(_rmse(errors)),
        "max_absolute_error": _rounded_or_none(max(errors) if errors else None),
        "within_0_05": sum(1 for error in errors if error <= 0.05),
        "within_0_10": sum(1 for error in errors if error <= 0.10),
        "within_0_15": sum(1 for error in errors if error <= 0.15),
        "worst_errors": worst_errors,
    }


def _confusion_counts(
    rows: Sequence[Mapping[str, object]],
    *,
    expected_key: str,
    observed_key: str,
) -> dict[str, dict[str, int]]:
    confusion: dict[str, Counter[str]] = {}
    for row in rows:
        expected = str(row.get(expected_key) or "").strip()
        observed = str(row.get(observed_key) or "").strip() or "missing"
        if not expected:
            continue
        bucket = confusion.setdefault(expected, Counter())
        bucket[observed] += 1
    return {
        expected: dict(sorted(counter.items())) for expected, counter in sorted(confusion.items())
    }


def _frontier_summary(seed_rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    return {
        "seed_count": len(seed_rows),
        "candidate_state_counts": _counter_dict(row["candidate_state"] for row in seed_rows),
        "presentation_mode_counts": _counter_dict(row["presentation_mode"] for row in seed_rows),
        "classification_confidence_counts": _counter_dict(
            row["classification_confidence"] for row in seed_rows
        ),
        "learner_signal_source_counts": _learner_signal_source_counts(seed_rows),
        "problem_class_counts": _counter_dict(row["problem_class"] for row in seed_rows),
        "pos_bucket_counts": _counter_dict(row["pos_bucket"] for row in seed_rows),
        "raw_pos_head_counts": _top_counter_rows(
            _pos_head(str(row.get("pos") or "")) for row in seed_rows
        ),
        "difficulty_summary": _difficulty_summary(seed_rows, key="current_difficulty_proxy"),
        "examples_by_problem_class": _examples_by_key(seed_rows, key="problem_class"),
        "examples_by_candidate_state": _examples_by_key(seed_rows, key="candidate_state"),
    }


def _build_findings(
    *,
    frequency_db: Path,
    jmdict_path: Path,
    seed_rows: Sequence[Mapping[str, object]],
    calibration_rows: Sequence[Mapping[str, object]],
    calibration_metrics: Mapping[str, object],
    proficiency_reports: Sequence[Mapping[str, object]],
    challenge_target_reports: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []
    findings.append(
        _finding(
            "PASS" if frequency_db.exists() else "FAIL",
            "frequency_db_available",
            f"Frequency DB: {_repo_or_home_path(frequency_db)}",
        )
    )
    findings.append(
        _finding(
            "PASS" if jmdict_path.exists() else "FAIL",
            "jmdict_available",
            f"JMDict: {_repo_or_home_path(jmdict_path)}",
        )
    )
    non_vocab_count = sum(
        1 for row in seed_rows if str(row.get("candidate_state") or "") != "normal_vocab"
    )
    findings.append(
        _finding(
            "WARN" if non_vocab_count else "PASS",
            "frontier_contains_non_vocab_candidate_states",
            f"{non_vocab_count} / {len(seed_rows)} unique seeds are obvious non-normal-vocab classes.",
        )
    )
    mismatch_count = sum(1 for row in calibration_rows if row.get("status") == "mismatch")
    missing_count = sum(1 for row in calibration_rows if row.get("status") == "missing")
    default_vocab_metrics = _as_mapping(calibration_metrics.get("default_vocab_decision"))
    difficulty_bucket_metrics = _as_mapping(calibration_metrics.get("difficulty_bucket"))
    difficulty_value_metrics = _as_mapping(calibration_metrics.get("difficulty_value"))
    findings.append(
        _finding(
            "WARN" if mismatch_count or missing_count else "PASS",
            "calibration_seed_set_alignment",
            f"{mismatch_count} mismatches and {missing_count} missing rows in calibration seed set.",
        )
    )
    false_default_admit = int(default_vocab_metrics.get("false_default_admit") or 0)
    false_default_suppress = int(default_vocab_metrics.get("false_default_suppress") or 0)
    findings.append(
        _finding(
            "WARN" if false_default_admit or false_default_suppress else "PASS",
            "calibration_default_vocab_decision_alignment",
            (
                "Default-vocab decision accuracy is "
                f"{default_vocab_metrics.get('accuracy')}; "
                f"false admits={false_default_admit}, "
                f"false suppressions={false_default_suppress}."
            ),
        )
    )
    difficulty_mismatch_count = int(difficulty_bucket_metrics.get("mismatch_count") or 0)
    difficulty_missing_count = int(difficulty_bucket_metrics.get("missing_count") or 0)
    findings.append(
        _finding(
            "WARN" if difficulty_mismatch_count or difficulty_missing_count else "PASS",
            "calibration_difficulty_bucket_alignment",
            (
                "Current learner-difficulty bucket accuracy is "
                f"{difficulty_bucket_metrics.get('accuracy')}; "
                f"mismatches={difficulty_mismatch_count}, missing={difficulty_missing_count}."
            ),
        )
    )
    difficulty_mae = _safe_float(difficulty_value_metrics.get("mae"))
    findings.append(
        _finding(
            "WARN" if difficulty_mae is not None and difficulty_mae > 0.15 else "PASS",
            "calibration_difficulty_value_alignment",
            (
                "Current learner-difficulty numeric MAE is "
                f"{difficulty_value_metrics.get('mae')} across "
                f"{difficulty_value_metrics.get('evaluated_count')} reviewed numeric labels."
            ),
        )
    )
    sample_non_vocab_count = sum(
        1
        for report in proficiency_reports
        for row in _mapping_rows(report.get("sample_rows"))
        if str(row.get("candidate_state") or "") != "normal_vocab"
    )
    sample_total = sum(
        len(_mapping_rows(report.get("sample_rows"))) for report in proficiency_reports
    )
    findings.append(
        _finding(
            "WARN" if sample_non_vocab_count else "PASS",
            "sample_non_vocab_leakage",
            f"{sample_non_vocab_count} / {sample_total} sampled rows are non-normal-vocab.",
        )
    )
    averages = [
        _safe_float(_as_mapping(row.get("difficulty_summary_sample")).get("avg"))
        for row in proficiency_reports
    ]
    monotonic = all(
        current is None or previous is None or current >= previous - 0.0001
        for previous, current in zip(averages, averages[1:])
    )
    findings.append(
        _finding(
            "PASS" if monotonic else "WARN",
            "sample_difficulty_average_monotonic",
            f"Sample difficulty averages by proficiency: {averages}",
        )
    )
    high_profile = proficiency_reports[-1] if proficiency_reports else {}
    high_avg = _safe_float(_as_mapping(high_profile.get("difficulty_summary_sample")).get("avg"))
    findings.append(
        _finding(
            "WARN" if high_avg is not None and high_avg < 0.80 else "PASS",
            "high_proficiency_not_strongly_advanced_under_current_proxy",
            f"Highest audited proficiency sample average difficulty is {high_avg}.",
        )
    )
    challenge_avgs = [
        _safe_float(_as_mapping(row.get("difficulty_summary_active")).get("avg"))
        for row in challenge_target_reports
    ]
    challenge_spread = (
        max(value for value in challenge_avgs if value is not None)
        - min(value for value in challenge_avgs if value is not None)
        if any(value is not None for value in challenge_avgs)
        else 0.0
    )
    findings.append(
        _finding(
            "PASS" if challenge_spread >= 0.25 else "WARN",
            "challenge_target_difficulty_spread",
            (
                "Active difficulty averages by challenge target at fixed proficiency "
                f"{DEFAULT_CHALLENGE_FIXED_PROFICIENCY}: {challenge_avgs}; "
                f"spread={round(challenge_spread, 6)}."
            ),
        )
    )
    return findings


def render_markdown(report: Mapping[str, object]) -> str:
    inputs = _as_mapping(report.get("inputs"))
    frontier = _as_mapping(report.get("frontier_summary"))
    lines = [
        "# en-ja SRS Learner Difficulty Audit",
        "",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Frequency DB: `{inputs.get('frequency_db', '')}`",
        f"- JMDict: `{inputs.get('jmdict', '')}`",
        f"- JMnedict: `{inputs.get('jmnedict', '')}`",
        f"- KANJIDIC2: `{inputs.get('kanjidic2', '')}`",
        f"- KanjiVG: `{inputs.get('kanjivg', '')}`",
        f"- Top N: `{inputs.get('top_n') if inputs.get('top_n') is not None else 'all'}`",
        "",
        "## Frontier Summary",
        "",
        f"- Unique seed count: `{frontier.get('seed_count', 0)}`",
        f"- Candidate states: `{_compact_counts(frontier.get('candidate_state_counts'))}`",
        f"- Presentation modes: `{_compact_counts(frontier.get('presentation_mode_counts'))}`",
        f"- Classification confidence: `{_compact_counts(frontier.get('classification_confidence_counts'))}`",
        f"- Problem classes: `{_compact_counts(frontier.get('problem_class_counts'))}`",
        f"- Learner signal sources: `{_compact_counts(frontier.get('learner_signal_source_counts'))}`",
        f"- Difficulty proxy: `{_compact_counts(frontier.get('difficulty_summary'))}`",
        "",
        "### Examples By Problem Class",
        "",
    ]
    examples = _as_mapping(frontier.get("examples_by_problem_class"))
    for key, rows in examples.items():
        row_values = (
            rows if isinstance(rows, Sequence) and not isinstance(rows, (str, bytes)) else []
        )
        examples_text = ", ".join(
            str(row.get("lemma")) for row in row_values if isinstance(row, Mapping)
        )
        lines.append(f"- `{key}`: {examples_text}")
    lines.extend(["", "## Calibration", ""])
    calibration = _as_mapping(report.get("calibration"))
    metrics = _as_mapping(calibration.get("metrics"))
    classification_metrics = _as_mapping(metrics.get("classification"))
    default_vocab_metrics = _as_mapping(metrics.get("default_vocab_decision"))
    difficulty_bucket_metrics = _as_mapping(metrics.get("difficulty_bucket"))
    difficulty_value_metrics = _as_mapping(metrics.get("difficulty_value"))
    lines.extend(
        [
            f"- Rows: `{calibration.get('row_count', 0)}`",
            f"- Matches: `{calibration.get('match_count', 0)}`",
            f"- Missing: `{calibration.get('missing_count', 0)}`",
            f"- Mismatches: `{calibration.get('mismatch_count', 0)}`",
            "",
            "### Calibration Metrics",
            "",
            (
                "- Classification exact accuracy: "
                f"`{classification_metrics.get('exact_accuracy')}` "
                f"({classification_metrics.get('match_count')} / "
                f"{classification_metrics.get('row_count')})"
            ),
            (
                "- Default-vocab decision accuracy: "
                f"`{default_vocab_metrics.get('accuracy')}` "
                f"(false admits `{default_vocab_metrics.get('false_default_admit')}`, "
                f"false suppressions `{default_vocab_metrics.get('false_default_suppress')}`)"
            ),
            (
                "- Difficulty bucket accuracy under current learner difficulty: "
                f"`{difficulty_bucket_metrics.get('accuracy')}` "
                f"({difficulty_bucket_metrics.get('match_count')} / "
                f"{difficulty_bucket_metrics.get('labeled_count')})"
            ),
            (
                "- Difficulty numeric error under current learner difficulty: "
                f"`mae={difficulty_value_metrics.get('mae')}, "
                f"rmse={difficulty_value_metrics.get('rmse')}, "
                f"within_0_10={difficulty_value_metrics.get('within_0_10')} / "
                f"{difficulty_value_metrics.get('evaluated_count')}`"
            ),
            "",
        ]
    )
    _append_label_metric_table(lines, "Candidate State", metrics.get("candidate_state"))
    _append_label_metric_table(lines, "Presentation Mode", metrics.get("presentation_mode"))
    _append_label_metric_table(lines, "Problem Class", metrics.get("problem_class"))
    lines.extend(
        [
            "### Calibration Rows",
            "",
            "| Lemma | Status | Expected | Observed | Difficulty | Proxy | Rationale |",
            "| --- | --- | --- | --- | --- | ---: | --- |",
        ]
    )
    for row in _mapping_rows(calibration.get("rows")):
        lines.append(
            "| "
            f"`{_escape_md(row.get('lemma'))}` | "
            f"`{_escape_md(row.get('status'))}` | "
            f"`{_escape_md(row.get('expected_candidate_state'))}` / "
            f"`{_escape_md(row.get('expected_presentation_mode'))}` / "
            f"`{_escape_md(row.get('expected_problem_class'))}` | "
            f"`{_escape_md(row.get('observed_candidate_state'))}` / "
            f"`{_escape_md(row.get('observed_presentation_mode'))}` / "
            f"`{_escape_md(row.get('observed_problem_class'))}` | "
            f"`{_escape_md(row.get('expected_difficulty_band'))}` -> "
            f"`{_escape_md(row.get('observed_difficulty_band'))}` "
            f"(`{_escape_md(row.get('difficulty_status'))}`) | "
            f"`{_escape_md(row.get('expected_learner_difficulty'))}` -> "
            f"`{_escape_md(row.get('observed_current_difficulty_proxy'))}` | "
            f"{_escape_md(row.get('rationale'))} |"
        )
    lines.extend(["", "## Proficiency Samples", ""])
    for row in _mapping_rows(report.get("proficiency_reports")):
        difficulty_sample = _as_mapping(row.get("difficulty_summary_sample"))
        lines.extend(
            [
                f"### Proficiency `{row.get('proficiency')}`",
                "",
                f"- Sample difficulty: `{_compact_counts(difficulty_sample)}`",
                f"- Sample candidate states: `{_compact_counts(row.get('candidate_state_counts_sample'))}`",
                f"- Sample confidence: `{_compact_counts(row.get('classification_confidence_counts_sample'))}`",
                f"- Sample problem classes: `{_compact_counts(row.get('problem_class_counts_sample'))}`",
                "",
                "| Lemma | Diff | State | Class | POS | Rank | Score |",
                "| --- | ---: | --- | --- | --- | ---: | ---: |",
            ]
        )
        for sample in _mapping_rows(row.get("sample_rows"))[:MAX_MARKDOWN_SAMPLE_ROWS]:
            lines.append(
                "| "
                f"`{_escape_md(sample.get('lemma'))}` | "
                f"`{_escape_md(sample.get('difficulty_estimate'))}` | "
                f"`{_escape_md(sample.get('candidate_state'))}` | "
                f"`{_escape_md(sample.get('problem_class'))}` | "
                f"`{_escape_md(sample.get('pos'))}` | "
                f"`{_escape_md(sample.get('core_rank'))}` | "
                f"`{_escape_md(sample.get('profile_score'))}` |"
            )
        lines.append("")
    lines.extend(["## Challenge Target Samples", ""])
    for row in _mapping_rows(report.get("challenge_target_reports")):
        difficulty_active = _as_mapping(row.get("difficulty_summary_active"))
        lines.extend(
            [
                (
                    f"### Challenge `{row.get('challenge_target')}` "
                    f"at proficiency `{row.get('fixed_proficiency')}`"
                ),
                "",
                f"- Active difficulty: `{_compact_counts(difficulty_active)}`",
                (
                    "- Readiness center sources: "
                    f"`{_compact_counts(row.get('readiness_center_source_counts_active'))}`"
                ),
                "",
            ]
        )
    lines.extend(["## Findings", "", "| Level | Code | Message |", "| --- | --- | --- |"])
    for finding in _mapping_rows(report.get("findings")):
        lines.append(
            "| "
            f"`{_escape_md(finding.get('level'))}` | "
            f"`{_escape_md(finding.get('code'))}` | "
            f"{_escape_md(finding.get('message'))} |"
        )
    lines.append("")
    return "\n".join(lines)


def _append_label_metric_table(lines: list[str], title: str, value: object) -> None:
    metric = _as_mapping(value)
    by_label = _as_mapping(metric.get("by_label"))
    lines.extend(
        [
            f"#### {title} Precision/Recall",
            "",
            f"- Accuracy: `{metric.get('accuracy')}`",
            "",
            "| Label | TP | FP | FN | Precision | Recall |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for label in sorted(by_label):
        row = _as_mapping(by_label.get(label))
        lines.append(
            "| "
            f"`{_escape_md(label)}` | "
            f"`{_escape_md(row.get('true_positive'))}` | "
            f"`{_escape_md(row.get('false_positive'))}` | "
            f"`{_escape_md(row.get('false_negative'))}` | "
            f"`{_escape_md(row.get('precision'))}` | "
            f"`{_escape_md(row.get('recall'))}` |"
        )
    lines.append("")


def _difficulty_summary(
    rows: Sequence[Mapping[str, object]],
    *,
    key: str = "difficulty_estimate",
) -> dict[str, object]:
    values = [_safe_float(row.get(key)) for row in rows]
    filtered = [value for value in values if value is not None]
    if not filtered:
        return {"count": 0, "avg": None, "min": None, "max": None}
    return {
        "count": len(filtered),
        "avg": round(sum(filtered) / len(filtered), 6),
        "min": round(min(filtered), 6),
        "max": round(max(filtered), 6),
    }


def _difficulty_band_for_value(value: object) -> str:
    parsed = _safe_float(value)
    if parsed is None:
        return ""
    if parsed < DIFFICULTY_BAND_BEGINNER_MAX:
        return "beginner"
    if parsed < DIFFICULTY_BAND_INTERMEDIATE_MAX:
        return "intermediate"
    return "advanced"


def _difficulty_absolute_error(expected: object, observed: object) -> float | None:
    expected_value = _safe_float(expected)
    observed_value = _safe_float(observed)
    if expected_value is None or observed_value is None:
        return None
    return abs(expected_value - observed_value)


def _mean(values: Sequence[float]) -> float | None:
    if not values:
        return None
    return sum(float(value) for value in values) / len(values)


def _rmse(values: Sequence[float]) -> float | None:
    if not values:
        return None
    return (sum(float(value) ** 2 for value in values) / len(values)) ** 0.5


def _examples_by_key(
    rows: Sequence[Mapping[str, object]],
    *,
    key: str,
) -> dict[str, list[dict[str, object]]]:
    grouped: dict[str, list[dict[str, object]]] = {}
    for row in rows:
        value = str(row.get(key) or "unknown")
        bucket = grouped.setdefault(value, [])
        if len(bucket) >= MAX_EXAMPLES_PER_BUCKET:
            continue
        bucket.append(
            {
                "lemma": row.get("lemma"),
                "pos": row.get("pos"),
                "core_rank": row.get("core_rank"),
                "base_weight": row.get("base_weight"),
                "admission_weight": row.get("admission_weight"),
                "difficulty_proxy": row.get("current_difficulty_proxy"),
            }
        )
    return {key: grouped[key] for key in sorted(grouped)}


def _top_counter_rows(values: Sequence[str], *, limit: int = 20) -> dict[str, int]:
    counter = Counter(str(value or "unknown") for value in values)
    return dict(counter.most_common(limit))


def _learner_signal_source_counts(seed_rows: Sequence[Mapping[str, object]]) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for row in seed_rows:
        sources = row.get("learner_signal_sources")
        if isinstance(sources, Sequence) and not isinstance(sources, (str, bytes)):
            for source in sources:
                text = str(source or "").strip()
                if text:
                    counter[text] += 1
            if sources:
                continue
        counter["none"] += 1
    return dict(sorted(counter.items()))


def _counter_dict(values: Sequence[object]) -> dict[str, int]:
    return dict(sorted(Counter(str(value or "unknown") for value in values).items()))


def _compact_counts(value: object) -> str:
    if not isinstance(value, Mapping):
        return str(value)
    return ", ".join(f"{key}={value[key]}" for key in sorted(value))


def _finding(level: str, code: str, message: str) -> dict[str, str]:
    return {"level": level, "code": code, "message": message}


def _ratio(numerator: int, denominator: int) -> float | None:
    if denominator <= 0:
        return None
    return round(float(numerator) / float(denominator), 6)


def _pos_head(value: str) -> str:
    return str(value or "").split("-", 1)[0].strip() or "unknown"


def _parse_proficiency_levels(value: str) -> tuple[float, ...]:
    levels: list[float] = []
    for raw in str(value or "").split(","):
        text = raw.strip()
        if not text:
            continue
        try:
            levels.append(max(0.0, min(1.0, float(text))))
        except ValueError as exc:
            raise ValueError(f"Invalid proficiency level: {raw}") from exc
    if not levels:
        return DEFAULT_PROFICIENCY_LEVELS
    return tuple(levels)


def _mapping_rows(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _string_attr_or_metadata(
    seed: object,
    metadata: Mapping[str, object],
    *,
    attr: str,
    fallback: str,
) -> str:
    value = getattr(seed, attr, None)
    if value is None:
        value = metadata.get(attr)
    text = str(value or "").strip()
    return text or fallback


def _sequence_attr_or_metadata(
    seed: object,
    metadata: Mapping[str, object],
    *,
    attr: str,
    fallback: Sequence[str],
) -> tuple[str, ...]:
    value = getattr(seed, attr, None)
    if value is None:
        value = metadata.get(attr)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        normalized = tuple(str(item).strip() for item in value if str(item).strip())
        if normalized:
            return normalized
    text = str(value or "").strip()
    if text:
        return (text,)
    return tuple(fallback)


def _load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_path(path: Path) -> Path:
    return path.expanduser().resolve(strict=False)


def _repo_or_home_path(path: Path | None) -> str:
    if path is None:
        return ""
    resolved = Path(path).expanduser().resolve(strict=False)
    for root, label in (
        (PROJECT_ROOT, "."),
        (Path.home().resolve(strict=False), "~"),
    ):
        try:
            return str(Path(label) / resolved.relative_to(root))
        except ValueError:
            pass
    return str(resolved)


def _rounded_or_none(value: object) -> float | None:
    parsed = _safe_float(value)
    return round(parsed, 6) if parsed is not None else None


def _safe_float(value: object) -> float | None:
    try:
        if value is None:
            return None
        parsed = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    if parsed != parsed:
        return None
    return parsed


def _optional_str(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _escape_md(value: object) -> str:
    return str(value if value is not None else "").replace("|", "\\|").replace("\n", " ")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
