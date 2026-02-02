#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional


DEFAULT_SKIP_PREFIXES = ("*", "-----")


@dataclass(frozen=True)
class ParseConfig:
    delimiter: str = "\t"
    header_starts_with: str = "rank"
    skip_prefixes: tuple[str, ...] = DEFAULT_SKIP_PREFIXES


def normalize_header(name: str) -> str:
    cleaned = name.strip().lower()
    cleaned = cleaned.replace("%", "pct_")
    cleaned = cleaned.replace("pos", "pos")
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


def iter_rows(path: Path, config: ParseConfig) -> tuple[list[str], Iterable[list[str]]]:
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
            row = line.split(config.delimiter)
            rows.append(row)
    if header is None:
        raise ValueError("Header row not found. Adjust header_starts_with or skip_prefixes.")
    return header, rows


def build_schema(headers: list[str]) -> tuple[list[str], list[str]]:
    normalized = [normalize_header(name) for name in headers]
    column_types = []
    for name in normalized:
        if name in {"lemma", "pos"}:
            column_types.append("TEXT")
        else:
            column_types.append("REAL")
    return normalized, column_types


def convert_value(value: str, column_type: str):
    if value == "":
        return None
    if column_type == "TEXT":
        return value
    try:
        return float(value)
    except ValueError:
        return None


def convert_to_sqlite(
    input_path: Path,
    output_path: Path,
    *,
    table: str = "frequency",
    overwrite: bool = False,
    config: Optional[ParseConfig] = None,
    index_column: str = "lemma",
) -> None:
    config = config or ParseConfig()
    headers, rows = iter_rows(input_path, config)
    column_names, column_types = build_schema(headers)

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
                convert_value(row[idx].strip(), column_types[idx])
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
        conn.execute(
            "CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT);"
        )
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert a frequency list to SQLite.")
    parser.add_argument("input", type=Path, help="Path to frequency list file")
    parser.add_argument("output", type=Path, help="Path to output SQLite file")
    parser.add_argument("--table", default="frequency", help="Table name")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite output if exists")
    parser.add_argument("--index-column", default="lemma", help="Column name to index")
    parser.add_argument("--delimiter", default="\t", help="Delimiter (default: tab)")
    parser.add_argument(
        "--header-starts-with",
        default="rank",
        help="Header row must start with this token",
    )
    parser.add_argument(
        "--skip-prefix",
        action="append",
        default=list(DEFAULT_SKIP_PREFIXES),
        help="Line prefix to skip (can be repeated)",
    )
    args = parser.parse_args()

    config = ParseConfig(
        delimiter=args.delimiter,
        header_starts_with=args.header_starts_with,
        skip_prefixes=tuple(args.skip_prefix),
    )
    convert_to_sqlite(
        args.input,
        args.output,
        table=args.table,
        overwrite=args.overwrite,
        config=config,
        index_column=args.index_column,
    )


if __name__ == "__main__":
    main()
