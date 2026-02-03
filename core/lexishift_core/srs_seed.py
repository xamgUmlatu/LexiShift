from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional, Sequence

from lexishift_core.dict_loaders import load_jmdict_lemmas
from lexishift_core.frequency_sqlite_store import SqliteFrequencyConfig, SqliteFrequencyStore
from lexishift_core.srs_selector import SelectorCandidate
from lexishift_core.weighting import PmwWeighting


@dataclass(frozen=True)
class SeedWord:
    lemma: str
    language_pair: str
    core_rank: Optional[float]
    pmw: Optional[float]
    base_weight: float
    metadata: dict[str, object]


@dataclass(frozen=True)
class SeedSelectionConfig:
    language_pair: str = "en-ja"
    top_n: int = 2000
    lemma_column: str = "lemma"
    rank_column: str = "core_rank"
    pmw_column: str = "pmw"
    pmw_weighting: PmwWeighting = PmwWeighting()
    require_jmdict: bool = True
    jmdict_path: Optional[Path] = None


def build_seed_candidates(
    *,
    frequency_db: Path,
    config: SeedSelectionConfig,
) -> list[SeedWord]:
    if config.require_jmdict and not config.jmdict_path:
        raise ValueError("JMDict path is required when require_jmdict is True.")
    jmdict_lemmas = _load_jmdict_lemmas(config.jmdict_path) if config.require_jmdict else None
    store_config = SqliteFrequencyConfig(
        path=frequency_db,
        lemma_column=config.lemma_column,
        rank_column=config.rank_column,
        pmw_column=config.pmw_column,
    )
    with SqliteFrequencyStore(store_config) as store:
        max_pmw = store.max_value(config.pmw_column)
        results: list[SeedWord] = []
        for row in store.iter_top_by_rank(limit=config.top_n, rank_column=config.rank_column):
            lemma = str(row[config.lemma_column]).strip()
            if not lemma:
                continue
            if jmdict_lemmas is not None and lemma not in jmdict_lemmas:
                continue
            columns = row.keys()
            core_rank = _safe_float(row[config.rank_column]) if config.rank_column in columns else None
            pmw = _safe_float(row[config.pmw_column]) if config.pmw_column in columns else None
            base_weight = config.pmw_weighting.normalize(pmw, max_value=max_pmw)
            results.append(
                SeedWord(
                    lemma=lemma,
                    language_pair=config.language_pair,
                    core_rank=core_rank,
                    pmw=pmw,
                    base_weight=base_weight,
                    metadata={
                        "source": "bccwj",
                        "rank_column": config.rank_column,
                        "pmw_column": config.pmw_column,
                    },
                )
            )
        return results


def seed_to_selector_candidates(seeds: Sequence[SeedWord]) -> list[SelectorCandidate]:
    return [
        SelectorCandidate(
            lemma=seed.lemma,
            language_pair=seed.language_pair,
            base_freq=seed.base_weight,
            metadata={
                "core_rank": seed.core_rank,
                "pmw": seed.pmw,
                **seed.metadata,
            },
        )
        for seed in seeds
    ]


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
