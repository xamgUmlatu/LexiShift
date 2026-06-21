from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import json
from pathlib import Path
import time
from typing import Optional, Sequence

from lexishift_core.lexicon.word_package import build_word_package
from lexishift_core.pos.normalization import normalize_pos
from lexishift_core.resources.dict_loaders import load_jmdict_lemmas
from lexishift_core.resources.japanese_learner_signals import (
    JAPANESE_LEARNER_SIGNALS_VERSION,
    build_japanese_learner_signal_bundle,
    load_japanese_lesson_vocabulary_index,
    load_jmdict_lexical_index,
    load_jmdict_priority_index,
    load_jmnedict_name_index,
    load_jlpt_vocabulary_index,
    load_kanjidic2_character_index,
    load_kanjivg_character_index,
)
from lexishift_core.resources.japanese_script import contains_kanji
from lexishift_core.frequency.sqlite_store import SqliteFrequencyConfig, SqliteFrequencyStore
from lexishift_core.srs.admission_features import normalize_topic_string_list
from lexishift_core.srs.admission_policy import (
    AdmissionPosWeights,
    POS_BUCKET_OTHER,
    compute_admission_weight,
    resolve_default_pos_weights,
)
from lexishift_core.srs.candidate_classification import (
    classify_srs_candidate,
)
from lexishift_core.srs.candidate_identity import (
    build_candidate_identity,
    candidate_identity_from_seed,
    candidate_identity_key_from_seed,
)
from lexishift_core.srs.pos_overlay import (
    PosOverlayEntry,
    load_pos_overlay_entries,
    lookup_pos_overlay_entry,
)
from lexishift_core.srs.seed_cache import (
    acquire_seed_frontier_cache_lock as _acquire_seed_frontier_cache_lock,
    cleanup_seed_frontier_cache,
    read_seed_frontier_cache_rows,
    release_seed_frontier_cache_lock as _release_seed_frontier_cache_lock,
    seed_frontier_cache_path as _seed_frontier_cache_path,
    seed_frontier_cache_status,
    write_seed_frontier_cache_rows,
)
from lexishift_core.srs.selector import SelectorCandidate
from lexishift_core.scoring.weighting import PmwWeighting


@dataclass(frozen=True)
class SeedWord:
    lemma: str
    language_pair: str
    word_package: Optional[dict[str, object]]
    core_rank: Optional[float]
    pos: Optional[str]
    pos_bucket: str
    pos_weight: float
    pmw: Optional[float]
    base_weight: float
    admission_weight: float
    metadata: dict[str, object]
    identity_key: str = ""
    candidate_state: str = "normal_vocab"
    presentation_mode: str = "vocab"
    problem_class: str = "normal_vocab"
    classification_confidence: str = "review"
    classification_reasons: Sequence[str] = ()
    admission_suitability: float = 1.0
    pos_raw: Optional[str] = None
    pos_canonical: Optional[str] = None
    pos_source_profile: Optional[str] = None
    pos_matched_rule: Optional[str] = None
    pos_mapped: bool = False


@dataclass(frozen=True)
class SeedSelectionConfig:
    language_pair: str = "en-ja"
    top_n: Optional[int] = None
    lemma_column: str = "lemma"
    rank_column: str = "core_rank"
    pmw_column: str = "pmw"
    pos_column: str = "pos"
    lform_column: str = "lform"
    wtype_column: str = "wtype"
    sublemma_column: str = "sublemma"
    pmw_weighting: PmwWeighting = PmwWeighting()
    admission_pos_weights: Optional[AdmissionPosWeights] = None
    sort_by_admission_weight: bool = True
    require_jmdict: bool = True
    jmdict_path: Optional[Path] = None
    jmnedict_path: Optional[Path] = None
    kanjidic2_path: Optional[Path] = None
    kanjivg_path: Optional[Path] = None
    jlpt_vocabulary_path: Optional[Path] = None
    lesson_vocabulary_path: Optional[Path] = None
    stopwords_path: Optional[Path] = None
    stopwords: Optional[set[str]] = None
    source_label: Optional[str] = None
    pos_overlay_path: Optional[Path] = None
    cache_dir: Optional[Path] = None
    apply_learner_signal_classification: bool = True
    topic_columns: Sequence[str] = (
        "sense_topics",
        "topics",
        "topic",
        "profile_topics",
    )


_JA_BOOTSTRAP_LEXICAL_EXCLUSIONS = frozenset(
    {
        "侭",
        "まま",
    }
)

_JA_BOOTSTRAP_ORTHOGRAPHIC_NORMALIZATION = {
    "為る": "する",
}


def build_seed_candidates(
    *,
    frequency_db: Path,
    config: SeedSelectionConfig,
) -> list[SeedWord]:
    if config.require_jmdict and not config.jmdict_path:
        raise ValueError("JMDict path is required when require_jmdict is True.")

    cache_path = _seed_frontier_cache_path(frequency_db=frequency_db, config=config)
    if cache_path is not None:
        cached = _load_seed_frontier_cache(cache_path=cache_path, config=config)
        if cached is not None:
            return cached
    lock_path: Path | None = None
    if cache_path is not None:
        lock_path = _acquire_seed_frontier_cache_lock(cache_path)
        cached = _load_seed_frontier_cache(cache_path=cache_path, config=config)
        if cached is not None:
            _release_seed_frontier_cache_lock(lock_path)
            return cached

    try:
        jmdict_lemmas = _load_jmdict_lemmas(config.jmdict_path) if config.require_jmdict else None
        jmdict_priority_index = _load_jmdict_priority_index(config.jmdict_path)
        jmdict_lexical_index = _load_jmdict_lexical_index(config.jmdict_path)
        jmnedict_name_index = _load_jmnedict_name_index(_resolve_jmnedict_path(config))
        kanjidic2_character_index = _load_kanjidic2_character_index(_resolve_kanjidic2_path(config))
        kanjivg_character_index = _load_kanjivg_character_index(_resolve_kanjivg_path(config))
        jlpt_vocabulary_index = _load_jlpt_vocabulary_index(_resolve_jlpt_vocabulary_path(config))
        lesson_vocabulary_index = _load_japanese_lesson_vocabulary_index(
            _resolve_lesson_vocabulary_path(config)
        )
        stopwords = _resolve_stopwords(config)
        source_label = _resolve_source_label(config=config, frequency_db=frequency_db)
        pos_overlay_entries = load_pos_overlay_entries(config.pos_overlay_path)
        store_config = SqliteFrequencyConfig(
            path=frequency_db,
            lemma_column=config.lemma_column,
            rank_column=config.rank_column,
            pmw_column=config.pmw_column,
        )
        with SqliteFrequencyStore(store_config) as store:
            available_columns = store.column_names()
            resolved_lemma_column = store.resolve_column(
                config.lemma_column,
                available_columns=available_columns,
            )
            if not resolved_lemma_column:
                raise ValueError(
                    f"Missing lemma column '{config.lemma_column}' in frequency DB: {frequency_db}"
                )
            resolved_rank_column = store.resolve_rank_column(
                config.rank_column,
                available_columns=available_columns,
            )
            resolved_pmw_column = store.resolve_frequency_column(
                config.pmw_column,
                available_columns=available_columns,
            )
            resolved_pos_column = store.resolve_column(
                config.pos_column,
                available_columns=available_columns,
            )
            resolved_lform_column = store.resolve_column(
                config.lform_column,
                available_columns=available_columns,
            )
            resolved_wtype_column = store.resolve_column(
                config.wtype_column,
                available_columns=available_columns,
            )
            resolved_sublemma_column = store.resolve_column(
                config.sublemma_column,
                available_columns=available_columns,
            )
            resolved_topic_columns = tuple(
                dict.fromkeys(
                    column
                    for column in (
                        store.resolve_column(topic_column, available_columns=available_columns)
                        for topic_column in config.topic_columns
                    )
                    if column
                )
            )
            resolved_frequency_profile_columns = _source_frequency_profile_columns(
                available_columns=available_columns
            )
            include_pos = bool(resolved_pos_column)
            include_lform = bool(resolved_lform_column)
            include_wtype = bool(resolved_wtype_column)
            include_sublemma = bool(resolved_sublemma_column)
            selected_columns = list(
                dict.fromkeys(
                    column
                    for column in (
                        resolved_pos_column,
                        resolved_lform_column,
                        resolved_wtype_column,
                        resolved_sublemma_column,
                        *resolved_topic_columns,
                        *resolved_frequency_profile_columns,
                    )
                    if column
                )
            )
            resolved_pos_weights = config.admission_pos_weights or resolve_default_pos_weights(
                language_pair=config.language_pair
            )
            max_pmw = store.max_value(resolved_pmw_column) if resolved_pmw_column else None
            results: list[SeedWord] = []
            for row_index, row in enumerate(
                store.iter_top_by_rank(
                    limit=config.top_n,
                    rank_column=resolved_rank_column,
                    pmw_column=resolved_pmw_column,
                    columns=selected_columns,
                ),
                start=1,
            ):
                lemma = str(row[resolved_lemma_column]).strip()
                if not lemma:
                    continue
                if stopwords and lemma in stopwords:
                    continue
                if jmdict_lemmas is not None and lemma not in jmdict_lemmas:
                    continue
                columns = row.keys()
                core_rank = (
                    _safe_float(row[resolved_rank_column])
                    if resolved_rank_column and resolved_rank_column in columns
                    else None
                )
                pmw = (
                    _safe_float(row[resolved_pmw_column])
                    if resolved_pmw_column and resolved_pmw_column in columns
                    else None
                )
                raw_pos = (
                    str(row[resolved_pos_column]).strip()
                    if include_pos
                    and resolved_pos_column in columns
                    and row[resolved_pos_column] is not None
                    else None
                )
                frequency_normalized_pos = normalize_pos(
                    raw_pos,
                    language_pair=config.language_pair,
                    source_provider=source_label,
                    source_kind="frequency",
                )
                pos_overlay_entry = lookup_pos_overlay_entry(pos_overlay_entries, lemma)
                raw_pos, normalized_pos, pos_source_metadata = _resolve_effective_pos(
                    raw_pos=raw_pos,
                    frequency_normalized_pos=frequency_normalized_pos,
                    overlay_entry=pos_overlay_entry,
                    language_pair=config.language_pair,
                )
                raw_lform = (
                    str(row[resolved_lform_column]).strip()
                    if include_lform
                    and resolved_lform_column in columns
                    and row[resolved_lform_column] is not None
                    else None
                )
                raw_wtype = (
                    str(row[resolved_wtype_column]).strip()
                    if include_wtype
                    and resolved_wtype_column in columns
                    and row[resolved_wtype_column] is not None
                    else None
                )
                raw_sublemma = (
                    str(row[resolved_sublemma_column]).strip()
                    if include_sublemma
                    and resolved_sublemma_column in columns
                    and row[resolved_sublemma_column] is not None
                    else None
                )
                if _should_exclude_bootstrap_lemma(
                    language_pair=config.language_pair,
                    lemma=lemma,
                ):
                    continue
                normalized_lemma, script_forms_override, bootstrap_metadata = (
                    _apply_bootstrap_surface_policy(
                        language_pair=config.language_pair,
                        lemma=lemma,
                    )
                )
                topic_metadata = _extract_seed_topic_metadata(
                    row,
                    topic_columns=resolved_topic_columns,
                )
                source_frequency_metadata = _extract_source_frequency_metadata(
                    row,
                    profile_columns=resolved_frequency_profile_columns,
                )
                learner_signal_metadata = _extract_learner_signal_metadata(
                    language_pair=config.language_pair,
                    lemma=normalized_lemma,
                    reading=raw_lform,
                    raw_pos=raw_pos,
                    wtype=raw_wtype,
                    source_frequency_profile=source_frequency_metadata.get(
                        "source_frequency_profile"
                    ),
                    jmdict_priority_index=jmdict_priority_index,
                    jmdict_lexical_index=jmdict_lexical_index,
                    jmnedict_name_index=jmnedict_name_index,
                    kanjidic2_character_index=kanjidic2_character_index,
                    kanjivg_character_index=kanjivg_character_index,
                    jlpt_vocabulary_index=jlpt_vocabulary_index,
                    lesson_vocabulary_index=lesson_vocabulary_index,
                )
                word_package_learner_signal_metadata = {
                    key: value
                    for key, value in learner_signal_metadata.items()
                    if key != "learner_signals"
                }
                if stopwords and normalized_lemma in stopwords:
                    continue
                if _should_exclude_bootstrap_lemma(
                    language_pair=config.language_pair,
                    lemma=normalized_lemma,
                ):
                    continue
                classification = classify_srs_candidate(
                    language_pair=config.language_pair,
                    lemma=normalized_lemma,
                    raw_pos=raw_pos,
                    learner_signals=learner_signal_metadata.get("learner_signals"),
                    apply_learner_signal_recommendations=(
                        config.apply_learner_signal_classification
                    ),
                )
                classification_payload = classification.to_dict()
                candidate_identity = build_candidate_identity(
                    language_pair=config.language_pair,
                    surface=normalized_lemma,
                    reading=raw_lform or normalized_lemma,
                    pos=raw_pos,
                    source_provider=source_label,
                    row_index=row_index,
                    row_rank=core_rank,
                )
                candidate_identity_key = str(candidate_identity.get("key") or "").strip()
                word_package = build_word_package(
                    language_pair=config.language_pair,
                    surface=normalized_lemma,
                    reading=raw_lform or normalized_lemma,
                    source_provider=source_label,
                    script_forms=script_forms_override,
                    pos=raw_pos,
                    pos_raw=raw_pos,
                    pos_canonical=normalized_pos.canonical,
                    wtype=raw_wtype,
                    sublemma=raw_sublemma,
                    core_rank=core_rank,
                    pmw=pmw,
                    lform_raw=raw_lform,
                    row_index=row_index,
                    row_rank=core_rank,
                    source_extra={
                        "rank_column": resolved_rank_column,
                        "pmw_column": resolved_pmw_column,
                        "lemma_column": resolved_lemma_column,
                        "pos_column": resolved_pos_column if include_pos else None,
                        "lform_column": resolved_lform_column if include_lform else None,
                        "wtype_column": resolved_wtype_column if include_wtype else None,
                        "sublemma_column": resolved_sublemma_column if include_sublemma else None,
                        "candidate_identity_key": candidate_identity_key,
                        "candidate_identity_version": candidate_identity.get("version"),
                        **classification_payload,
                        **pos_source_metadata,
                        **bootstrap_metadata,
                        **source_frequency_metadata,
                        **word_package_learner_signal_metadata,
                    },
                )
                base_weight = config.pmw_weighting.normalize(pmw, max_value=max_pmw)
                canonical_pos_for_admission = (
                    normalized_pos.canonical if normalized_pos.mapped else None
                )
                pos_bucket, pos_weight, admission_weight = compute_admission_weight(
                    language_pair=config.language_pair,
                    raw_pos=raw_pos,
                    canonical_pos=canonical_pos_for_admission,
                    base_weight=base_weight,
                    pos_weights=resolved_pos_weights,
                )
                results.append(
                    SeedWord(
                        lemma=normalized_lemma,
                        language_pair=config.language_pair,
                        identity_key=candidate_identity_key,
                        word_package=word_package,
                        core_rank=core_rank,
                        pos=raw_pos,
                        pos_bucket=pos_bucket,
                        pos_weight=pos_weight,
                        pmw=pmw,
                        base_weight=base_weight,
                        admission_weight=admission_weight,
                        metadata={
                            "source": source_label,
                            "pos_raw": raw_pos,
                            "pos_canonical": normalized_pos.canonical,
                            "pos_mapped": normalized_pos.mapped,
                            "pos_source_profile": normalized_pos.source_profile,
                            "pos_matched_rule": normalized_pos.matched_rule,
                            **pos_source_metadata,
                            "rank_column": resolved_rank_column,
                            "pmw_column": resolved_pmw_column,
                            "pos_column": resolved_pos_column if include_pos else None,
                            "lform_column": resolved_lform_column if include_lform else None,
                            "wtype_column": resolved_wtype_column if include_wtype else None,
                            "sublemma_column": resolved_sublemma_column
                            if include_sublemma
                            else None,
                            "candidate_identity_key": candidate_identity_key,
                            "candidate_identity": candidate_identity,
                            "pos_bucket": pos_bucket,
                            "pos_weight": pos_weight,
                            "admission_weight": admission_weight,
                            **classification_payload,
                            **bootstrap_metadata,
                            **source_frequency_metadata,
                            **learner_signal_metadata,
                            **topic_metadata,
                        },
                        candidate_state=classification.candidate_state,
                        presentation_mode=classification.presentation_mode,
                        problem_class=classification.problem_class,
                        classification_confidence=classification.confidence,
                        classification_reasons=tuple(classification.reasons),
                        admission_suitability=classification.admission_suitability,
                        pos_raw=raw_pos,
                        pos_canonical=normalized_pos.canonical,
                        pos_source_profile=normalized_pos.source_profile,
                        pos_matched_rule=normalized_pos.matched_rule,
                        pos_mapped=normalized_pos.mapped,
                    )
                )
            if config.sort_by_admission_weight:
                results.sort(key=_admission_sort_key)
            if cache_path is not None and lock_path is not None:
                _write_seed_frontier_cache(
                    cache_path=cache_path,
                    seeds=results,
                    config=config,
                )
            return results
    finally:
        _release_seed_frontier_cache_lock(lock_path)


def _load_seed_frontier_cache(
    *,
    cache_path: Path,
    config: SeedSelectionConfig,
) -> list[SeedWord] | None:
    rows = read_seed_frontier_cache_rows(cache_path)
    if rows is None:
        return None
    return [_seed_from_cache_row(row, language_pair=config.language_pair) for row in rows]


def _load_jmdict_priority_index(path: Optional[Path]):
    if path is None or not Path(path).is_file():
        return {}
    return load_jmdict_priority_index(Path(path))


def _load_jmdict_lexical_index(path: Optional[Path]):
    if path is None or not Path(path).is_file():
        return {}
    return load_jmdict_lexical_index(Path(path))


def _load_kanjidic2_character_index(path: Optional[Path]):
    if path is None or not Path(path).is_file():
        return {}
    return load_kanjidic2_character_index(Path(path))


def _load_jmnedict_name_index(path: Optional[Path]):
    if path is None or not Path(path).is_file():
        return {}
    return load_jmnedict_name_index(Path(path))


def _load_kanjivg_character_index(path: Optional[Path]):
    if path is None or not Path(path).is_file():
        return {}
    return load_kanjivg_character_index(Path(path))


def _load_jlpt_vocabulary_index(path: Optional[Path]):
    if path is None or not Path(path).exists():
        return {}
    return load_jlpt_vocabulary_index(Path(path))


def _load_japanese_lesson_vocabulary_index(path: Optional[Path]):
    if path is None or not Path(path).exists():
        return {}
    return load_japanese_lesson_vocabulary_index(Path(path))


def _resolve_jmnedict_path(config: SeedSelectionConfig) -> Optional[Path]:
    if config.jmnedict_path is not None:
        return Path(config.jmnedict_path)
    jmdict_path = config.jmdict_path
    if jmdict_path is None:
        return None
    candidate_roots = tuple(
        dict.fromkeys(
            candidate
            for candidate in (
                Path(jmdict_path).parent,
                Path(jmdict_path).parent.parent,
            )
            if str(candidate)
        )
    )
    for root in candidate_roots:
        for candidate in (
            root / "jmnedict-ja" / "JMnedict.xml",
            root / "jmnedict-ja" / "JMnedict.xml.gz",
            root / "JMnedict.xml",
            root / "JMnedict.xml.gz",
        ):
            if candidate.is_file():
                return candidate
    return None


def _resolve_kanjivg_path(config: SeedSelectionConfig) -> Optional[Path]:
    if config.kanjivg_path is not None:
        return Path(config.kanjivg_path)
    jmdict_path = config.jmdict_path
    if jmdict_path is None:
        return None
    candidate_roots = tuple(
        dict.fromkeys(
            candidate
            for candidate in (
                Path(jmdict_path).parent,
                Path(jmdict_path).parent.parent,
            )
            if str(candidate)
        )
    )
    for root in candidate_roots:
        for candidate in (
            root / "kanjivg-ja" / "kanjivg-20250816.xml",
            root / "kanjivg-ja" / "kanjivg.xml",
            root / "kanjivg-ja" / "kanjivg.xml.gz",
            root / "kanjivg-20250816.xml",
            root / "kanjivg.xml",
            root / "kanjivg.xml.gz",
        ):
            if candidate.is_file():
                return candidate
    return None


def _resolve_jlpt_vocabulary_path(config: SeedSelectionConfig) -> Optional[Path]:
    if config.jlpt_vocabulary_path is not None:
        return Path(config.jlpt_vocabulary_path)
    jmdict_path = config.jmdict_path
    if jmdict_path is None:
        return None
    candidate_roots = _japanese_optional_signal_roots(jmdict_path)
    for root in candidate_roots:
        for candidate in (
            root / "jlpt-tanos-vocab-ja" / "JLPT_vocab_ALL.csv",
            root / "jlpt-tanos-vocab-ja" / "JLPT_vocab_ALL.json",
            root / "JLPT_vocab_ALL.csv",
            root / "JLPT_vocab_ALL.json",
        ):
            if candidate.is_file():
                return candidate
    return None


def _resolve_lesson_vocabulary_path(config: SeedSelectionConfig) -> Optional[Path]:
    if config.lesson_vocabulary_path is not None:
        return Path(config.lesson_vocabulary_path)
    jmdict_path = config.jmdict_path
    if jmdict_path is None:
        return None
    candidate_roots = _japanese_optional_signal_roots(jmdict_path)
    for root in candidate_roots:
        for candidate in (
            root / "sbsjapanese1-ja",
            root / "sbsjapanese1-ja" / "EPUB",
            root / "sbsjapanese1",
            root / "sbsjapanese1" / "EPUB",
        ):
            if candidate.exists():
                return candidate
    return None


def _resolve_kanjidic2_path(config: SeedSelectionConfig) -> Optional[Path]:
    if config.kanjidic2_path is not None:
        return Path(config.kanjidic2_path)
    jmdict_path = config.jmdict_path
    if jmdict_path is None:
        return None
    candidate_roots = tuple(
        dict.fromkeys(
            candidate
            for candidate in (
                Path(jmdict_path).parent,
                Path(jmdict_path).parent.parent,
            )
            if str(candidate)
        )
    )
    for root in candidate_roots:
        for candidate in (
            root / "kanjidic2-ja" / "kanjidic2.xml",
            root / "kanjidic2-ja" / "kanjidic2.xml.gz",
            root / "kanjidic2.xml",
            root / "kanjidic2.xml.gz",
        ):
            if candidate.is_file():
                return candidate
    return None


def _japanese_optional_signal_roots(jmdict_path: Path) -> tuple[Path, ...]:
    return tuple(
        dict.fromkeys(
            candidate
            for candidate in (
                Path(jmdict_path).parent,
                Path(jmdict_path).parent.parent,
            )
            if str(candidate)
        )
    )


def _extract_learner_signal_metadata(
    *,
    language_pair: str,
    lemma: str,
    reading: object | None = None,
    raw_pos: object | None = None,
    wtype: object | None = None,
    source_frequency_profile: object | None = None,
    jmdict_priority_index,
    jmdict_lexical_index,
    jmnedict_name_index,
    kanjidic2_character_index,
    kanjivg_character_index,
    jlpt_vocabulary_index,
    lesson_vocabulary_index,
) -> dict[str, object]:
    if str(language_pair or "").strip().lower() != "en-ja":
        return {}
    learner_signals = build_japanese_learner_signal_bundle(
        lemma=lemma,
        reading=reading,
        raw_pos=raw_pos,
        wtype=wtype,
        source_frequency_profile=(
            source_frequency_profile if isinstance(source_frequency_profile, dict) else None
        ),
        jmdict_priority_index=jmdict_priority_index,
        jmdict_lexical_index=jmdict_lexical_index,
        jmnedict_name_index=jmnedict_name_index,
        kanjidic2_character_index=kanjidic2_character_index,
        kanjivg_character_index=kanjivg_character_index,
        jlpt_vocabulary_index=jlpt_vocabulary_index,
        lesson_vocabulary_index=lesson_vocabulary_index,
    )
    if not learner_signals:
        return {
            "learner_signal_version": JAPANESE_LEARNER_SIGNALS_VERSION,
            "learner_signal_sources": [],
        }
    return {
        "learner_signal_version": learner_signals.get("version"),
        "learner_signal_sources": list(learner_signals.get("sources", ()) or ()),
        "learner_signals": learner_signals,
    }


def _source_frequency_profile_columns(*, available_columns: Sequence[str]) -> tuple[str, ...]:
    columns: list[str] = []
    for column in available_columns:
        lowered = str(column or "").strip().lower()
        if not lowered:
            continue
        if lowered in {"rank", "core_rank", "pmw", "core_pmw", "frequency", "core_frequency"}:
            columns.append(str(column))
            continue
        if lowered.endswith(("_rank", "_pmw", "_frequency")):
            columns.append(str(column))
    return tuple(dict.fromkeys(columns))


def _extract_source_frequency_metadata(
    row,
    *,
    profile_columns: Sequence[str],
) -> dict[str, object]:
    if not profile_columns:
        return {}
    row_columns = row.keys()
    rank_values: list[float] = []
    pmw_values: list[float] = []
    frequency_values: list[float] = []
    domain_rank_values: list[float] = []
    fixed_rank_values: list[float] = []
    variable_rank_values: list[float] = []
    known_columns: list[str] = []
    for column in profile_columns:
        if column not in row_columns:
            continue
        value = _safe_float(row[column])
        if value is None:
            continue
        lowered = str(column or "").strip().lower()
        known_columns.append(column)
        if lowered.endswith("_rank") or lowered == "rank":
            rank_values.append(value)
            if lowered not in {"rank", "core_rank"}:
                domain_rank_values.append(value)
            if "_fixed_" in lowered:
                fixed_rank_values.append(value)
            elif "_variable_" in lowered:
                variable_rank_values.append(value)
        elif lowered.endswith("_pmw") or lowered == "pmw":
            pmw_values.append(value)
        elif lowered.endswith("_frequency") or lowered == "frequency":
            frequency_values.append(value)
    profile: dict[str, object] = {
        "version": 1,
        "column_count": len(profile_columns),
        "known_column_count": len(known_columns),
        "known_columns_sample": known_columns[:24],
    }
    profile.update(_numeric_profile(prefix="rank", values=rank_values))
    profile.update(_numeric_profile(prefix="domain_rank", values=domain_rank_values))
    profile.update(_numeric_profile(prefix="pmw", values=pmw_values))
    profile.update(_numeric_profile(prefix="frequency", values=frequency_values))
    profile.update(_numeric_profile(prefix="fixed_rank", values=fixed_rank_values))
    profile.update(_numeric_profile(prefix="variable_rank", values=variable_rank_values))
    if fixed_rank_values and variable_rank_values:
        profile["fixed_variable_rank_delta"] = round(
            _mean_float(variable_rank_values) - _mean_float(fixed_rank_values),
            6,
        )
    return {"source_frequency_profile": profile}


def _numeric_profile(*, prefix: str, values: Sequence[float]) -> dict[str, object]:
    if not values:
        return {f"{prefix}_known_count": 0}
    minimum = min(values)
    maximum = max(values)
    return {
        f"{prefix}_known_count": len(values),
        f"{prefix}_min": round(minimum, 6),
        f"{prefix}_max": round(maximum, 6),
        f"{prefix}_mean": round(_mean_float(values), 6),
        f"{prefix}_spread": round(maximum - minimum, 6),
    }


def _mean_float(values: Sequence[float]) -> float:
    if not values:
        return 0.0
    return float(sum(values) / len(values))


def prepare_seed_frontier_cache(
    *,
    frequency_db: Path,
    config: SeedSelectionConfig,
    cleanup: bool = True,
) -> dict[str, object]:
    started_at = time.perf_counter()
    seeds = build_seed_candidates(frequency_db=frequency_db, config=config)
    cache_path = _seed_frontier_cache_path(frequency_db=frequency_db, config=config)
    cleanup_payload: dict[str, object] = {}
    if cleanup and cache_path is not None:
        cleanup_payload = cleanup_seed_frontier_cache(
            cache_dir=Path(config.cache_dir) if config.cache_dir else None,
            pair=config.language_pair,
            active_cache_path=cache_path,
        )
    status = seed_frontier_cache_status(frequency_db=frequency_db, config=config)
    status.update(
        {
            "prepared": True,
            "seed_count": len(seeds),
            "duration_ms": round((time.perf_counter() - started_at) * 1000.0, 3),
            "cleanup": cleanup_payload,
        }
    )
    return status


def _write_seed_frontier_cache(
    *,
    cache_path: Path,
    seeds: Sequence[SeedWord],
    config: SeedSelectionConfig,
) -> None:
    write_seed_frontier_cache_rows(
        cache_path=cache_path,
        rows=[_seed_to_cache_row(seed) for seed in seeds],
        config=config,
    )


def _seed_to_cache_row(seed: SeedWord) -> dict[str, object]:
    candidate_identity = candidate_identity_from_seed(seed)
    return {
        "lemma": seed.lemma,
        "language_pair": seed.language_pair,
        "identity_key": seed.identity_key or str(candidate_identity.get("key") or "").strip(),
        "candidate_identity": _json_safe(candidate_identity),
        "word_package": _json_safe(seed.word_package),
        "core_rank": seed.core_rank,
        "pos": seed.pos,
        "pos_bucket": seed.pos_bucket,
        "pos_weight": seed.pos_weight,
        "pmw": seed.pmw,
        "base_weight": seed.base_weight,
        "admission_weight": seed.admission_weight,
        "metadata": _json_safe(seed.metadata),
        "candidate_state": seed.candidate_state,
        "presentation_mode": seed.presentation_mode,
        "problem_class": seed.problem_class,
        "classification_confidence": seed.classification_confidence,
        "classification_reasons": list(seed.classification_reasons),
        "admission_suitability": seed.admission_suitability,
        "pos_raw": seed.pos_raw,
        "pos_canonical": seed.pos_canonical,
        "pos_source_profile": seed.pos_source_profile,
        "pos_matched_rule": seed.pos_matched_rule,
        "pos_mapped": seed.pos_mapped,
    }


def _seed_from_cache_row(row: object, *, language_pair: str) -> SeedWord:
    if not isinstance(row, dict):
        raise ValueError("Invalid seed frontier cache row.")
    lemma = str(row.get("lemma") or "").strip()
    if not lemma:
        raise ValueError("Invalid seed frontier cache row without lemma.")
    metadata = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
    word_package = row.get("word_package") if isinstance(row.get("word_package"), dict) else None
    classification_reasons = row.get("classification_reasons")
    if not isinstance(classification_reasons, list):
        classification_reasons = []
    admission_suitability = _safe_float(row.get("admission_suitability"))
    if admission_suitability is None:
        admission_suitability = 1.0
    identity_key = str(row.get("identity_key") or "").strip()
    candidate_identity = row.get("candidate_identity")
    if not identity_key and isinstance(candidate_identity, dict):
        identity_key = str(candidate_identity.get("key") or "").strip()
    return SeedWord(
        lemma=lemma,
        language_pair=str(row.get("language_pair") or language_pair),
        identity_key=identity_key,
        word_package=word_package,
        core_rank=_safe_float(row.get("core_rank")),
        pos=_optional_text(row.get("pos")),
        pos_bucket=str(row.get("pos_bucket") or POS_BUCKET_OTHER),
        pos_weight=_safe_float(row.get("pos_weight")) or 0.0,
        pmw=_safe_float(row.get("pmw")),
        base_weight=_safe_float(row.get("base_weight")) or 0.0,
        admission_weight=_safe_float(row.get("admission_weight")) or 0.0,
        metadata=metadata,
        candidate_state=str(row.get("candidate_state") or "normal_vocab"),
        presentation_mode=str(row.get("presentation_mode") or "vocab"),
        problem_class=str(row.get("problem_class") or "normal_vocab"),
        classification_confidence=str(row.get("classification_confidence") or "review"),
        classification_reasons=tuple(str(item) for item in classification_reasons),
        admission_suitability=admission_suitability,
        pos_raw=_optional_text(row.get("pos_raw")),
        pos_canonical=_optional_text(row.get("pos_canonical")),
        pos_source_profile=_optional_text(row.get("pos_source_profile")),
        pos_matched_rule=_optional_text(row.get("pos_matched_rule")),
        pos_mapped=bool(row.get("pos_mapped")),
    )


def _json_safe(value: object) -> object:
    return json.loads(json.dumps(value, ensure_ascii=False, default=str))


def _optional_text(value: object) -> Optional[str]:
    text = str(value or "").strip()
    return text or None


def _resolve_effective_pos(
    *,
    raw_pos: str | None,
    frequency_normalized_pos,
    overlay_entry: PosOverlayEntry | None,
    language_pair: str,
):
    frequency_raw_pos = raw_pos
    if raw_pos and frequency_normalized_pos.mapped:
        return (
            raw_pos,
            frequency_normalized_pos,
            {
                "pos_source_kind": "frequency",
                "frequency_pos_raw": frequency_raw_pos,
            },
        )
    if overlay_entry is None:
        return (
            raw_pos,
            frequency_normalized_pos,
            {
                "pos_source_kind": "frequency",
                "frequency_pos_raw": frequency_raw_pos,
            },
        )
    overlay_normalized_pos = normalize_pos(
        overlay_entry.raw_pos,
        language_pair=language_pair,
        source_provider=overlay_entry.source_provider,
        source_kind="pos_overlay",
        source_profile=overlay_entry.pos_source_profile,
    )
    if not overlay_normalized_pos.mapped:
        return (
            raw_pos,
            frequency_normalized_pos,
            {
                "pos_source_kind": "frequency",
                "frequency_pos_raw": frequency_raw_pos,
                "pos_overlay_id": overlay_entry.overlay_id,
                "pos_overlay_raw_pos": overlay_entry.raw_pos,
                "pos_overlay_mapped": False,
            },
        )
    return (
        overlay_entry.raw_pos,
        overlay_normalized_pos,
        {
            "pos_source_kind": "pos_overlay",
            "frequency_pos_raw": frequency_raw_pos,
            "pos_overlay_id": overlay_entry.overlay_id,
            "pos_overlay_provider": overlay_entry.source_provider,
            "pos_overlay_raw_pos": overlay_entry.raw_pos,
            "pos_overlay_confidence": overlay_entry.confidence,
            "pos_overlay_source_count": overlay_entry.source_count,
            "pos_overlay_total_count": overlay_entry.total_count,
            "pos_overlay_mapped": True,
        },
    )


def seed_to_selector_candidates(seeds: Sequence[SeedWord]) -> list[SelectorCandidate]:
    candidates: list[SelectorCandidate] = []
    for seed in seeds:
        pos_raw = getattr(seed, "pos_raw", None)
        pos_canonical = getattr(seed, "pos_canonical", None)
        pos_mapped = bool(getattr(seed, "pos_mapped", False))
        pos_source_profile = getattr(seed, "pos_source_profile", None)
        pos_matched_rule = getattr(seed, "pos_matched_rule", None)
        seed_metadata = getattr(seed, "metadata", None)
        if not isinstance(seed_metadata, dict):
            seed_metadata = {}
        suitability_raw = getattr(seed, "admission_suitability", None)
        if suitability_raw is None:
            suitability_raw = seed_metadata.get("admission_suitability", 1.0)
        try:
            admission_suitability = float(suitability_raw)
        except (TypeError, ValueError):
            admission_suitability = 1.0
        metadata = {
            "candidate_identity_key": candidate_identity_key_from_seed(seed),
            "core_rank": seed.core_rank,
            "pos": seed.pos,
            "pos_raw": pos_raw if pos_raw is not None else seed.pos,
            "pos_canonical": pos_canonical,
            "pos_mapped": pos_mapped,
            "pos_source_profile": pos_source_profile,
            "pos_matched_rule": pos_matched_rule,
            "pos_bucket": seed.pos_bucket,
            "pos_weight": seed.pos_weight,
            "pmw": seed.pmw,
            "base_weight": seed.base_weight,
            "admission_weight": seed.admission_weight,
            "candidate_state": getattr(seed, "candidate_state", "normal_vocab"),
            "presentation_mode": getattr(seed, "presentation_mode", "vocab"),
            "problem_class": getattr(seed, "problem_class", "normal_vocab"),
            "classification_confidence": getattr(seed, "classification_confidence", "review"),
            "classification_reasons": list(getattr(seed, "classification_reasons", ())),
            "admission_suitability": admission_suitability,
            **seed_metadata,
        }
        word_package = getattr(seed, "word_package", None)
        if word_package:
            metadata["word_package"] = word_package
        candidates.append(
            SelectorCandidate(
                lemma=seed.lemma,
                language_pair=seed.language_pair,
                base_freq=seed.admission_weight,
                admission_suitability=admission_suitability,
                confidence=seed.admission_weight,
                pos=seed.pos_bucket,
                metadata=metadata,
            )
        )
    return candidates


def _load_jmdict_lemmas(path: Optional[Path]) -> Optional[frozenset[str]]:
    if not path:
        return None
    resolved = Path(path).resolve()
    try:
        stat = resolved.stat()
    except OSError:
        return frozenset()
    return _load_jmdict_lemmas_cached(
        str(resolved),
        int(stat.st_mtime_ns),
        int(stat.st_size),
    )


@lru_cache(maxsize=8)
def _load_jmdict_lemmas_cached(
    path: str,
    mtime_ns: int,
    size: int,
) -> frozenset[str]:
    del mtime_ns, size
    return frozenset(load_jmdict_lemmas(Path(path)))


def _safe_float(value) -> Optional[float]:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _extract_seed_topic_metadata(
    row,
    *,
    topic_columns: Sequence[str],
) -> dict[str, list[str]]:
    row_columns = row.keys()
    topic_metadata: dict[str, list[str]] = {}
    for column in topic_columns:
        if column not in row_columns:
            continue
        normalized_topics = normalize_topic_string_list(row[column])
        if normalized_topics:
            topic_metadata[column] = normalized_topics
    return topic_metadata


def _resolve_stopwords(config: SeedSelectionConfig) -> set[str]:
    if config.stopwords is not None:
        return {str(item).strip() for item in config.stopwords if str(item).strip()}
    if not config.stopwords_path:
        return set()
    return _load_stopwords(config.stopwords_path)


def _load_stopwords(path: Path) -> set[str]:
    if not path.exists() or not path.is_file():
        return set()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"Could not read stopwords file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid stopwords JSON: {path}") from exc
    if not isinstance(payload, list):
        raise ValueError(f"Invalid stopwords format in {path}: expected a JSON array of strings.")
    stopwords: set[str] = set()
    for index, item in enumerate(payload):
        if not isinstance(item, str):
            raise ValueError(f"Invalid stopwords format in {path}: item #{index} is not a string.")
        value = item.strip()
        if not value:
            raise ValueError(f"Invalid stopwords format in {path}: item #{index} is empty.")
        stopwords.add(value)
    return stopwords


def _admission_sort_key(item: SeedWord) -> tuple[float, float, float, str]:
    rank = item.core_rank if item.core_rank is not None else float("inf")
    return (-item.admission_weight, -item.base_weight, rank, item.lemma)


def _resolve_source_label(*, config: SeedSelectionConfig, frequency_db: Path) -> str:
    configured = str(config.source_label or "").strip()
    if configured:
        return configured
    stem = str(frequency_db.stem or "").strip()
    if stem:
        return stem
    return "frequency"


def _target_language_from_pair(pair: str) -> str:
    normalized = str(pair or "").strip().lower()
    _source, separator, target = normalized.partition("-")
    if not separator:
        return ""
    return target.strip()


def _should_exclude_bootstrap_lemma(*, language_pair: str, lemma: str) -> bool:
    if _target_language_from_pair(language_pair) != "ja":
        return False
    return str(lemma or "").strip() in _JA_BOOTSTRAP_LEXICAL_EXCLUSIONS


def _apply_bootstrap_surface_policy(
    *,
    language_pair: str,
    lemma: str,
) -> tuple[str, Optional[dict[str, str]], dict[str, object]]:
    if _target_language_from_pair(language_pair) != "ja":
        return lemma, None, {}
    source_surface = str(lemma or "").strip()
    normalized_surface = _JA_BOOTSTRAP_ORTHOGRAPHIC_NORMALIZATION.get(
        source_surface,
        source_surface,
    )
    if normalized_surface == source_surface:
        return normalized_surface, None, {}
    script_forms: Optional[dict[str, str]] = None
    if contains_kanji(source_surface):
        script_forms = {"kanji": source_surface}
    return (
        normalized_surface,
        script_forms,
        {
            "source_surface_original": source_surface,
            "surface_normalized_from": source_surface,
            "surface_normalization_rule": (
                f"ja_manual_bootstrap_surface_map:{source_surface}->{normalized_surface}"
            ),
        },
    )
