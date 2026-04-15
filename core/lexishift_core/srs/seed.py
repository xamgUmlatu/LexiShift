from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Optional, Sequence

from lexishift_core.lexicon.word_package import build_word_package
from lexishift_core.pos.normalization import normalize_pos
from lexishift_core.resources.dict_loaders import load_jmdict_lemmas
from lexishift_core.resources.japanese_script import contains_kanji
from lexishift_core.frequency.sqlite_store import SqliteFrequencyConfig, SqliteFrequencyStore
from lexishift_core.srs.admission_features import normalize_topic_string_list
from lexishift_core.srs.admission_policy import (
    AdmissionPosWeights,
    compute_admission_weight,
    resolve_default_pos_weights,
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
    pos_raw: Optional[str] = None
    pos_canonical: Optional[str] = None
    pos_source_profile: Optional[str] = None
    pos_matched_rule: Optional[str] = None
    pos_mapped: bool = False


@dataclass(frozen=True)
class SeedSelectionConfig:
    language_pair: str = "en-ja"
    top_n: int = 2000
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
    stopwords_path: Optional[Path] = None
    stopwords: Optional[set[str]] = None
    source_label: Optional[str] = None
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
    jmdict_lemmas = _load_jmdict_lemmas(config.jmdict_path) if config.require_jmdict else None
    stopwords = _resolve_stopwords(config)
    source_label = _resolve_source_label(config=config, frequency_db=frequency_db)
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
        include_pos = bool(resolved_pos_column)
        include_lform = bool(resolved_lform_column)
        include_wtype = bool(resolved_wtype_column)
        include_sublemma = bool(resolved_sublemma_column)
        selected_columns = [
            column
            for column in (
                resolved_pos_column,
                resolved_lform_column,
                resolved_wtype_column,
                resolved_sublemma_column,
                *resolved_topic_columns,
            )
            if column
        ]
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
            normalized_pos = normalize_pos(
                raw_pos,
                language_pair=config.language_pair,
                source_provider=source_label,
                source_kind="frequency",
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
            if stopwords and normalized_lemma in stopwords:
                continue
            if _should_exclude_bootstrap_lemma(
                language_pair=config.language_pair,
                lemma=normalized_lemma,
            ):
                continue
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
                    **bootstrap_metadata,
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
                        "rank_column": resolved_rank_column,
                        "pmw_column": resolved_pmw_column,
                        "pos_column": resolved_pos_column if include_pos else None,
                        "lform_column": resolved_lform_column if include_lform else None,
                        "wtype_column": resolved_wtype_column if include_wtype else None,
                        "sublemma_column": resolved_sublemma_column if include_sublemma else None,
                        "pos_bucket": pos_bucket,
                        "pos_weight": pos_weight,
                        "admission_weight": admission_weight,
                        **bootstrap_metadata,
                        **topic_metadata,
                    },
                    pos_raw=raw_pos,
                    pos_canonical=normalized_pos.canonical,
                    pos_source_profile=normalized_pos.source_profile,
                    pos_matched_rule=normalized_pos.matched_rule,
                    pos_mapped=normalized_pos.mapped,
                )
            )
        if config.sort_by_admission_weight:
            results.sort(key=_admission_sort_key)
        return results


def seed_to_selector_candidates(seeds: Sequence[SeedWord]) -> list[SelectorCandidate]:
    candidates: list[SelectorCandidate] = []
    for seed in seeds:
        pos_raw = getattr(seed, "pos_raw", None)
        pos_canonical = getattr(seed, "pos_canonical", None)
        pos_mapped = bool(getattr(seed, "pos_mapped", False))
        pos_source_profile = getattr(seed, "pos_source_profile", None)
        pos_matched_rule = getattr(seed, "pos_matched_rule", None)
        metadata = {
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
            **seed.metadata,
        }
        word_package = getattr(seed, "word_package", None)
        if word_package:
            metadata["word_package"] = word_package
        candidates.append(
            SelectorCandidate(
                lemma=seed.lemma,
                language_pair=seed.language_pair,
                base_freq=seed.admission_weight,
                confidence=seed.admission_weight,
                pos=seed.pos_bucket,
                metadata=metadata,
            )
        )
    return candidates


def _load_jmdict_lemmas(path: Optional[Path]) -> Optional[set[str]]:
    if not path:
        return None
    return load_jmdict_lemmas(path)


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
