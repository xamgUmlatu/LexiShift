from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

FREQUENCY_VALUE_COLUMNS = (
    "pmw",
    "core_pmw",
    "frequency",
    "core_frequency",
    "freq",
    "freq_per_million",
    "count",
    "ipm",
)
RANK_COLUMNS = ("core_rank", "rank", "id", "index")


@dataclass(frozen=True)
class SqliteFrequencyConfig:
    path: Path
    table: str = "frequency"
    lemma_column: str = "lemma"
    pmw_column: str = "pmw"
    rank_column: str = "core_rank"


class SqliteFrequencyStore:
    def __init__(self, config: SqliteFrequencyConfig) -> None:
        self._config = config
        self._conn = sqlite3.connect(str(config.path))
        self._conn.row_factory = sqlite3.Row
        self._cache: dict[tuple[str, str], Optional[float]] = {}
        self._max_cache: dict[str, Optional[float]] = {}

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> "SqliteFrequencyStore":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def max_value(self, column: str) -> Optional[float]:
        columns = self.column_names()
        resolved_column = self.resolve_column(column, available_columns=columns)
        if not resolved_column and self._looks_like_frequency_column(column):
            resolved_column = self.resolve_frequency_column(column, available_columns=columns)
        if not resolved_column and self._looks_like_rank_column(column):
            resolved_column = self.resolve_rank_column(column, available_columns=columns)
        if not resolved_column:
            return None
        if resolved_column in self._max_cache:
            return self._max_cache[resolved_column]
        query = f"SELECT MAX({resolved_column}) as value FROM {self._config.table};"
        row = self._conn.execute(query).fetchone()
        value = float(row["value"]) if row and row["value"] is not None else None
        self._max_cache[resolved_column] = value
        return value

    def column_names(self) -> list[str]:
        rows = self._conn.execute(f"PRAGMA table_info({self._config.table});").fetchall()
        return [row[1] for row in rows if len(row) > 1]

    def get_value(self, lemma: str, column: str) -> Optional[float]:
        columns = self.column_names()
        resolved_lemma_column = self.resolve_column(self._config.lemma_column, available_columns=columns)
        resolved_value_column = self.resolve_column(column, available_columns=columns)
        if not resolved_value_column and self._looks_like_frequency_column(column):
            resolved_value_column = self.resolve_frequency_column(column, available_columns=columns)
        if not resolved_value_column and self._looks_like_rank_column(column):
            resolved_value_column = self.resolve_rank_column(column, available_columns=columns)
        if not resolved_lemma_column or not resolved_value_column:
            return None
        key = (lemma, resolved_value_column)
        if key in self._cache:
            return self._cache[key]
        query = (
            f"SELECT {resolved_value_column} as value FROM {self._config.table} "
            f"WHERE {resolved_lemma_column} = ? LIMIT 1;"
        )
        row = self._conn.execute(query, (lemma,)).fetchone()
        value = float(row["value"]) if row and row["value"] is not None else None
        self._cache[key] = value
        return value

    def iter_top_by_rank(
        self,
        *,
        limit: int,
        rank_column: Optional[str] = None,
        pmw_column: Optional[str] = None,
        columns: Optional[Iterable[str]] = None,
    ) -> Iterable[sqlite3.Row]:
        available_columns = self.column_names()
        resolved_lemma_column = self.resolve_column(
            self._config.lemma_column,
            available_columns=available_columns,
        )
        if not resolved_lemma_column:
            raise ValueError(
                f"Missing lemma column '{self._config.lemma_column}' in table '{self._config.table}'."
            )
        requested_rank_column = rank_column or self._config.rank_column
        requested_pmw_column = pmw_column or self._config.pmw_column
        resolved_rank_column = self.resolve_rank_column(
            requested_rank_column,
            available_columns=available_columns,
        )
        resolved_pmw_column = self.resolve_frequency_column(
            requested_pmw_column,
            available_columns=available_columns,
        )
        extra = list(columns or [])
        cols = [resolved_lemma_column]
        if resolved_rank_column and resolved_rank_column not in cols:
            cols.append(resolved_rank_column)
        if resolved_pmw_column and resolved_pmw_column not in cols:
            cols.append(resolved_pmw_column)
        for item in extra:
            resolved_item = self.resolve_column(item, available_columns=available_columns)
            if resolved_item and resolved_item not in cols:
                cols.append(resolved_item)
        col_sql = ", ".join(cols)
        order_terms: list[str] = []
        if resolved_rank_column:
            # Some frequency packs contain NULL rank values. In SQLite, NULL sorts
            # before numeric values for ASC order, which can incorrectly put
            # unranked entries at the top. Push NULL ranks to the end.
            order_terms.append(f"({resolved_rank_column} IS NULL) ASC")
            order_terms.append(f"{resolved_rank_column} ASC")
        if resolved_pmw_column:
            order_terms.append(f"{resolved_pmw_column} DESC")
        order_sql = f" ORDER BY {', '.join(order_terms)}" if order_terms else ""
        query = (
            f"SELECT {col_sql} FROM {self._config.table}"
            f"{order_sql} LIMIT ?;"
        )
        for row in self._conn.execute(query, (limit,)):
            yield row

    def resolve_column(self, requested: Optional[str], *, available_columns: list[str]) -> Optional[str]:
        if not requested:
            return None
        lowered = {name.lower(): name for name in available_columns}
        return lowered.get(str(requested).strip().lower())

    def resolve_rank_column(
        self,
        requested: Optional[str] = None,
        *,
        available_columns: Optional[list[str]] = None,
    ) -> Optional[str]:
        columns = available_columns or self.column_names()
        direct = self.resolve_column(requested, available_columns=columns)
        if direct:
            return direct
        for candidate in RANK_COLUMNS:
            resolved = self.resolve_column(candidate, available_columns=columns)
            if resolved:
                return resolved
        return None

    def resolve_frequency_column(
        self,
        requested: Optional[str] = None,
        *,
        available_columns: Optional[list[str]] = None,
    ) -> Optional[str]:
        columns = available_columns or self.column_names()
        direct = self.resolve_column(requested, available_columns=columns)
        if direct:
            return direct
        for candidate in FREQUENCY_VALUE_COLUMNS:
            resolved = self.resolve_column(candidate, available_columns=columns)
            if resolved:
                return resolved
        return None

    def _looks_like_frequency_column(self, column: Optional[str]) -> bool:
        lowered = str(column or "").strip().lower()
        if not lowered:
            return False
        return lowered in FREQUENCY_VALUE_COLUMNS

    def _looks_like_rank_column(self, column: Optional[str]) -> bool:
        lowered = str(column or "").strip().lower()
        if not lowered:
            return False
        return lowered in RANK_COLUMNS
