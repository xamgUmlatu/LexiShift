from __future__ import annotations

import csv
import json
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Optional, Sequence


@dataclass(frozen=True)
class ParseConfig:
    delimiter: str = "\t"
    header_starts_with: Optional[str] = "rank"
    skip_prefixes: Sequence[str] = field(default_factory=tuple)


def convert_frequency_to_sqlite(
    input_path: Path,
    output_path: Path,
    *,
    table: str = "frequency",
    overwrite: bool = False,
    config: Optional[ParseConfig] = None,
    index_column: str = "lemma",
) -> None:
    config = config or ParseConfig()
    headers, rows = _iter_rows(input_path, config)
    column_names, column_types = _build_schema(headers)

    if output_path.exists():
        if overwrite:
            output_path.unlink()
        else:
            raise FileExistsError(f"Output already exists: {output_path}")

    with sqlite3.connect(output_path) as conn:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        columns_sql = ", ".join(
            f"{name} {ctype}" for name, ctype in zip(column_names, column_types)
        )
        conn.execute(f"CREATE TABLE {table} ({columns_sql});")
        placeholders = ", ".join("?" for _ in column_names)
        insert_sql = f"INSERT INTO {table} ({', '.join(column_names)}) VALUES ({placeholders});"

        batch = []
        for row in rows:
            if len(row) < len(column_names):
                row.extend([""] * (len(column_names) - len(row)))
            converted = [
                _convert_value(row[idx].strip(), column_types[idx])
                for idx in range(len(column_names))
            ]
            batch.append(converted)
            if len(batch) >= 2000:
                conn.executemany(insert_sql, batch)
                batch.clear()
        if batch:
            conn.executemany(insert_sql, batch)

        if index_column and index_column in column_names:
            conn.execute(f"CREATE INDEX idx_{table}_{index_column} ON {table}({index_column});")
        conn.execute("CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT);")
        meta = {
            "source_file": str(input_path),
            "headers": headers,
            "column_names": column_names,
            "index_column": index_column,
        }
        conn.execute(
            "INSERT INTO meta (key, value) VALUES (?, ?);",
            ("metadata", json.dumps(meta)),
        )
        conn.commit()


def _iter_rows(
    path: Path,
    config: ParseConfig,
) -> tuple[list[str], Iterable[list[str]]]:
    header: Optional[list[str]] = None
    rows: list[list[str]] = []
    with path.open(encoding="utf-8", errors="ignore") as handle:
        for raw in handle:
            line = raw.rstrip("\n")
            if not line:
                continue
            if any(line.startswith(prefix) for prefix in config.skip_prefixes):
                continue
            if header is None:
                if config.header_starts_with and not line.startswith(config.header_starts_with):
                    continue
                header = line.split(config.delimiter)
                continue
            rows.append(line.split(config.delimiter))
    if header is None:
        raise ValueError("Header row not found. Adjust header_starts_with or skip_prefixes.")
    return header, rows


def _build_schema(headers: list[str]) -> tuple[list[str], list[str]]:
    normalized = [_normalize_header(name) for name in headers]
    column_types = []
    for name in normalized:
        if name in {"lemma", "pos", "sublemma", "lform", "wtype"}:
            column_types.append("TEXT")
        else:
            column_types.append("REAL")
    return normalized, column_types


def _normalize_header(name: str) -> str:
    cleaned = name.strip().lower().replace("%", "pct_")
    out = []
    for ch in cleaned:
        if ch.isalnum():
            out.append(ch)
        else:
            out.append("_")
    normalized = "".join(out)
    while "__" in normalized:
        normalized = normalized.replace("__", "_")
    return normalized.strip("_")


def _convert_value(value: str, column_type: str):
    if value == "":
        return None
    if column_type == "TEXT":
        return value
    try:
        return float(value)
    except ValueError:
        return None
