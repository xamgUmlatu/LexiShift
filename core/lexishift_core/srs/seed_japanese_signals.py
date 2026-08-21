from __future__ import annotations

from pathlib import Path
from typing import Iterable, Optional, Sequence, cast

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


def load_optional_jmdict_priority_index(path: Optional[Path]):
    if path is None or not Path(path).is_file():
        return {}
    return load_jmdict_priority_index(Path(path))


def load_optional_jmdict_lexical_index(path: Optional[Path]):
    if path is None or not Path(path).is_file():
        return {}
    return load_jmdict_lexical_index(Path(path))


def load_optional_kanjidic2_character_index(path: Optional[Path]):
    if path is None or not Path(path).is_file():
        return {}
    return load_kanjidic2_character_index(Path(path))


def load_optional_jmnedict_name_index(path: Optional[Path]):
    if path is None or not Path(path).is_file():
        return {}
    return load_jmnedict_name_index(Path(path))


def load_optional_kanjivg_character_index(path: Optional[Path]):
    if path is None or not Path(path).is_file():
        return {}
    return load_kanjivg_character_index(Path(path))


def load_optional_jlpt_vocabulary_index(
    path: Optional[Path],
    *,
    jmdict_path: Optional[Path] = None,
):
    if path is None or not Path(path).exists():
        return {}
    resolved_jmdict_path = Path(jmdict_path) if jmdict_path is not None else None
    return load_jlpt_vocabulary_index(Path(path), jmdict_path=resolved_jmdict_path)


def load_optional_japanese_lesson_vocabulary_index(path: Optional[Path]):
    if path is None or not Path(path).exists():
        return {}
    return load_japanese_lesson_vocabulary_index(Path(path))


def resolve_jmnedict_path(config: object) -> Optional[Path]:
    configured_path = getattr(config, "jmnedict_path", None)
    if configured_path is not None:
        return Path(configured_path)
    jmdict_path = getattr(config, "jmdict_path", None)
    if jmdict_path is None:
        return None
    candidate_roots = _japanese_optional_signal_roots(Path(jmdict_path))
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


def resolve_kanjivg_path(config: object) -> Optional[Path]:
    configured_path = getattr(config, "kanjivg_path", None)
    if configured_path is not None:
        return Path(configured_path)
    jmdict_path = getattr(config, "jmdict_path", None)
    if jmdict_path is None:
        return None
    candidate_roots = _japanese_optional_signal_roots(Path(jmdict_path))
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


def resolve_jlpt_vocabulary_path(config: object) -> Optional[Path]:
    configured_path = getattr(config, "jlpt_vocabulary_path", None)
    if configured_path is not None:
        return Path(configured_path)
    jmdict_path = getattr(config, "jmdict_path", None)
    if jmdict_path is None:
        return None
    candidate_roots = _japanese_optional_signal_roots(Path(jmdict_path))
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


def resolve_lesson_vocabulary_path(config: object) -> Optional[Path]:
    configured_path = getattr(config, "lesson_vocabulary_path", None)
    if configured_path is not None:
        return Path(configured_path)
    jmdict_path = getattr(config, "jmdict_path", None)
    if jmdict_path is None:
        return None
    candidate_roots = _japanese_optional_signal_roots(Path(jmdict_path))
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


def resolve_kanjidic2_path(config: object) -> Optional[Path]:
    configured_path = getattr(config, "kanjidic2_path", None)
    if configured_path is not None:
        return Path(configured_path)
    jmdict_path = getattr(config, "jmdict_path", None)
    if jmdict_path is None:
        return None
    candidate_roots = _japanese_optional_signal_roots(Path(jmdict_path))
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


def extract_learner_signal_metadata(
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
    raw_sources = learner_signals.get("sources", ())
    learner_signal_sources = (
        list(cast(Iterable[object], raw_sources))
        if hasattr(raw_sources, "__iter__") and not isinstance(raw_sources, (str, bytes))
        else []
    )
    return {
        "learner_signal_version": learner_signals.get("version"),
        "learner_signal_sources": learner_signal_sources,
        "learner_signals": learner_signals,
    }


def source_frequency_profile_columns(*, available_columns: Sequence[str]) -> tuple[str, ...]:
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


def extract_source_frequency_metadata(
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


def _safe_float(value) -> Optional[float]:
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
