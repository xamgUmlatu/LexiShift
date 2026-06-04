#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
import sys
from typing import Iterable, Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / "core"
SCRIPT_ROOT = Path(__file__).resolve().parent
TEST_OUTPUTS_ROOT = PROJECT_ROOT / "docs" / "test_outputs"
if str(CORE_ROOT) not in sys.path:
    sys.path.insert(0, str(CORE_ROOT))
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from lexishift_core.frequency.sqlite_store import (  # noqa: E402
    FREQUENCY_VALUE_COLUMNS,
    RANK_COLUMNS,
)
from lexishift_core.srs.admission_features import normalize_topic_string_list  # noqa: E402
from semantic_veto_product_quality_en_es import _as_mapping, _load_json, _repo_path  # noqa: E402


DEFAULT_PAIR = "en-es"
DEFAULT_BRIDGE_JSON = TEST_OUTPUTS_ROOT / "semantic_veto_srs_zipf_bridge_en_es_latest.json"
DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / "semantic_veto_srs_corpus_expansion_audit_en_es_latest.json"
DEFAULT_MARKDOWN_OUT = (
    TEST_OUTPUTS_ROOT / "semantic_veto_srs_corpus_expansion_audit_en_es_latest.md"
)
DEFAULT_TARGET_SIZES = (2000, 5000, 10000)
LEMMA_COLUMNS = ("lemma", "word", "surface", "form")
POS_COLUMNS = ("pos", "part_of_speech", "upos", "tag")
TOPIC_COLUMNS = ("sense_topics", "topics", "topic", "profile_topics", "domain", "domains")
PREFERRED_TABLE_NAMES = ("frequency", "freq", "lemmas", "words")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Audit en-es SRS corpus expansion candidates without changing SRS, rulegen, "
            "semantic-veto evidence, or paid-generation state."
        )
    )
    parser.add_argument("--pair", default=DEFAULT_PAIR)
    parser.add_argument(
        "--bridge-json",
        type=Path,
        default=DEFAULT_BRIDGE_JSON,
        help=(
            "Existing SRS Zipf bridge artifact used to locate the current installed "
            "frequency DB when --candidate-db is omitted."
        ),
    )
    parser.add_argument(
        "--candidate-db",
        type=Path,
        action="append",
        default=None,
        help="Frequency SQLite candidate to audit. May be repeated.",
    )
    parser.add_argument(
        "--target-size",
        type=int,
        action="append",
        default=None,
        help="Target learner-corpus size to assess. Defaults to 2000, 5000, and 10000.",
    )
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--fail-on-error", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    bridge_payload = _load_json(args.bridge_json)
    candidate_dbs = args.candidate_db or _candidate_dbs_from_bridge(bridge_payload)
    report = build_corpus_expansion_audit_report(
        pair=str(args.pair),
        candidate_dbs=candidate_dbs,
        bridge_payload=bridge_payload,
        bridge_path=args.bridge_json,
        target_sizes=args.target_size or DEFAULT_TARGET_SIZES,
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.markdown_out.write_text(render_corpus_expansion_markdown(report), encoding="utf-8")
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    if args.fail_on_error and report["summary"]["error_candidate_count"]:
        return 1
    return 0


def build_corpus_expansion_audit_report(
    *,
    pair: str = DEFAULT_PAIR,
    candidate_dbs: Iterable[Path],
    bridge_payload: Mapping[str, object] | None = None,
    bridge_path: Path | None = None,
    target_sizes: Sequence[int] = DEFAULT_TARGET_SIZES,
    generated_at: str | None = None,
) -> dict[str, object]:
    target_sizes = tuple(sorted({max(1, int(size)) for size in target_sizes}))
    bridge_payload = _as_mapping(bridge_payload)
    candidate_paths = [Path(path) for path in candidate_dbs]
    audits = [
        audit_frequency_candidate(
            path=path,
            label="current_bridge_frequency_db" if index == 0 else f"candidate_{index + 1}",
            target_sizes=target_sizes,
        )
        for index, path in enumerate(candidate_paths)
    ]
    summary = _build_summary(audits, target_sizes=target_sizes)
    return {
        "schema_version": 1,
        "pair": str(pair or DEFAULT_PAIR).strip().lower() or DEFAULT_PAIR,
        "generated_at": generated_at or _utc_now(),
        "decision": "srs_corpus_expansion_candidates_audited",
        "runtime_policy_change": "none",
        "llm_generation": "none",
        "inputs": {
            "bridge_json": _repo_path(bridge_path),
            "bridge_decision": str(bridge_payload.get("decision") or ""),
            "candidate_db_count": len(candidate_paths),
            "target_sizes": list(target_sizes),
        },
        "methodology": {
            "purpose": (
                "Compare possible Spanish learner-corpus/frequency-pack sources before "
                "expanding SRS admission, rulegen denominator, or semantic-veto generation."
            ),
            "acceptance_for_first_expansion": (
                "A candidate should have at least the chosen target-size of distinct non-empty "
                "lemmas, usable ordering through rank or frequency, POS coverage sufficient for "
                "admission weighting, and ideally topic/domain metadata for user-preference "
                "selection."
            ),
            "not_a_quality_claim": (
                "This audit does not prove replacement accuracy. It only measures whether a "
                "source can feed the existing SRS/rulegen/veto pipeline without hidden ceilings."
            ),
        },
        "summary": summary,
        "audits": audits,
        "candidate_source_research_matrix": _candidate_source_research_matrix(),
        "recommended_next_steps": _recommended_next_steps(summary),
    }


def audit_frequency_candidate(
    *,
    path: Path,
    label: str,
    target_sizes: Sequence[int] = DEFAULT_TARGET_SIZES,
) -> dict[str, object]:
    resolved_path = Path(path).expanduser().resolve(strict=False)
    base: dict[str, object] = {
        "label": label,
        "path": str(resolved_path),
        "exists": resolved_path.exists(),
        "status": "ok",
        "issues": [],
        "target_readiness": [],
    }
    if not resolved_path.exists() or not resolved_path.is_file():
        base["status"] = "error"
        base["issues"] = ["candidate_db_missing"]
        return base
    try:
        with resolved_path.open("rb") as handle:
            header = handle.read(16)
    except OSError as exc:
        base["status"] = "error"
        base["issues"] = [f"candidate_db_unreadable:{exc.__class__.__name__}"]
        return base
    if not header.startswith(b"SQLite format 3"):
        base["status"] = "error"
        base["issues"] = ["candidate_db_not_sqlite"]
        return base

    try:
        with sqlite3.connect(resolved_path) as conn:
            table_names = _table_names(conn)
            table_name = _resolve_frequency_table(table_names)
            if not table_name:
                base.update(
                    {
                        "status": "error",
                        "issues": ["frequency_table_unresolved"],
                        "table_names": table_names,
                    }
                )
                return base
            columns = _column_names(conn, table_name)
            resolved = {
                "lemma": _resolve_preferred(columns, LEMMA_COLUMNS),
                "rank": _resolve_preferred(columns, RANK_COLUMNS),
                "frequency": _resolve_preferred(columns, FREQUENCY_VALUE_COLUMNS),
                "pos": _resolve_preferred(columns, POS_COLUMNS),
                "topics": [
                    column
                    for column in (
                        _resolve_preferred(columns, (topic_column,))
                        for topic_column in TOPIC_COLUMNS
                    )
                    if column
                ],
            }
            row_count = _count_rows(conn, table_name)
            unique_lemma_count = (
                _count_distinct_nonempty(conn, table_name, str(resolved["lemma"]))
                if resolved["lemma"]
                else 0
            )
            pos_nonempty = (
                _count_nonempty(conn, table_name, str(resolved["pos"])) if resolved["pos"] else 0
            )
            rank_nonempty = (
                _count_nonempty(conn, table_name, str(resolved["rank"])) if resolved["rank"] else 0
            )
            frequency_nonempty = (
                _count_nonempty(conn, table_name, str(resolved["frequency"]))
                if resolved["frequency"]
                else 0
            )
            topic_columns = [str(column) for column in resolved["topics"]]
            topic_coverage = _topic_coverage(conn, table_name, topic_columns)
            issues = _candidate_issues(
                row_count=row_count,
                unique_lemma_count=unique_lemma_count,
                resolved_columns=resolved,
                pos_nonempty=pos_nonempty,
                rank_nonempty=rank_nonempty,
                frequency_nonempty=frequency_nonempty,
                topic_rows=int(topic_coverage["rows_with_any_topic"]),
                target_sizes=target_sizes,
            )
            base.update(
                {
                    "status": "review" if issues else "ok",
                    "issues": issues,
                    "table_names": table_names,
                    "table_name": table_name,
                    "row_count": row_count,
                    "unique_lemma_count": unique_lemma_count,
                    "duplicate_or_empty_lemma_rows": max(0, row_count - unique_lemma_count),
                    "available_columns": columns,
                    "resolved_columns": resolved,
                    "column_coverage": {
                        "lemma_nonempty_rows": _count_nonempty(
                            conn, table_name, str(resolved["lemma"])
                        )
                        if resolved["lemma"]
                        else 0,
                        "rank_nonempty_rows": rank_nonempty,
                        "frequency_nonempty_rows": frequency_nonempty,
                        "pos_nonempty_rows": pos_nonempty,
                        "pos_nonempty_share": _ratio(pos_nonempty, row_count),
                        "topic_rows_with_any_topic": int(topic_coverage["rows_with_any_topic"]),
                        "topic_row_share": _ratio(
                            int(topic_coverage["rows_with_any_topic"]), row_count
                        ),
                    },
                    "topic_coverage": topic_coverage,
                    "target_readiness": _target_readiness(
                        unique_lemma_count=unique_lemma_count,
                        target_sizes=target_sizes,
                    ),
                    "meta": _read_meta(conn),
                }
            )
            return base
    except sqlite3.Error as exc:
        base["status"] = "error"
        base["issues"] = [f"sqlite_error:{exc.__class__.__name__}"]
        return base


def render_corpus_expansion_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# en-es SRS Corpus Expansion Audit",
        "",
        f"- Status: `{summary.get('status')}`",
        f"- Decision: `{report.get('decision')}`",
        f"- Generated: `{report.get('generated_at')}`",
        f"- Candidate DBs: `{summary.get('candidate_count')}`",
        f"- Current candidate unique lemmas: `{summary.get('current_unique_lemma_count')}`",
        f"- Largest candidate unique lemmas: `{summary.get('largest_unique_lemma_count')}`",
        f"- Candidate reaching 5k: `{summary.get('candidate_reaching_5000')}`",
        f"- Candidate reaching 10k: `{summary.get('candidate_reaching_10000')}`",
        "",
        "## Why This Exists",
        "",
        str(_as_mapping(report.get("methodology")).get("purpose") or ""),
        "",
        "This is a source-readiness audit. It does not change SRS admission, rulegen, "
        "semantic-veto evidence, runtime policy, or paid generation.",
        "",
        "## Candidate Summary",
        "",
        "| Candidate | Status | Unique Lemmas | Rows | Rank | Frequency | POS Share | Topic Share | Issues |",
        "| --- | --- | ---: | ---: | --- | --- | ---: | ---: | --- |",
    ]
    for audit in _mapping_rows(report.get("audits")):
        resolved = _as_mapping(audit.get("resolved_columns"))
        coverage = _as_mapping(audit.get("column_coverage"))
        lines.append(
            "| "
            f"`{_escape_pipe(str(audit.get('label') or 'candidate'))}` | "
            f"`{audit.get('status')}` | "
            f"{int(audit.get('unique_lemma_count') or 0)} | "
            f"{int(audit.get('row_count') or 0)} | "
            f"`{resolved.get('rank') or 'none'}` | "
            f"`{resolved.get('frequency') or 'none'}` | "
            f"{_format_ratio(coverage.get('pos_nonempty_share'))} | "
            f"{_format_ratio(coverage.get('topic_row_share'))} | "
            f"{_format_issues(audit.get('issues'))} |"
        )
    lines.extend(
        [
            "",
            "## Target Readiness",
            "",
            "| Candidate | Target | Reaches Target | Shortfall | Available Share |",
            "| --- | ---: | --- | ---: | ---: |",
        ]
    )
    for audit in _mapping_rows(report.get("audits")):
        for row in _mapping_rows(audit.get("target_readiness")):
            lines.append(
                "| "
                f"`{_escape_pipe(str(audit.get('label') or 'candidate'))}` | "
                f"{int(row.get('target_size') or 0)} | "
                f"`{bool(row.get('reaches_target'))}` | "
                f"{int(row.get('shortfall') or 0)} | "
                f"{_format_ratio(row.get('available_share'))} |"
            )
    lines.extend(
        [
            "",
            "## Candidate Source Research Matrix",
            "",
            "| Source Family | What It Could Improve | Main Risk | First Check |",
            "| --- | --- | --- | --- |",
        ]
    )
    for row in _mapping_rows(report.get("candidate_source_research_matrix")):
        lines.append(
            "| "
            f"{_escape_pipe(str(row.get('source_family') or ''))} | "
            f"{_escape_pipe(str(row.get('could_improve') or ''))} | "
            f"{_escape_pipe(str(row.get('main_risk') or ''))} | "
            f"{_escape_pipe(str(row.get('first_check') or ''))} |"
        )
    lines.extend(["", "## Recommended Next Steps", ""])
    for index, item in enumerate(report.get("recommended_next_steps") or [], start=1):
        lines.append(f"{index}. {item}")
    lines.append("")
    return "\n".join(lines)


def _candidate_dbs_from_bridge(payload: Mapping[str, object]) -> list[Path]:
    full_srs = _as_mapping(_as_mapping(payload.get("inputs")).get("full_srs"))
    frequency_db = str(full_srs.get("frequency_db") or "").strip()
    if not frequency_db:
        return []
    return [Path(frequency_db)]


def _build_summary(
    audits: Sequence[Mapping[str, object]],
    *,
    target_sizes: Sequence[int],
) -> dict[str, object]:
    candidate_count = len(audits)
    error_candidate_count = sum(1 for audit in audits if audit.get("status") == "error")
    review_candidate_count = sum(1 for audit in audits if audit.get("status") == "review")
    unique_counts = [int(audit.get("unique_lemma_count") or 0) for audit in audits]
    current_unique = unique_counts[0] if unique_counts else 0
    largest_unique = max(unique_counts, default=0)
    target_flags = {
        f"candidate_reaching_{target_size}": any(count >= target_size for count in unique_counts)
        for target_size in target_sizes
    }
    expansion_blockers: list[str] = []
    if candidate_count <= 0:
        expansion_blockers.append("no_candidate_db_supplied_or_resolved")
    if largest_unique < 5000:
        expansion_blockers.append("no_candidate_reaches_5000_distinct_lemmas")
    if not any(_as_mapping(audit.get("resolved_columns")).get("pos") for audit in audits):
        expansion_blockers.append("no_candidate_has_pos_column")
    if not any(
        int(_as_mapping(audit.get("column_coverage")).get("topic_rows_with_any_topic") or 0) > 0
        for audit in audits
    ):
        expansion_blockers.append("no_candidate_has_topic_or_domain_rows")
    status = "error" if error_candidate_count else "review" if expansion_blockers else "ok"
    return {
        "status": status,
        "candidate_count": candidate_count,
        "error_candidate_count": error_candidate_count,
        "review_candidate_count": review_candidate_count,
        "current_unique_lemma_count": current_unique,
        "largest_unique_lemma_count": largest_unique,
        "target_sizes": list(target_sizes),
        "expansion_blockers": expansion_blockers,
        **target_flags,
    }


def _candidate_issues(
    *,
    row_count: int,
    unique_lemma_count: int,
    resolved_columns: Mapping[str, object],
    pos_nonempty: int,
    rank_nonempty: int,
    frequency_nonempty: int,
    topic_rows: int,
    target_sizes: Sequence[int],
) -> list[str]:
    issues: list[str] = []
    if row_count <= 0:
        issues.append("empty_candidate")
    if not resolved_columns.get("lemma"):
        issues.append("missing_lemma_column")
    if not resolved_columns.get("rank") and not resolved_columns.get("frequency"):
        issues.append("missing_rank_or_frequency_column")
    if unique_lemma_count < min(target_sizes):
        issues.append(f"below_smallest_target_size:{min(target_sizes)}")
    if unique_lemma_count < 5000:
        issues.append("below_5000_distinct_lemmas")
    if not resolved_columns.get("pos") or pos_nonempty <= 0:
        issues.append("missing_or_empty_pos_column")
    if rank_nonempty <= 0 and frequency_nonempty <= 0:
        issues.append("empty_ordering_columns")
    if topic_rows <= 0:
        issues.append("missing_or_empty_topic_domain_metadata")
    return issues


def _target_readiness(
    *,
    unique_lemma_count: int,
    target_sizes: Sequence[int],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for target_size in target_sizes:
        target_size = max(1, int(target_size))
        rows.append(
            {
                "target_size": target_size,
                "reaches_target": unique_lemma_count >= target_size,
                "shortfall": max(0, target_size - unique_lemma_count),
                "available_share": _ratio(unique_lemma_count, target_size),
            }
        )
    return rows


def _topic_coverage(
    conn: sqlite3.Connection,
    table_name: str,
    topic_columns: Sequence[str],
) -> dict[str, object]:
    column_reports: dict[str, object] = {}
    rows_with_any_topic: set[int] = set()
    topic_counter: Counter[str] = Counter()
    for column_name in topic_columns:
        rows = conn.execute(
            f"SELECT rowid, {_quote_identifier(column_name)} FROM {_quote_identifier(table_name)} "
            f"WHERE TRIM(COALESCE(CAST({_quote_identifier(column_name)} AS TEXT), '')) <> ''"
        ).fetchall()
        nonempty = 0
        for row_id, raw_value in rows:
            normalized_topics = normalize_topic_string_list(raw_value)
            if normalized_topics:
                nonempty += 1
                rows_with_any_topic.add(int(row_id))
                topic_counter.update(normalized_topics)
        column_reports[column_name] = {
            "nonempty_rows_after_normalization": nonempty,
            "sample_topics": [topic for topic, _count in topic_counter.most_common(8)],
        }
    return {
        "topic_columns": list(topic_columns),
        "rows_with_any_topic": len(rows_with_any_topic),
        "top_topics": [
            {"topic": topic, "count": count} for topic, count in topic_counter.most_common(12)
        ],
        "columns": column_reports,
    }


def _candidate_source_research_matrix() -> list[dict[str, str]]:
    return [
        {
            "source_family": "Recovered or rebuilt Spanish 20k frequency list",
            "could_improve": "Fastest path if it preserves the current pack's ordering semantics.",
            "main_risk": "May still lack topic/domain metadata and license/provenance clarity.",
            "first_check": "Confirm provenance, row count, POS coverage, and pack schema.",
        },
        {
            "source_family": "General frequency corpus",
            "could_improve": "Broad 5k-10k coverage for ordinary browsing and SRS.",
            "main_risk": "Frequency alone may overvalue function words or weak learner targets.",
            "first_check": "Measure lemma/POS quality and compare overlap with current 2k.",
        },
        {
            "source_family": "Learner-level or CEFR-style list",
            "could_improve": "Better alignment with staged learner progression.",
            "main_risk": "May be smaller, licensed restrictively, or missing frequency values.",
            "first_check": "Check level coverage and mergeability with frequency ranks.",
        },
        {
            "source_family": "Dictionary-derived lemma expansion",
            "could_improve": "Large coverage without waiting for a frequency source.",
            "main_risk": "No natural ranking; may admit obscure or awkward lemmas.",
            "first_check": "Require rank backfill, POS validation, and exclusion filters.",
        },
        {
            "source_family": "Domain/topic overlays",
            "could_improve": "Makes user preference SRS useful for medicine, law, travel, etc.",
            "main_risk": "Domain value is high but general-frequency comparability is weak.",
            "first_check": "Keep source/domain tags and blend as an overlay, not a replacement.",
        },
        {
            "source_family": "Hybrid base-frequency plus overlays",
            "could_improve": "Most product-aligned path: general coverage plus user-specific depth.",
            "main_risk": "Merge policy can hide provenance and duplicate lemmas if not audited.",
            "first_check": "Version the merged pack and audit per-source contribution.",
        },
    ]


def _recommended_next_steps(summary: Mapping[str, object]) -> list[str]:
    steps = [
        "Keep the current 2k frequency pack frozen as the baseline denominator.",
        "Recover or recreate the apparent Spanish 20k source before choosing a new corpus source.",
        "Run this audit on every candidate SQLite pack and compare row count, unique lemmas, POS coverage, and topic/domain coverage.",
    ]
    blockers = set(summary.get("expansion_blockers") or [])
    if "no_candidate_has_topic_or_domain_rows" in blockers:
        steps.append(
            "Treat topic/domain metadata as a second-track requirement: absence should not block a 5k general expansion, but it must be visible before claiming profile-personalized coverage."
        )
    if "no_candidate_reaches_5000_distinct_lemmas" in blockers:
        steps.append(
            "Do not start another paid semantic-veto generation wave until a larger learner-corpus source is installed or linked."
        )
    steps.append(
        "After selecting a candidate source, rerun the SRS Zipf bridge with full rulegen and then refresh the semantic-veto denominator audit."
    )
    return steps


def _table_names(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()
    return [str(row[0]) for row in rows if str(row[0]).strip()]


def _resolve_frequency_table(table_names: Sequence[str]) -> str | None:
    normalized = {name.casefold(): name for name in table_names}
    for preferred in PREFERRED_TABLE_NAMES:
        if preferred.casefold() in normalized:
            return normalized[preferred.casefold()]
    for table_name in table_names:
        if table_name.casefold() != "meta":
            return table_name
    return None


def _column_names(conn: sqlite3.Connection, table_name: str) -> list[str]:
    rows = conn.execute(f"PRAGMA table_info({_quote_identifier(table_name)})").fetchall()
    return [str(row[1]) for row in rows if len(row) > 1 and str(row[1]).strip()]


def _resolve_preferred(columns: Sequence[str], candidates: Sequence[str]) -> str | None:
    normalized = {column.casefold(): column for column in columns}
    for candidate in candidates:
        resolved = normalized.get(str(candidate).casefold())
        if resolved:
            return resolved
    return None


def _count_rows(conn: sqlite3.Connection, table_name: str) -> int:
    row = conn.execute(f"SELECT COUNT(*) FROM {_quote_identifier(table_name)}").fetchone()
    return int(row[0] or 0) if row else 0


def _count_nonempty(conn: sqlite3.Connection, table_name: str, column_name: str) -> int:
    row = conn.execute(
        f"SELECT COUNT(*) FROM {_quote_identifier(table_name)} "
        f"WHERE TRIM(COALESCE(CAST({_quote_identifier(column_name)} AS TEXT), '')) <> ''"
    ).fetchone()
    return int(row[0] or 0) if row else 0


def _count_distinct_nonempty(conn: sqlite3.Connection, table_name: str, column_name: str) -> int:
    row = conn.execute(
        f"SELECT COUNT(DISTINCT TRIM(CAST({_quote_identifier(column_name)} AS TEXT))) "
        f"FROM {_quote_identifier(table_name)} "
        f"WHERE TRIM(COALESCE(CAST({_quote_identifier(column_name)} AS TEXT), '')) <> ''"
    ).fetchone()
    return int(row[0] or 0) if row else 0


def _read_meta(conn: sqlite3.Connection) -> dict[str, object]:
    table_names = {name.casefold(): name for name in _table_names(conn)}
    meta_table = table_names.get("meta")
    if not meta_table:
        return {}
    columns = _column_names(conn, meta_table)
    if len(columns) < 2:
        return {"columns": columns}
    rows = conn.execute(
        f"SELECT {_quote_identifier(columns[0])}, {_quote_identifier(columns[1])} "
        f"FROM {_quote_identifier(meta_table)} LIMIT 50"
    ).fetchall()
    metadata: dict[str, object] = {}
    for key, value in rows:
        normalized_key = str(key or "").strip()
        if not normalized_key:
            continue
        value_text = str(value or "").strip()
        try:
            metadata[normalized_key] = json.loads(value_text)
        except json.JSONDecodeError:
            metadata[normalized_key] = value_text
    return metadata


def _quote_identifier(identifier: str) -> str:
    return '"' + str(identifier).replace('"', '""') + '"'


def _ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(min(1.0, max(0.0, numerator / denominator)), 6)


def _mapping_rows(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _format_ratio(value: object) -> str:
    try:
        return f"{float(value):.1%}"
    except (TypeError, ValueError):
        return "0.0%"


def _format_issues(value: object) -> str:
    if not isinstance(value, list) or not value:
        return "`none`"
    return ", ".join(f"`{_escape_pipe(str(item))}`" for item in value)


def _escape_pipe(value: str) -> str:
    return str(value).replace("|", "\\|")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


if __name__ == "__main__":
    raise SystemExit(main())
