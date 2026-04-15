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


@dataclass(frozen=True)
class TopicEnrichmentConfig:
    source_sqlite_path: Path
    source_provider: str = ""
    source_kind: str = "dictionary_topics"
    source_table: str = "sense_glosses"
    source_headword_column: str = "headword"
    source_headword_lc_column: str = "headword_lc"
    source_topics_column: str = "topics_json"
    target_lemma_column: str = "lemma"
    target_topic_column: str = "sense_topics"
    max_topics_per_lemma: int = 24
    replace_existing: bool = True


def convert_frequency_to_sqlite(
    input_path: Path,
    output_path: Path,
    *,
    table: str = "frequency",
    overwrite: bool = False,
    config: Optional[ParseConfig] = None,
    index_column: str = "lemma",
    pos_inventory: Optional[PosInventoryConfig] = None,
    topic_enrichment: Optional[TopicEnrichmentConfig] = None,
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

    conn = sqlite3.connect(output_path)
    try:
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
    finally:
        conn.close()
    if topic_enrichment is not None:
        topic_metadata = enrich_frequency_sqlite_topics(
            output_path,
            table=table,
            enrichment=topic_enrichment,
        )
        metadata.update(topic_metadata)
    return metadata


def enrich_frequency_sqlite_topics(
    frequency_db_path: Path,
    *,
    table: str = "frequency",
    enrichment: TopicEnrichmentConfig,
) -> dict[str, Any]:
    frequency_db = Path(frequency_db_path)
    source_db = Path(enrichment.source_sqlite_path)
    if not frequency_db.exists():
        raise FileNotFoundError(frequency_db)
    if not source_db.exists():
        raise FileNotFoundError(source_db)

    conn = sqlite3.connect(frequency_db)
    try:
        conn.row_factory = sqlite3.Row
        table_names = _list_table_names(conn)
        resolved_table = _resolve_table_name(table_names, table)
        if resolved_table is None:
            raise ValueError(f"Missing table '{table}' in frequency DB: {frequency_db}")
        column_names = _list_column_names(conn, resolved_table)
        resolved_lemma_column = _resolve_column_name(
            column_names,
            enrichment.target_lemma_column,
        )
        if resolved_lemma_column is None:
            raise ValueError(
                f"Missing lemma column '{enrichment.target_lemma_column}' in table '{resolved_table}'."
            )
        resolved_topic_column = _resolve_column_name(
            column_names,
            enrichment.target_topic_column,
        )
        if resolved_topic_column is None:
            conn.execute(
                f"ALTER TABLE {_quote_identifier(resolved_table)} "
                f"ADD COLUMN {_quote_identifier(enrichment.target_topic_column)} TEXT"
            )
            resolved_topic_column = enrichment.target_topic_column
        if enrichment.replace_existing:
            conn.execute(
                f"UPDATE {_quote_identifier(resolved_table)} "
                f"SET {_quote_identifier(resolved_topic_column)} = NULL"
            )

        exact_targets, lc_targets = _collect_target_lemmas(
            conn,
            table_name=resolved_table,
            lemma_column=resolved_lemma_column,
        )
        aggregated_topics = _collect_matching_topics(
            source_db,
            exact_targets=exact_targets,
            lc_targets=lc_targets,
            enrichment=enrichment,
        )
        update_rows = [
            (
                json.dumps(topics, ensure_ascii=False),
                lemma,
            )
            for lemma, topics in sorted(aggregated_topics.items())
            if topics
        ]
        if update_rows:
            conn.executemany(
                f"UPDATE {_quote_identifier(resolved_table)} "
                f"SET {_quote_identifier(resolved_topic_column)} = ? "
                f"WHERE {_quote_identifier(resolved_lemma_column)} = ?",
                update_rows,
            )

        updated_row_count = 0
        row = conn.execute(
            f"SELECT COUNT(*) AS value FROM {_quote_identifier(resolved_table)} "
            f"WHERE TRIM(COALESCE(CAST({_quote_identifier(resolved_topic_column)} AS TEXT), '')) <> ''"
        ).fetchone()
        if row is not None:
            updated_row_count = int(row["value"] or 0)

        enrichment_metadata = {
            "topic_enrichment_applied": True,
            "topic_enrichment_target_column": resolved_topic_column,
            "topic_enrichment_source_file": str(source_db),
            "topic_enrichment_source_provider": str(enrichment.source_provider or "") or None,
            "topic_enrichment_source_kind": str(enrichment.source_kind or "dictionary_topics"),
            "topic_enrichment_matched_lemma_count": len(update_rows),
            "topic_enrichment_rows_with_topics": updated_row_count,
            "topic_enrichment_max_topics_per_lemma": int(enrichment.max_topics_per_lemma),
        }
        _merge_metadata_row(conn, enrichment_metadata)
        conn.commit()
        return enrichment_metadata
    finally:
        conn.close()


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


def _resolve_pos_column_indexes(
    column_names: Sequence[str], pos_columns: Sequence[str]
) -> list[int]:
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


def _quote_identifier(identifier: str) -> str:
    return '"' + str(identifier).replace('"', '""') + '"'


def _list_table_names(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()
    return [str(row[0]) for row in rows if str(row[0]).strip()]


def _list_column_names(conn: sqlite3.Connection, table_name: str) -> list[str]:
    rows = conn.execute(f"PRAGMA table_info({_quote_identifier(table_name)})").fetchall()
    return [str(row[1]) for row in rows if len(row) > 1 and str(row[1]).strip()]


def _resolve_table_name(table_names: Sequence[str], requested: str) -> Optional[str]:
    lowered = {name.lower(): name for name in table_names}
    return lowered.get(str(requested or "").strip().lower())


def _resolve_column_name(column_names: Sequence[str], requested: str) -> Optional[str]:
    lowered = {name.lower(): name for name in column_names}
    return lowered.get(str(requested or "").strip().lower())


def _collect_target_lemmas(
    conn: sqlite3.Connection,
    *,
    table_name: str,
    lemma_column: str,
) -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    exact_targets: dict[str, set[str]] = {}
    lc_targets: dict[str, set[str]] = {}
    rows = conn.execute(
        f"SELECT DISTINCT CAST({_quote_identifier(lemma_column)} AS TEXT) AS lemma "
        f"FROM {_quote_identifier(table_name)} "
        f"WHERE TRIM(COALESCE(CAST({_quote_identifier(lemma_column)} AS TEXT), '')) <> ''"
    ).fetchall()
    for row in rows:
        lemma = str(row["lemma"] or "").strip()
        if not lemma:
            continue
        exact_targets.setdefault(lemma, set()).add(lemma)
        lc_targets.setdefault(lemma.lower(), set()).add(lemma)
    return exact_targets, lc_targets


def _collect_matching_topics(
    source_db: Path,
    *,
    exact_targets: dict[str, set[str]],
    lc_targets: dict[str, set[str]],
    enrichment: TopicEnrichmentConfig,
) -> dict[str, list[str]]:
    source_conn = sqlite3.connect(source_db)
    try:
        source_conn.row_factory = sqlite3.Row
        table_names = _list_table_names(source_conn)
        resolved_table = _resolve_table_name(table_names, enrichment.source_table)
        if resolved_table is None:
            raise ValueError(
                f"Missing table '{enrichment.source_table}' in topic source: {source_db}"
            )
        column_names = _list_column_names(source_conn, resolved_table)
        resolved_headword_column = _resolve_column_name(
            column_names,
            enrichment.source_headword_column,
        )
        resolved_headword_lc_column = _resolve_column_name(
            column_names,
            enrichment.source_headword_lc_column,
        )
        resolved_topics_column = _resolve_column_name(
            column_names,
            enrichment.source_topics_column,
        )
        if resolved_topics_column is None:
            raise ValueError(
                f"Missing topics column '{enrichment.source_topics_column}' in topic source: {source_db}"
            )
        if resolved_headword_column is None and resolved_headword_lc_column is None:
            raise ValueError(
                "Topic source must expose at least one headword column for enrichment matching."
            )

        topic_map: dict[str, dict[str, str]] = {}
        cursor = source_conn.execute(
            f"SELECT "
            f"{_quoted_select_column(resolved_headword_column)} AS headword, "
            f"{_quoted_select_column(resolved_headword_lc_column)} AS headword_lc, "
            f"{_quote_identifier(resolved_topics_column)} AS topics_json "
            f"FROM {_quote_identifier(resolved_table)} "
            f"WHERE TRIM(COALESCE(CAST({_quote_identifier(resolved_topics_column)} AS TEXT), '')) <> ''"
        )
        try:
            for row in cursor:
                topics = _parse_topics_json(
                    row["topics_json"],
                    max_topics=max(1, int(enrichment.max_topics_per_lemma)),
                )
                if not topics:
                    continue
                target_lemmas: set[str] = set()
                headword = str(row["headword"] or "").strip()
                headword_lc = str(row["headword_lc"] or "").strip().lower()
                if headword and headword in exact_targets:
                    target_lemmas.update(exact_targets[headword])
                if headword_lc and headword_lc in lc_targets:
                    target_lemmas.update(lc_targets[headword_lc])
                if not target_lemmas:
                    continue
                for lemma in target_lemmas:
                    bucket = topic_map.setdefault(lemma, {})
                    for topic in topics:
                        normalized_key = topic.casefold()
                        if normalized_key not in bucket:
                            bucket[normalized_key] = topic
                        if len(bucket) >= max(1, int(enrichment.max_topics_per_lemma)):
                            break
        finally:
            cursor.close()
        return {
            lemma: list(bucket.values())[: max(1, int(enrichment.max_topics_per_lemma))]
            for lemma, bucket in topic_map.items()
            if bucket
        }
    finally:
        source_conn.close()


def _quoted_select_column(column_name: Optional[str]) -> str:
    if not column_name:
        return "NULL"
    return _quote_identifier(column_name)


def _parse_topics_json(value: object, *, max_topics: int) -> list[str]:
    text = str(value or "").strip()
    if not text:
        return []
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        parsed = text
    values: list[str] = []
    seen: set[str] = set()
    if isinstance(parsed, str):
        parsed_values: Sequence[object] = (parsed,)
    elif isinstance(parsed, Sequence):
        parsed_values = parsed
    else:
        parsed_values = ()
    for item in parsed_values:
        topic = str(item or "").strip()
        if not topic:
            continue
        normalized = topic.casefold()
        if normalized in seen:
            continue
        seen.add(normalized)
        values.append(topic)
        if len(values) >= max_topics:
            break
    return values


def _merge_metadata_row(conn: sqlite3.Connection, new_values: dict[str, Any]) -> None:
    conn.execute("CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT)")
    row = conn.execute("SELECT value FROM meta WHERE key='metadata'").fetchone()
    payload: dict[str, Any] = {}
    if row is not None and row[0]:
        try:
            payload = json.loads(str(row[0]))
        except json.JSONDecodeError:
            payload = {}
    payload.update(new_values)
    if row is None:
        conn.execute(
            "INSERT INTO meta (key, value) VALUES ('metadata', ?)",
            (json.dumps(payload, ensure_ascii=False),),
        )
        return
    conn.execute(
        "UPDATE meta SET value = ? WHERE key = 'metadata'",
        (json.dumps(payload, ensure_ascii=False),),
    )
