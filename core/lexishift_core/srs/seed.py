from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Optional, Sequence

from lexishift_core.lexicon.word_package import build_word_package
from lexishift_core.resources.dict_loaders import load_jmdict_lemmas
from lexishift_core.frequency.sqlite_store import SqliteFrequencyConfig, SqliteFrequencyStore
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
        available_columns = set(store.column_names())
        include_pos = bool(config.pos_column and config.pos_column in available_columns)
        include_lform = bool(config.lform_column and config.lform_column in available_columns)
        include_wtype = bool(config.wtype_column and config.wtype_column in available_columns)
        include_sublemma = bool(config.sublemma_column and config.sublemma_column in available_columns)
        selected_columns = [
            column
            for column, enabled in (
                (config.pos_column, include_pos),
                (config.lform_column, include_lform),
                (config.wtype_column, include_wtype),
                (config.sublemma_column, include_sublemma),
            )
            if enabled and column
        ]
        resolved_pos_weights = (
            config.admission_pos_weights
            or resolve_default_pos_weights(language_pair=config.language_pair)
        )
        max_pmw = store.max_value(config.pmw_column)
        results: list[SeedWord] = []
        for row_index, row in enumerate(
            store.iter_top_by_rank(
                limit=config.top_n,
                rank_column=config.rank_column,
                columns=selected_columns,
            ),
            start=1,
        ):
            lemma = str(row[config.lemma_column]).strip()
            if not lemma:
                continue
            if stopwords and lemma in stopwords:
                continue
            if jmdict_lemmas is not None and lemma not in jmdict_lemmas:
                continue
            columns = row.keys()
            core_rank = _safe_float(row[config.rank_column]) if config.rank_column in columns else None
            pmw = _safe_float(row[config.pmw_column]) if config.pmw_column in columns else None
            raw_pos = (
                str(row[config.pos_column]).strip()
                if include_pos and config.pos_column in columns and row[config.pos_column] is not None
                else None
            )
            raw_lform = (
                str(row[config.lform_column]).strip()
                if include_lform and config.lform_column in columns and row[config.lform_column] is not None
                else None
            )
            raw_wtype = (
                str(row[config.wtype_column]).strip()
                if include_wtype and config.wtype_column in columns and row[config.wtype_column] is not None
                else None
            )
            raw_sublemma = (
                str(row[config.sublemma_column]).strip()
                if include_sublemma
                and config.sublemma_column in columns
                and row[config.sublemma_column] is not None
                else None
            )
            word_package = build_word_package(
                language_pair=config.language_pair,
                surface=lemma,
                reading=raw_lform or lemma,
                source_provider=source_label,
                pos=raw_pos,
                wtype=raw_wtype,
                sublemma=raw_sublemma,
                core_rank=core_rank,
                pmw=pmw,
                lform_raw=raw_lform,
                row_index=row_index,
                row_rank=core_rank,
                source_extra={
                    "rank_column": config.rank_column,
                    "pmw_column": config.pmw_column,
                    "lemma_column": config.lemma_column,
                    "pos_column": config.pos_column if include_pos else None,
                    "lform_column": config.lform_column if include_lform else None,
                    "wtype_column": config.wtype_column if include_wtype else None,
                    "sublemma_column": config.sublemma_column if include_sublemma else None,
                },
            )
            base_weight = config.pmw_weighting.normalize(pmw, max_value=max_pmw)
            pos_bucket, pos_weight, admission_weight = compute_admission_weight(
                language_pair=config.language_pair,
                raw_pos=raw_pos,
                base_weight=base_weight,
                pos_weights=resolved_pos_weights,
            )
            results.append(
                SeedWord(
                    lemma=lemma,
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
                        "rank_column": config.rank_column,
                        "pmw_column": config.pmw_column,
                        "pos_column": config.pos_column if include_pos else None,
                        "lform_column": config.lform_column if include_lform else None,
                        "wtype_column": config.wtype_column if include_wtype else None,
                        "sublemma_column": config.sublemma_column if include_sublemma else None,
                        "pos_bucket": pos_bucket,
                        "pos_weight": pos_weight,
                        "admission_weight": admission_weight,
                    },
                )
            )
        if config.sort_by_admission_weight:
            results.sort(key=_admission_sort_key)
        return results


def seed_to_selector_candidates(seeds: Sequence[SeedWord]) -> list[SelectorCandidate]:
    candidates: list[SelectorCandidate] = []
    for seed in seeds:
        metadata = {
            "core_rank": seed.core_rank,
            "pos": seed.pos,
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
            raise ValueError(
                f"Invalid stopwords format in {path}: item #{index} is not a string."
            )
        value = item.strip()
        if not value:
            raise ValueError(
                f"Invalid stopwords format in {path}: item #{index} is empty."
            )
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
