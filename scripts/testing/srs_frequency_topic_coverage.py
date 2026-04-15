#!/usr/bin/env python3
from __future__ import annotations

# ruff: noqa: E402

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
import sys
from typing import Any, Iterable, Mapping, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / "core"
if str(CORE_ROOT) not in sys.path:
    sys.path.insert(0, str(CORE_ROOT))

from lexishift_core.frequency.sqlite_store import (  # noqa: E402
    SqliteFrequencyConfig,
    SqliteFrequencyStore,
)
from lexishift_core.srs.admission_features import (  # noqa: E402
    normalize_topic_string_list,
    normalize_topic_string_list_with_origins,
)

DEFAULT_TOPIC_COLUMNS: tuple[str, ...] = (
    "sense_topics",
    "topics",
    "topic",
    "profile_topics",
)
PREFERRED_TABLE_NAMES: tuple[str, ...] = ("frequency", "freq")
DEFAULT_FRONTIER_LIMIT = 800


def _now_iso_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _finding(
    *,
    level: str,
    code: str,
    message: str,
    db_path: str | None = None,
    details: str | None = None,
) -> dict[str, Any]:
    return {
        "level": level,
        "code": code,
        "db_path": db_path,
        "message": message,
        "details": details,
    }


def summarize_findings(findings: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    pass_count = 0
    warn_count = 0
    fail_count = 0
    for item in findings:
        level = str(item.get("level") or "").upper()
        if level == "PASS":
            pass_count += 1
        elif level == "WARN":
            warn_count += 1
        elif level == "FAIL":
            fail_count += 1
    status = "FAIL" if fail_count else "WARN" if warn_count else "PASS"
    return {
        "status": status,
        "pass_count": pass_count,
        "warn_count": warn_count,
        "fail_count": fail_count,
    }


def _table_names(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()
    return [str(row[0]) for row in rows if str(row[0]).strip()]


def _resolve_frequency_table(conn: sqlite3.Connection) -> str | None:
    table_names = _table_names(conn)
    normalized = {name.casefold(): name for name in table_names}
    for preferred in PREFERRED_TABLE_NAMES:
        resolved = normalized.get(preferred.casefold())
        if resolved:
            return resolved
    for table_name in table_names:
        if table_name.casefold() != "meta":
            return table_name
    return None


def _column_names(conn: sqlite3.Connection, table_name: str) -> list[str]:
    rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    return [str(row[1]) for row in rows if len(row) > 1 and str(row[1]).strip()]


def _count_rows(conn: sqlite3.Connection, table_name: str) -> int:
    row = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
    return int(row[0] or 0) if row else 0


def _quote_identifier(identifier: str) -> str:
    return '"' + str(identifier).replace('"', '""') + '"'


def _count_nonempty_rows(conn: sqlite3.Connection, table_name: str, column_name: str) -> int:
    sql = (
        f"SELECT COUNT(*) FROM {_quote_identifier(table_name)} "
        f"WHERE TRIM(COALESCE(CAST({_quote_identifier(column_name)} AS TEXT), '')) <> ''"
    )
    row = conn.execute(sql).fetchone()
    return int(row[0] or 0) if row else 0


def _sample_nonempty_values(
    conn: sqlite3.Connection,
    table_name: str,
    column_name: str,
    *,
    limit: int = 5,
) -> list[str]:
    sql = (
        f"SELECT DISTINCT CAST({_quote_identifier(column_name)} AS TEXT) "
        f"FROM {_quote_identifier(table_name)} "
        f"WHERE TRIM(COALESCE(CAST({_quote_identifier(column_name)} AS TEXT), '')) <> '' "
        f"LIMIT {max(1, int(limit))}"
    )
    rows = conn.execute(sql).fetchall()
    return [str(row[0]) for row in rows if row and str(row[0]).strip()]


def _counter_to_ranked(counter: Counter[str], *, limit: int = 10) -> list[dict[str, Any]]:
    return [
        {"topic": topic, "count": count} for topic, count in counter.most_common(max(1, int(limit)))
    ]


def _audit_frontier(
    db_path: Path,
    *,
    topic_columns: Sequence[str],
    frontier_limit: int,
) -> dict[str, Any]:
    resolved_path = db_path.resolve()
    if not resolved_path.exists():
        return {
            "limit_requested": max(0, int(frontier_limit)),
            "row_count": 0,
            "resolved_rank_column": None,
            "resolved_topic_columns": [],
            "rows_with_raw_topics": 0,
            "rows_with_canonical_topics": 0,
            "raw_topic_coverage_ratio": 0.0,
            "canonical_topic_coverage_ratio": 0.0,
            "top_raw_topics": [],
            "top_canonical_topics": [],
        }

    with SqliteFrequencyStore(SqliteFrequencyConfig(path=resolved_path)) as store:
        available_columns = store.column_names()
        resolved_rank_column = store.resolve_rank_column(available_columns=available_columns)
        resolved_topic_columns = tuple(
            dict.fromkeys(
                column
                for column in (
                    store.resolve_column(topic_column, available_columns=available_columns)
                    for topic_column in topic_columns
                )
                if column
            )
        )
        if not resolved_topic_columns:
            return {
                "limit_requested": max(0, int(frontier_limit)),
                "row_count": 0,
                "resolved_rank_column": resolved_rank_column,
                "resolved_topic_columns": [],
                "rows_with_raw_topics": 0,
                "rows_with_canonical_topics": 0,
                "raw_topic_coverage_ratio": 0.0,
                "canonical_topic_coverage_ratio": 0.0,
                "top_raw_topics": [],
                "top_canonical_topics": [],
            }

        frontier_rows = list(
            store.iter_top_by_rank(
                limit=max(0, int(frontier_limit)),
                rank_column=resolved_rank_column,
                columns=resolved_topic_columns,
            )
        )
        raw_counter: Counter[str] = Counter()
        canonical_counter: Counter[str] = Counter()
        rows_with_raw_topics = 0
        rows_with_canonical_topics = 0
        for row in frontier_rows:
            raw_topics: set[str] = set()
            canonical_topics: set[str] = set()
            for column_name in resolved_topic_columns:
                raw_topics.update(normalize_topic_string_list(row[column_name]))
                expanded_topics, _origins = normalize_topic_string_list_with_origins(
                    row[column_name]
                )
                canonical_topics.update(expanded_topics)
            if raw_topics:
                rows_with_raw_topics += 1
                raw_counter.update(raw_topics)
            if canonical_topics:
                rows_with_canonical_topics += 1
                canonical_counter.update(canonical_topics)
        row_count = len(frontier_rows)
        return {
            "limit_requested": max(0, int(frontier_limit)),
            "row_count": row_count,
            "resolved_rank_column": resolved_rank_column,
            "resolved_topic_columns": list(resolved_topic_columns),
            "rows_with_raw_topics": rows_with_raw_topics,
            "rows_with_canonical_topics": rows_with_canonical_topics,
            "raw_topic_coverage_ratio": round(rows_with_raw_topics / max(1, row_count), 6),
            "canonical_topic_coverage_ratio": round(
                rows_with_canonical_topics / max(1, row_count), 6
            ),
            "top_raw_topics": _counter_to_ranked(raw_counter),
            "top_canonical_topics": _counter_to_ranked(canonical_counter),
        }


def audit_frequency_db(
    db_path: Path,
    *,
    topic_columns: Sequence[str] = DEFAULT_TOPIC_COLUMNS,
    frontier_limit: int = DEFAULT_FRONTIER_LIMIT,
) -> dict[str, Any]:
    resolved_path = db_path.resolve()
    if not resolved_path.exists():
        return {
            "db_path": str(resolved_path),
            "exists": False,
            "table_name": None,
            "row_count": 0,
            "available_columns": [],
            "topic_columns_requested": list(topic_columns),
            "topic_columns_present": [],
            "topic_columns_missing": list(topic_columns),
            "any_topic_rows": 0,
            "topic_columns": {},
            "frontier": _audit_frontier(
                resolved_path,
                topic_columns=topic_columns,
                frontier_limit=frontier_limit,
            ),
        }

    conn = sqlite3.connect(resolved_path)
    try:
        table_name = _resolve_frequency_table(conn)
        if not table_name:
            return {
                "db_path": str(resolved_path),
                "exists": True,
                "table_name": None,
                "row_count": 0,
                "available_columns": [],
                "topic_columns_requested": list(topic_columns),
                "topic_columns_present": [],
                "topic_columns_missing": list(topic_columns),
                "any_topic_rows": 0,
                "topic_columns": {},
                "frontier": _audit_frontier(
                    resolved_path,
                    topic_columns=topic_columns,
                    frontier_limit=frontier_limit,
                ),
            }
        available_columns = _column_names(conn, table_name)
        available_set = {column.casefold(): column for column in available_columns}
        present_topic_columns = [
            available_set[column.casefold()]
            for column in topic_columns
            if column.casefold() in available_set
        ]
        column_reports: dict[str, Any] = {}
        any_topic_rows = 0
        total_row_count = _count_rows(conn, table_name)
        for column_name in present_topic_columns:
            nonempty_rows = _count_nonempty_rows(conn, table_name, column_name)
            any_topic_rows = max(any_topic_rows, nonempty_rows)
            column_reports[column_name] = {
                "nonempty_rows": nonempty_rows,
                "nonempty_ratio": round(
                    (nonempty_rows / max(1, total_row_count)),
                    6,
                ),
                "sample_values": _sample_nonempty_values(conn, table_name, column_name),
            }
        return {
            "db_path": str(resolved_path),
            "exists": True,
            "table_name": table_name,
            "row_count": total_row_count,
            "available_columns": available_columns,
            "topic_columns_requested": list(topic_columns),
            "topic_columns_present": present_topic_columns,
            "topic_columns_missing": [
                column for column in topic_columns if column not in present_topic_columns
            ],
            "any_topic_rows": any_topic_rows,
            "topic_columns": column_reports,
            "frontier": _audit_frontier(
                resolved_path,
                topic_columns=topic_columns,
                frontier_limit=frontier_limit,
            ),
        }
    finally:
        conn.close()


def build_report(
    db_paths: Iterable[Path],
    *,
    topic_columns: Sequence[str] = DEFAULT_TOPIC_COLUMNS,
    frontier_limit: int = DEFAULT_FRONTIER_LIMIT,
) -> dict[str, Any]:
    audits = [
        audit_frequency_db(
            Path(db_path),
            topic_columns=topic_columns,
            frontier_limit=frontier_limit,
        )
        for db_path in db_paths
    ]
    findings: list[dict[str, Any]] = []
    for audit in audits:
        db_path = str(audit["db_path"])
        if not audit["exists"]:
            findings.append(
                _finding(
                    level="FAIL",
                    code="FREQUENCY_DB_MISSING",
                    db_path=db_path,
                    message="Frequency DB does not exist.",
                )
            )
            continue
        if not audit["table_name"]:
            findings.append(
                _finding(
                    level="FAIL",
                    code="FREQUENCY_TABLE_UNRESOLVED",
                    db_path=db_path,
                    message="Could not resolve a usable frequency table.",
                )
            )
            continue
        if not audit["topic_columns_present"]:
            findings.append(
                _finding(
                    level="WARN",
                    code="TOPIC_COLUMNS_ABSENT",
                    db_path=db_path,
                    message=(
                        "No requested topic columns are present, so profile-topic matching "
                        "would rely on lexical exact-match fallback only."
                    ),
                    details=", ".join(audit["topic_columns_missing"]),
                )
            )
            continue
        if int(audit["any_topic_rows"] or 0) <= 0:
            findings.append(
                _finding(
                    level="WARN",
                    code="TOPIC_COLUMNS_EMPTY",
                    db_path=db_path,
                    message="Topic columns exist but currently contain no non-empty rows.",
                    details=", ".join(audit["topic_columns_present"]),
                )
            )
            continue
        findings.append(
            _finding(
                level="PASS",
                code="TOPIC_COLUMNS_PRESENT",
                db_path=db_path,
                message="Topic columns are present with non-empty rows.",
                details=", ".join(audit["topic_columns_present"]),
            )
        )
        frontier = audit.get("frontier") if isinstance(audit.get("frontier"), Mapping) else {}
        if int(frontier.get("row_count") or 0) <= 0:
            findings.append(
                _finding(
                    level="WARN",
                    code="FRONTIER_EMPTY",
                    db_path=db_path,
                    message="Bootstrap frontier audit returned no rows.",
                    details=str(frontier.get("limit_requested") or 0),
                )
            )
        elif int(frontier.get("rows_with_canonical_topics") or 0) <= 0:
            findings.append(
                _finding(
                    level="WARN",
                    code="FRONTIER_TOPICS_EMPTY",
                    db_path=db_path,
                    message=(
                        "Topic columns exist, but the bootstrap frontier currently contains no "
                        "canonical topic metadata."
                    ),
                    details=(
                        f"limit={frontier.get('limit_requested')}, "
                        f"rank_column={frontier.get('resolved_rank_column') or 'n/a'}"
                    ),
                )
            )
        else:
            findings.append(
                _finding(
                    level="PASS",
                    code="FRONTIER_TOPICS_PRESENT",
                    db_path=db_path,
                    message=(
                        "Bootstrap frontier contains candidates with canonical topic metadata."
                    ),
                    details=(
                        f"rows={frontier.get('row_count')}, "
                        f"canonical_rows={frontier.get('rows_with_canonical_topics')}"
                    ),
                )
            )
    summary = summarize_findings(findings)
    return {
        "generated_at": _now_iso_utc(),
        "topic_columns_requested": list(topic_columns),
        "frontier_limit": max(0, int(frontier_limit)),
        "audits": audits,
        "findings": findings,
        "summary": summary,
    }


def render_markdown(report: Mapping[str, Any]) -> str:
    lines = [
        "# SRS Frequency Topic Coverage",
        "",
        f"- status: {report['summary']['status']}",
        f"- pass_count: {report['summary']['pass_count']}",
        f"- warn_count: {report['summary']['warn_count']}",
        f"- fail_count: {report['summary']['fail_count']}",
        f"- topic_columns_requested: {', '.join(report['topic_columns_requested'])}",
        f"- frontier_limit: {report.get('frontier_limit', DEFAULT_FRONTIER_LIMIT)}",
        "",
        "## Findings",
    ]
    for finding in report["findings"]:
        details = f" ({finding['details']})" if finding.get("details") else ""
        lines.append(
            f"- {finding['level']} `{finding['code']}` [{finding['db_path']}]: "
            f"{finding['message']}{details}"
        )
    lines.append("")
    lines.append("## Per-DB audit")
    for audit in report["audits"]:
        lines.extend(
            [
                "",
                f"### {audit['db_path']}",
                f"- exists: {audit['exists']}",
                f"- table_name: {audit['table_name']}",
                f"- row_count: {audit['row_count']}",
                f"- topic_columns_present: {', '.join(audit['topic_columns_present']) or 'none'}",
                f"- topic_columns_missing: {', '.join(audit['topic_columns_missing']) or 'none'}",
                f"- any_topic_rows: {audit['any_topic_rows']}",
            ]
        )
        frontier = audit.get("frontier") if isinstance(audit.get("frontier"), Mapping) else {}
        if frontier:
            lines.extend(
                [
                    f"- frontier_row_count: {frontier.get('row_count', 0)}",
                    f"- frontier_rank_column: {frontier.get('resolved_rank_column') or 'n/a'}",
                    (
                        "- frontier_topic_columns: "
                        f"{', '.join(frontier.get('resolved_topic_columns', [])) or 'none'}"
                    ),
                    f"- frontier_rows_with_raw_topics: {frontier.get('rows_with_raw_topics', 0)}",
                    (
                        "- frontier_rows_with_canonical_topics: "
                        f"{frontier.get('rows_with_canonical_topics', 0)}"
                    ),
                    (
                        "- frontier_canonical_topic_coverage_ratio: "
                        f"{frontier.get('canonical_topic_coverage_ratio', 0.0)}"
                    ),
                    (
                        "- frontier_top_canonical_topics: "
                        + (
                            ", ".join(
                                f"{entry['topic']}={entry['count']}"
                                for entry in frontier.get("top_canonical_topics", [])
                            )
                            or "none"
                        )
                    ),
                ]
            )
    return "\n".join(lines) + "\n"


def _write_json(path: Path | None, payload: Mapping[str, Any]) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"json_out: {path}")


def _write_markdown(path: Path | None, content: str) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"markdown_out: {path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Audit live frequency SQLite packs for the topic columns that SRS admission "
            "preference routing expects."
        )
    )
    parser.add_argument("--db", type=Path, action="append", required=True)
    parser.add_argument("--frontier-limit", type=int, default=DEFAULT_FRONTIER_LIMIT)
    parser.add_argument("--json-out", type=Path, default=None)
    parser.add_argument("--markdown-out", type=Path, default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.db, frontier_limit=args.frontier_limit)
    markdown = render_markdown(report)
    _write_json(args.json_out, report)
    _write_markdown(args.markdown_out, markdown)
    print(json.dumps(report["summary"], ensure_ascii=False))
    return 1 if int(report["summary"]["fail_count"]) > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
