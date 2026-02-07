from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional


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
        if column in self._max_cache:
            return self._max_cache[column]
        query = f"SELECT MAX({column}) as value FROM {self._config.table};"
        row = self._conn.execute(query).fetchone()
        value = float(row["value"]) if row and row["value"] is not None else None
        self._max_cache[column] = value
        return value

    def column_names(self) -> list[str]:
        rows = self._conn.execute(f"PRAGMA table_info({self._config.table});").fetchall()
        return [row[1] for row in rows if len(row) > 1]

    def get_value(self, lemma: str, column: str) -> Optional[float]:
        key = (lemma, column)
        if key in self._cache:
            return self._cache[key]
        query = (
            f"SELECT {column} as value FROM {self._config.table} "
            f"WHERE {self._config.lemma_column} = ? LIMIT 1;"
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
        columns: Optional[Iterable[str]] = None,
    ) -> Iterable[sqlite3.Row]:
        rank_column = rank_column or self._config.rank_column
        extra = list(columns or [])
        cols = [self._config.lemma_column, rank_column, self._config.pmw_column]
        for item in extra:
            if item not in cols:
                cols.append(item)
        col_sql = ", ".join(cols)
        # Some frequency packs contain NULL rank values. In SQLite, NULL sorts
        # before numeric values for ASC order, which can incorrectly put
        # unranked entries at the top. Push NULL ranks to the end and
        # tie-break with pmw descending.
        query = (
            f"SELECT {col_sql} FROM {self._config.table} "
            f"ORDER BY ({rank_column} IS NULL) ASC, {rank_column} ASC, {self._config.pmw_column} DESC LIMIT ?;"
        )
        for row in self._conn.execute(query, (limit,)):
            yield row
