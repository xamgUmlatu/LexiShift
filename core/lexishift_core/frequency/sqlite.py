from __future__ import annotations

from collections import Counter
import json
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
import re
from typing import Any, Callable, Iterable, Optional, Sequence

_normalize_pos: Optional[Callable[..., Any]]
try:
    from lexishift_core.pos.normalization import normalize_pos as _normalize_pos_impl
except Exception:  # noqa: BLE001
    _normalize_pos = None
else:
    _normalize_pos = _normalize_pos_impl


@dataclass(frozen=True)
class ParseConfig:
    delimiter: str = "\t"
    header_starts_with: Optional[str] = "rank"
    skip_prefixes: Sequence[str] = field(default_factory=tuple)
    encoding: str = "utf-8"
    errors: str = "ignore"


@dataclass(frozen=True)
class PosInventoryConfig:
    source_provider: str = ""
    source_profile: str = ""
    source_kind: str = "frequency"
    pos_columns: Sequence[str] = field(default_factory=lambda: ("pos", "wtype"))
    inventory_limit: int = 100


def convert_frequency_to_sqlite(
    input_path: Path,
    output_path: Path,
    *,
    table: str = "frequency",
    overwrite: bool = False,
    config: Optional[ParseConfig] = None,
    index_column: str = "lemma",
    pos_inventory: Optional[PosInventoryConfig] = None,
) -> dict[str, Any]:
    config = config or ParseConfig()
    headers, rows = _iter_rows(input_path, config)
    column_names, column_types = _build_schema(headers)

    if output_path.exists():
        if overwrite:
            output_path.unlink()
        else:
            raise FileExistsError(f"Output already exists: {output_path}")

    pos_column_indexes = _resolve_pos_column_indexes(
        column_names,
        pos_inventory.pos_columns if pos_inventory else (),
    )
    pos_counter: Counter[str] = Counter()
    unknown_pos_counter: Counter[str] = Counter()
    rows_with_pos = 0
    rows_without_pos = 0
    row_count = 0

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
            row_count += 1
            if len(row) < len(column_names):
                row.extend([""] * (len(column_names) - len(row)))
            if pos_inventory is not None:
                tags = _extract_pos_tags_from_row(row, pos_column_indexes)
                if tags:
                    rows_with_pos += 1
                else:
                    rows_without_pos += 1
                for raw_tag in tags:
                    pos_counter[raw_tag] += 1
                    if _is_pos_unmapped(raw_tag, pos_inventory):
                        unknown_pos_counter[raw_tag] += 1
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
        metadata: dict[str, Any] = {
            "source_file": str(input_path),
            "headers": headers,
            "column_names": column_names,
            "index_column": index_column,
            "row_count": row_count,
        }
        if pos_inventory is not None:
            metadata.update(
                {
                    "rows_with_pos": rows_with_pos,
                    "rows_without_pos": rows_without_pos,
                    "pos_inventory_size": len(pos_counter),
                    "pos_inventory_top": _counter_to_ranked(
                        pos_counter, limit=max(1, int(pos_inventory.inventory_limit))
                    ),
                    "unknown_pos_inventory_size": len(unknown_pos_counter),
                    "unknown_pos_inventory_top": _counter_to_ranked(
                        unknown_pos_counter,
                        limit=max(1, int(pos_inventory.inventory_limit)),
                    ),
                    "pos_source_provider": str(pos_inventory.source_provider or "") or None,
                    "pos_source_kind": str(pos_inventory.source_kind or "") or "frequency",
                    "pos_mapping_profile": str(pos_inventory.source_profile or "") or None,
                    "pos_mapping_available": bool(_normalize_pos is not None),
                    "pos_columns_requested": list(pos_inventory.pos_columns),
                    "pos_columns_resolved": [column_names[idx] for idx in pos_column_indexes],
                }
            )
        conn.execute(
            "INSERT INTO meta (key, value) VALUES (?, ?);",
            ("metadata", json.dumps(metadata)),
        )
        conn.commit()
    return metadata


def _iter_rows(
    path: Path,
    config: ParseConfig,
) -> tuple[list[str], Iterable[list[str]]]:
    header: Optional[list[str]] = None
    rows: list[list[str]] = []
    with path.open(encoding=config.encoding, errors=config.errors) as handle:
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


_POS_SPLIT_PATTERN = re.compile(r"[|/,;]+")


def _resolve_pos_column_indexes(column_names: Sequence[str], pos_columns: Sequence[str]) -> list[int]:
    if not pos_columns:
        return []
    indexes: list[int] = []
    name_to_index = {name: idx for idx, name in enumerate(column_names)}
    for raw_name in pos_columns:
        normalized = _normalize_header(str(raw_name or ""))
        if not normalized:
            continue
        idx = name_to_index.get(normalized)
        if idx is None:
            continue
        if idx not in indexes:
            indexes.append(idx)
    return indexes


def _extract_pos_tags_from_row(row: Sequence[str], pos_column_indexes: Sequence[int]) -> list[str]:
    tags: list[str] = []
    seen: set[str] = set()
    for idx in pos_column_indexes:
        if idx >= len(row):
            continue
        value = str(row[idx] or "").strip()
        if not value:
            continue
        split_parts = [part.strip() for part in _POS_SPLIT_PATTERN.split(value) if part.strip()]
        parts = split_parts or [value]
        for tag in parts:
            if tag in seen:
                continue
            seen.add(tag)
            tags.append(tag)
    return tags


def _is_pos_unmapped(raw_tag: str, config: PosInventoryConfig) -> bool:
    if _normalize_pos is None:
        return False
    normalized = _normalize_pos(
        raw_tag,
        source_provider=str(config.source_provider or ""),
        source_kind=str(config.source_kind or "frequency"),
        source_profile=str(config.source_profile or ""),
    )
    return not bool(normalized.mapped)


def _counter_to_ranked(counter: Counter[str], *, limit: int) -> list[dict[str, object]]:
    ranked: list[dict[str, object]] = []
    for tag, count in counter.most_common(limit):
        ranked.append({"tag": tag, "count": int(count)})
    return ranked
