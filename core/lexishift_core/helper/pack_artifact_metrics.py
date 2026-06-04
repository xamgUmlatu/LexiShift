from __future__ import annotations

from pathlib import Path
import sqlite3
from typing import Mapping


def sqlite_artifact_metrics_for_pack(
    *,
    pack_kind: str,
    artifact_path: Path,
) -> dict[str, int]:
    """Return conservative sidecar metrics for supported SQLite pack families."""
    if str(pack_kind or "").strip() != "frequency":
        return {}
    path = Path(artifact_path)
    if not path.is_file():
        return {}
    try:
        with sqlite3.connect(str(path)) as conn:
            conn.execute("PRAGMA query_only = ON;")
            if not _table_exists(conn, "frequency"):
                return {}
            columns = _table_columns(conn, "frequency")
            metrics: dict[str, int] = {"row_count": _count_rows(conn, "frequency")}
            if "lemma" in columns:
                metrics["distinct_lemma_count"] = _count_distinct_nonempty(
                    conn,
                    "frequency",
                    "lemma",
                )
            if "pos" in columns:
                metrics["pos_rows"] = _count_nonempty(conn, "frequency", "pos")
            else:
                metrics["pos_rows"] = 0
            metrics["topic_domain_rows"] = _count_topic_domain_rows(
                conn,
                "frequency",
                columns,
            )
            return metrics
    except sqlite3.Error:
        return {}


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ? LIMIT 1;",
        (table,),
    ).fetchone()
    return row is not None


def _table_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    rows = conn.execute(f"PRAGMA table_info({_quote_ident(table)});").fetchall()
    return {str(row[1] or "").strip() for row in rows if str(row[1] or "").strip()}


def _count_rows(conn: sqlite3.Connection, table: str) -> int:
    return int(conn.execute(f"SELECT COUNT(*) FROM {_quote_ident(table)};").fetchone()[0] or 0)


def _count_distinct_nonempty(conn: sqlite3.Connection, table: str, column: str) -> int:
    row = conn.execute(
        f"""
        SELECT COUNT(DISTINCT TRIM(COALESCE({_quote_ident(column)}, '')))
        FROM {_quote_ident(table)}
        WHERE TRIM(COALESCE({_quote_ident(column)}, '')) <> '';
        """
    ).fetchone()
    return int(row[0] or 0)


def _count_nonempty(conn: sqlite3.Connection, table: str, column: str) -> int:
    row = conn.execute(
        f"""
        SELECT COUNT(*)
        FROM {_quote_ident(table)}
        WHERE TRIM(COALESCE({_quote_ident(column)}, '')) <> '';
        """
    ).fetchone()
    return int(row[0] or 0)


def _count_topic_domain_rows(
    conn: sqlite3.Connection,
    table: str,
    columns: Mapping[str, object] | set[str],
) -> int:
    topic_columns = [
        column
        for column in columns
        if column
        in {
            "topic",
            "topics",
            "topics_json",
            "domain",
            "domains",
            "domains_json",
            "topic_domain",
            "topic_domain_json",
        }
    ]
    if not topic_columns:
        return 0
    predicates = [
        f"TRIM(COALESCE({_quote_ident(column)}, '')) <> ''" for column in sorted(topic_columns)
    ]
    row = conn.execute(
        f"SELECT COUNT(*) FROM {_quote_ident(table)} WHERE {' OR '.join(predicates)};"
    ).fetchone()
    return int(row[0] or 0)


def _quote_ident(value: str) -> str:
    return '"' + str(value).replace('"', '""') + '"'
