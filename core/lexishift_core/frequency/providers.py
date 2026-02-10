from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional

from lexishift_core.frequency.sqlite_store import SqliteFrequencyConfig, SqliteFrequencyStore
from lexishift_core.scoring.weighting import PmwWeighting


@dataclass(frozen=True)
class SqliteFrequencyProviderConfig:
    sqlite: SqliteFrequencyConfig
    value_column: str = "pmw"
    weighting: PmwWeighting = field(default_factory=PmwWeighting)
    lower_case: bool = True


class SqliteFrequencyProvider:
    def __init__(self, config: SqliteFrequencyProviderConfig) -> None:
        self._config = config
        self._store = SqliteFrequencyStore(config.sqlite)
        self._value_column = self._resolve_value_column(config.value_column)
        self._max_value = self._store.max_value(self._value_column)
        self._cache: dict[str, float] = {}

    def close(self) -> None:
        self._store.close()

    def __enter__(self) -> "SqliteFrequencyProvider":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def weight(self, token: str) -> float:
        key = token.lower() if self._config.lower_case else token
        if key in self._cache:
            return self._cache[key]
        raw = self._store.get_value(key, self._value_column)
        weight = self._config.weighting.normalize(raw, max_value=self._max_value)
        self._cache[key] = weight
        return weight

    def weight_phrase(self, phrase: str, *, reducer: str = "avg") -> float:
        tokens = [item for item in phrase.split() if item]
        if not tokens:
            return 0.0
        values = [self.weight(token) for token in tokens]
        if reducer == "min":
            return min(values)
        if reducer == "max":
            return max(values)
        return sum(values) / len(values)

    def _resolve_value_column(self, requested: str) -> str:
        columns = self._store.column_names()
        lowered = {name.lower(): name for name in columns}
        if requested and requested.lower() in lowered:
            return lowered[requested.lower()]
        preferred = ("pmw", "frequency", "freq", "freq_per_million", "count")
        for name in preferred:
            if name in lowered:
                return lowered[name]
        fallback = [name for name in columns if name.lower() not in {"lemma", "pos", "sublemma", "lform", "wtype"}]
        return fallback[0] if fallback else (columns[0] if columns else requested)


def build_sqlite_frequency_provider(
    config: SqliteFrequencyProviderConfig,
    *,
    reducer: str = "avg",
) -> Callable[[object], float]:
    provider = SqliteFrequencyProvider(config)

    def _fn(candidate: object) -> float:
        phrase = getattr(candidate, "source_phrase", "")
        return provider.weight_phrase(str(phrase), reducer=reducer)

    _fn._lexishift_provider = provider  # type: ignore[attr-defined]
    return _fn
