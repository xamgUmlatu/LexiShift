#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
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
from lexishift_core.helper.paths import build_helper_paths  # noqa: E402
from lexishift_core.pos.normalization import normalize_pos  # noqa: E402
from semantic_veto_product_quality_en_es import _repo_path  # noqa: E402
from semantic_veto_srs_corpus_expansion_audit_en_es import (  # noqa: E402
    LEMMA_COLUMNS,
    _column_names,
    _quote_identifier,
    _resolve_frequency_table,
    _resolve_preferred,
    _table_names,
)
from semantic_veto_srs_candidate_pos_backfill_rendering import (  # noqa: E402
    build_chosen_pos_distribution,
    build_samples,
    candidate_pos_backfill_limitations,
    candidate_pos_backfill_recommended_next_steps,
    render_candidate_pos_backfill_markdown as render_candidate_pos_backfill_markdown,
)


DEFAULT_PAIR = "en-es"
DEFAULT_JSON_OUT = (
    TEST_OUTPUTS_ROOT / "semantic_veto_srs_candidate_pos_backfill_audit_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    TEST_OUTPUTS_ROOT / "semantic_veto_srs_candidate_pos_backfill_audit_en_es_latest.md"
)
DEFAULT_TARGET_SIZES = (2000, 5000, 10000)
POS_TABLE_SPECS = {
    "wiktionary_es_en": (
        ("entry_meta", "headword_lc", "pos"),
        ("sense_glosses", "headword_lc", "pos"),
    ),
    "freedict_es_en": (("entries", "headword_lc", "pos"),),
}
POS_SOURCE_PROFILES = {
    "wiktionary_es_en": "wiktionary",
    "freedict_es_en": "freedict",
}
SOURCE_PRIORITY = {
    ("wiktionary_es_en", "entry_meta"): 0,
    ("wiktionary_es_en", "sense_glosses"): 1,
    ("freedict_es_en", "entries"): 2,
}
BUCKET_PRIORITY = {
    "noun": 0,
    "adjective": 1,
    "verb": 2,
    "adverb": 3,
    "other": 4,
}


@dataclass(frozen=True)
class CandidateLemma:
    lemma: str
    row_number: int
    rank: object = None
    frequency: object = None
    original_pos: str = ""


@dataclass(frozen=True)
class PosEvidence:
    lemma: str
    source_id: str
    table_name: str
    raw_pos: str
    canonical: str
    bucket: str
    mapped: bool
    matched_rule: str

    def to_dict(self) -> dict[str, object]:
        return {
            "lemma": self.lemma,
            "source_id": self.source_id,
            "table_name": self.table_name,
            "raw_pos": self.raw_pos,
            "canonical": self.canonical,
            "bucket": self.bucket,
            "mapped": self.mapped,
            "matched_rule": self.matched_rule,
        }


def _parse_args() -> argparse.Namespace:
    default_language_packs = build_helper_paths().language_packs_dir
    parser = argparse.ArgumentParser(
        description=(
            "Audit whether installed en-es lexical resources can backfill POS for a "
            "candidate Spanish frequency SQLite without installing or mutating the candidate."
        )
    )
    parser.add_argument("--pair", default=DEFAULT_PAIR)
    parser.add_argument(
        "--candidate-db",
        type=Path,
        required=True,
        help="Candidate Spanish frequency SQLite to audit.",
    )
    parser.add_argument(
        "--wiktionary-es-en-sqlite",
        type=Path,
        default=default_language_packs / "wiktionary-es-en.sqlite",
    )
    parser.add_argument(
        "--freedict-es-en-sqlite",
        type=Path,
        default=default_language_packs / "freedict-es-en" / "main.sqlite",
    )
    parser.add_argument(
        "--target-size",
        type=int,
        action="append",
        default=None,
        help="Target corpus size to assess. Defaults to 2000, 5000, and 10000.",
    )
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--fail-on-error", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_candidate_pos_backfill_report(
        pair=str(args.pair),
        candidate_db=args.candidate_db,
        wiktionary_es_en_sqlite=args.wiktionary_es_en_sqlite,
        freedict_es_en_sqlite=args.freedict_es_en_sqlite,
        target_sizes=args.target_size or DEFAULT_TARGET_SIZES,
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.markdown_out.write_text(render_candidate_pos_backfill_markdown(report), encoding="utf-8")
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    if args.fail_on_error and report["summary"]["status"] == "error":
        return 1
    return 0


def build_candidate_pos_backfill_report(
    *,
    candidate_db: Path,
    wiktionary_es_en_sqlite: Path | None = None,
    freedict_es_en_sqlite: Path | None = None,
    pair: str = DEFAULT_PAIR,
    target_sizes: Sequence[int] = DEFAULT_TARGET_SIZES,
    generated_at: str | None = None,
) -> dict[str, object]:
    target_sizes = tuple(sorted({max(1, int(size)) for size in target_sizes}))
    candidate_report, candidate_rows = _read_candidate_lemmas(candidate_db)
    default_language_packs = build_helper_paths().language_packs_dir
    source_paths = {
        "wiktionary_es_en": wiktionary_es_en_sqlite
        or default_language_packs / "wiktionary-es-en.sqlite",
        "freedict_es_en": freedict_es_en_sqlite
        or default_language_packs / "freedict-es-en" / "main.sqlite",
    }
    source_reports, evidences_by_lemma = _read_pos_sources(
        source_paths=source_paths,
        candidate_lemmas=[row.lemma for row in candidate_rows],
        pair=pair,
    )
    lemma_reports = _build_lemma_reports(candidate_rows, evidences_by_lemma)
    summary = _build_summary(
        candidate_report=candidate_report,
        source_reports=source_reports,
        lemma_reports=lemma_reports,
        target_sizes=target_sizes,
    )
    return {
        "schema_version": 1,
        "pair": str(pair or DEFAULT_PAIR).strip().lower() or DEFAULT_PAIR,
        "generated_at": generated_at or _utc_now(),
        "decision": "candidate_pos_backfill_audited",
        "runtime_policy_change": "none",
        "candidate_db_mutation": "none",
        "llm_generation": "none",
        "inputs": {
            "candidate_db": _repo_path(candidate_db),
            "wiktionary_es_en_sqlite": _repo_path(wiktionary_es_en_sqlite),
            "freedict_es_en_sqlite": _repo_path(freedict_es_en_sqlite),
            "target_sizes": list(target_sizes),
        },
        "methodology": {
            "purpose": (
                "Measure whether installed Spanish-headword lexical resources can backfill POS "
                "for a candidate Spanish frequency source before it is promoted into SRS or "
                "semantic-veto denominator work."
            ),
            "join_policy": (
                "Exact lowercase candidate lemma to Spanish resource headword_lc only. "
                "English-to-Spanish translation rows are intentionally excluded because their "
                "POS describes the English source sense, not the Spanish candidate target."
            ),
            "mutation_policy": (
                "Diagnostic-only. The candidate frequency DB and installed language packs are "
                "read as inputs and are not modified."
            ),
        },
        "summary": summary,
        "candidate": candidate_report,
        "sources": source_reports,
        "target_readiness": _target_readiness(summary, target_sizes=target_sizes),
        "rank_band_coverage": _rank_band_coverage(lemma_reports, target_sizes=target_sizes),
        "chosen_pos_distribution": build_chosen_pos_distribution(lemma_reports),
        "samples": build_samples(lemma_reports),
        "limitations": candidate_pos_backfill_limitations(),
        "recommended_next_steps": candidate_pos_backfill_recommended_next_steps(summary),
    }


def _read_candidate_lemmas(path: Path) -> tuple[dict[str, object], list[CandidateLemma]]:
    resolved = Path(path).expanduser().resolve(strict=False)
    report: dict[str, object] = {
        "path": str(resolved),
        "exists": resolved.exists(),
        "status": "ok",
        "issues": [],
        "row_count": 0,
        "unique_lemma_count": 0,
    }
    if not resolved.exists() or not resolved.is_file():
        report["status"] = "error"
        report["issues"] = ["candidate_db_missing"]
        return report, []
    try:
        with resolved.open("rb") as handle:
            header = handle.read(16)
    except OSError as exc:
        report["status"] = "error"
        report["issues"] = [f"candidate_db_unreadable:{exc.__class__.__name__}"]
        return report, []
    if not header.startswith(b"SQLite format 3"):
        report["status"] = "error"
        report["issues"] = ["candidate_db_not_sqlite"]
        return report, []
    try:
        with sqlite3.connect(resolved) as conn:
            table_names = _table_names(conn)
            table_name = _resolve_frequency_table(table_names)
            if not table_name:
                report.update(
                    {
                        "status": "error",
                        "issues": ["frequency_table_unresolved"],
                        "table_names": table_names,
                    }
                )
                return report, []
            columns = _column_names(conn, table_name)
            lemma_column = _resolve_preferred(columns, LEMMA_COLUMNS)
            rank_column = _resolve_preferred(columns, RANK_COLUMNS)
            frequency_column = _resolve_preferred(columns, FREQUENCY_VALUE_COLUMNS)
            pos_column = _resolve_preferred(columns, ("pos", "part_of_speech", "upos", "tag"))
            if not lemma_column:
                report.update(
                    {
                        "status": "error",
                        "issues": ["missing_lemma_column"],
                        "table_names": table_names,
                        "table_name": table_name,
                        "available_columns": columns,
                    }
                )
                return report, []
            select_columns = [
                _quote_identifier(lemma_column),
                _quote_identifier(rank_column) if rank_column else "NULL",
                _quote_identifier(frequency_column) if frequency_column else "NULL",
                _quote_identifier(pos_column) if pos_column else "NULL",
            ]
            rows = conn.execute(
                "SELECT "
                + ", ".join(select_columns)
                + f" FROM {_quote_identifier(table_name)} "
                + f"WHERE TRIM(COALESCE(CAST({_quote_identifier(lemma_column)} AS TEXT), '')) <> '' "
                + "ORDER BY ROWID"
            ).fetchall()
    except sqlite3.Error as exc:
        report["status"] = "error"
        report["issues"] = [f"sqlite_error:{exc.__class__.__name__}"]
        return report, []

    seen: set[str] = set()
    candidate_rows: list[CandidateLemma] = []
    original_pos_count = 0
    for row_number, (lemma_value, rank_value, frequency_value, pos_value) in enumerate(
        rows,
        start=1,
    ):
        lemma = str(lemma_value or "").strip().lower()
        if not lemma or lemma in seen:
            continue
        seen.add(lemma)
        original_pos = str(pos_value or "").strip()
        if original_pos:
            original_pos_count += 1
        candidate_rows.append(
            CandidateLemma(
                lemma=lemma,
                row_number=row_number,
                rank=rank_value,
                frequency=frequency_value,
                original_pos=original_pos,
            )
        )
    report.update(
        {
            "status": "ok",
            "table_names": table_names,
            "table_name": table_name,
            "available_columns": columns,
            "resolved_columns": {
                "lemma": lemma_column,
                "rank": rank_column,
                "frequency": frequency_column,
                "pos": pos_column,
            },
            "row_count": len(rows),
            "unique_lemma_count": len(candidate_rows),
            "original_pos_nonempty_lemma_count": original_pos_count,
            "original_pos_nonempty_lemma_share": _ratio(original_pos_count, len(candidate_rows)),
        }
    )
    return report, candidate_rows


def _read_pos_sources(
    *,
    source_paths: Mapping[str, Path | None],
    candidate_lemmas: Sequence[str],
    pair: str,
) -> tuple[list[dict[str, object]], dict[str, list[PosEvidence]]]:
    candidate_set = set(candidate_lemmas)
    evidences_by_lemma: dict[str, list[PosEvidence]] = {lemma: [] for lemma in candidate_lemmas}
    reports: list[dict[str, object]] = []
    for source_id, raw_path in source_paths.items():
        report, evidences = _read_pos_source(
            source_id=source_id,
            path=raw_path,
            candidate_set=candidate_set,
            pair=pair,
        )
        reports.append(report)
        for evidence in evidences:
            evidences_by_lemma.setdefault(evidence.lemma, []).append(evidence)
    return reports, evidences_by_lemma


def _read_pos_source(
    *,
    source_id: str,
    path: Path | None,
    candidate_set: set[str],
    pair: str,
) -> tuple[dict[str, object], list[PosEvidence]]:
    resolved = Path(path).expanduser().resolve(strict=False) if path else None
    report: dict[str, object] = {
        "source_id": source_id,
        "path": str(resolved) if resolved else None,
        "exists": bool(resolved and resolved.exists()),
        "status": "ok",
        "issues": [],
        "usable_pos_row_count": 0,
        "distinct_source_lemma_count": 0,
        "candidate_hit_count": 0,
        "candidate_hit_share": 0.0,
        "tables": [],
    }
    if resolved is None or not resolved.exists() or not resolved.is_file():
        report["status"] = "review"
        report["issues"] = ["source_sqlite_missing"]
        return report, []
    try:
        with sqlite3.connect(resolved) as conn:
            table_names = set(_table_names(conn))
            source_lemmas: set[str] = set()
            hit_lemmas: set[str] = set()
            evidences: list[PosEvidence] = []
            for table_name, lemma_column, pos_column in POS_TABLE_SPECS.get(source_id, ()):
                table_report, table_evidences, table_source_lemmas, table_hit_lemmas = (
                    _read_pos_source_table(
                        conn=conn,
                        source_id=source_id,
                        table_name=table_name,
                        lemma_column=lemma_column,
                        pos_column=pos_column,
                        table_names=table_names,
                        candidate_set=candidate_set,
                        pair=pair,
                    )
                )
                report["tables"].append(table_report)
                report["usable_pos_row_count"] = int(report["usable_pos_row_count"]) + int(
                    table_report.get("usable_pos_row_count") or 0
                )
                source_lemmas.update(table_source_lemmas)
                hit_lemmas.update(table_hit_lemmas)
                evidences.extend(table_evidences)
    except sqlite3.Error as exc:
        report["status"] = "error"
        report["issues"] = [f"sqlite_error:{exc.__class__.__name__}"]
        return report, []

    report["distinct_source_lemma_count"] = len(source_lemmas)
    report["candidate_hit_count"] = len(hit_lemmas)
    report["candidate_hit_share"] = _ratio(len(hit_lemmas), len(candidate_set))
    if int(report["usable_pos_row_count"]) <= 0:
        report["status"] = "review"
        report["issues"] = [*list(report.get("issues") or []), "source_has_no_usable_pos_rows"]
    elif len(hit_lemmas) <= 0:
        report["status"] = "review"
        report["issues"] = [*list(report.get("issues") or []), "source_has_no_candidate_hits"]
    return report, _dedupe_evidences(evidences)


def _read_pos_source_table(
    *,
    conn: sqlite3.Connection,
    source_id: str,
    table_name: str,
    lemma_column: str,
    pos_column: str,
    table_names: set[str],
    candidate_set: set[str],
    pair: str,
) -> tuple[dict[str, object], list[PosEvidence], set[str], set[str]]:
    table_report: dict[str, object] = {
        "table_name": table_name,
        "status": "ok",
        "issues": [],
        "usable_pos_row_count": 0,
        "distinct_source_lemma_count": 0,
        "candidate_hit_count": 0,
    }
    if table_name not in table_names:
        table_report["status"] = "review"
        table_report["issues"] = ["table_missing"]
        return table_report, [], set(), set()
    columns = set(_column_names(conn, table_name))
    missing_columns = [column for column in (lemma_column, pos_column) if column not in columns]
    if missing_columns:
        table_report["status"] = "review"
        table_report["issues"] = [f"columns_missing:{','.join(missing_columns)}"]
        return table_report, [], set(), set()

    source_lemmas: set[str] = set()
    hit_lemmas: set[str] = set()
    evidences: list[PosEvidence] = []
    rows = conn.execute(
        f"SELECT {_quote_identifier(lemma_column)}, {_quote_identifier(pos_column)} "
        f"FROM {_quote_identifier(table_name)} "
        f"WHERE TRIM(COALESCE(CAST({_quote_identifier(lemma_column)} AS TEXT), '')) <> '' "
        f"AND TRIM(COALESCE(CAST({_quote_identifier(pos_column)} AS TEXT), '')) <> ''"
    )
    source_profile = POS_SOURCE_PROFILES.get(source_id, source_id)
    usable_row_count = 0
    for lemma_value, pos_value in rows:
        lemma = str(lemma_value or "").strip().lower()
        raw_pos = str(pos_value or "").strip()
        if not lemma or not raw_pos:
            continue
        usable_row_count += 1
        source_lemmas.add(lemma)
        if lemma not in candidate_set:
            continue
        hit_lemmas.add(lemma)
        normalized = normalize_pos(
            raw_pos,
            language_pair=pair,
            source_provider=source_profile,
            source_kind=source_profile,
            target_language="es",
        )
        evidences.append(
            PosEvidence(
                lemma=lemma,
                source_id=source_id,
                table_name=table_name,
                raw_pos=raw_pos,
                canonical=normalized.canonical,
                bucket=normalized.bucket,
                mapped=bool(normalized.mapped),
                matched_rule=normalized.matched_rule,
            )
        )
    table_report["usable_pos_row_count"] = usable_row_count
    table_report["distinct_source_lemma_count"] = len(source_lemmas)
    table_report["candidate_hit_count"] = len(hit_lemmas)
    return table_report, evidences, source_lemmas, hit_lemmas


def _dedupe_evidences(evidences: Iterable[PosEvidence]) -> list[PosEvidence]:
    seen: set[tuple[str, str, str, str]] = set()
    deduped: list[PosEvidence] = []
    for evidence in evidences:
        key = (evidence.lemma, evidence.source_id, evidence.table_name, evidence.raw_pos)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(evidence)
    return deduped


def _build_lemma_reports(
    candidate_rows: Sequence[CandidateLemma],
    evidences_by_lemma: Mapping[str, Sequence[PosEvidence]],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for candidate in candidate_rows:
        evidences = _dedupe_evidences(evidences_by_lemma.get(candidate.lemma, []))
        chosen = _choose_evidence(evidences)
        raw_pos_values = sorted({evidence.raw_pos for evidence in evidences})
        mapped_canonical_values = sorted(
            {evidence.canonical for evidence in evidences if evidence.mapped}
        )
        mapped_bucket_values = sorted(
            {evidence.bucket for evidence in evidences if evidence.mapped}
        )
        rows.append(
            {
                "lemma": candidate.lemma,
                "candidate_row_number": candidate.row_number,
                "original_pos": candidate.original_pos,
                "evidence_count": len(evidences),
                "sources": sorted({evidence.source_id for evidence in evidences}),
                "raw_pos_values": raw_pos_values,
                "mapped_canonical_values": mapped_canonical_values,
                "mapped_bucket_values": mapped_bucket_values,
                "has_any_pos": bool(evidences),
                "has_mapped_pos": bool(mapped_canonical_values),
                "has_weighted_lexical_bucket": (
                    len(mapped_bucket_values) == 1 and mapped_bucket_values[0] != "other"
                ),
                "ambiguous_raw_pos": len(raw_pos_values) > 1,
                "canonical_conflict": len(mapped_canonical_values) > 1,
                "chosen_pos": chosen.to_dict() if chosen else None,
            }
        )
    return rows


def _choose_evidence(evidences: Sequence[PosEvidence]) -> PosEvidence | None:
    if not evidences:
        return None
    return min(
        evidences,
        key=lambda evidence: (
            0 if evidence.mapped and evidence.bucket != "other" else 1 if evidence.mapped else 2,
            BUCKET_PRIORITY.get(evidence.bucket, 99),
            SOURCE_PRIORITY.get((evidence.source_id, evidence.table_name), 99),
            evidence.raw_pos,
        ),
    )


def _build_summary(
    *,
    candidate_report: Mapping[str, object],
    source_reports: Sequence[Mapping[str, object]],
    lemma_reports: Sequence[Mapping[str, object]],
    target_sizes: Sequence[int],
) -> dict[str, object]:
    candidate_count = int(candidate_report.get("unique_lemma_count") or 0)
    any_pos_count = sum(1 for row in lemma_reports if bool(row.get("has_any_pos")))
    mapped_pos_count = sum(1 for row in lemma_reports if bool(row.get("has_mapped_pos")))
    weighted_lexical_count = sum(
        1 for row in lemma_reports if bool(row.get("has_weighted_lexical_bucket"))
    )
    ambiguous_count = sum(1 for row in lemma_reports if bool(row.get("ambiguous_raw_pos")))
    canonical_conflict_count = sum(
        1 for row in lemma_reports if bool(row.get("canonical_conflict"))
    )
    source_error_count = sum(1 for row in source_reports if row.get("status") == "error")
    source_review_count = sum(1 for row in source_reports if row.get("status") == "review")
    issues: list[str] = []
    if candidate_report.get("status") == "error":
        issues.extend(str(issue) for issue in candidate_report.get("issues") or [])
    if candidate_count <= 0:
        issues.append("candidate_has_no_resolved_lemmas")
    if source_error_count:
        issues.append("pos_source_error")
    if any_pos_count <= 0 and candidate_count > 0:
        issues.append("no_external_pos_backfill_available")
    if mapped_pos_count < candidate_count and candidate_count > 0:
        issues.append("candidate_pos_backfill_incomplete")
    if target_sizes and mapped_pos_count < min(target_sizes):
        issues.append(f"mapped_pos_below_smallest_target_size:{min(target_sizes)}")
    if 5000 in set(target_sizes) and mapped_pos_count < 5000:
        issues.append("mapped_pos_below_5000_lemmas")
    if 10000 in set(target_sizes) and mapped_pos_count < 10000:
        issues.append("mapped_pos_below_10000_lemmas")
    status = (
        "error"
        if candidate_report.get("status") == "error" or source_error_count
        else ("review" if issues or source_review_count else "ok")
    )
    return {
        "status": status,
        "issues": sorted(dict.fromkeys(issues)),
        "candidate_unique_lemma_count": candidate_count,
        "original_pos_nonempty_lemma_count": int(
            candidate_report.get("original_pos_nonempty_lemma_count") or 0
        ),
        "original_pos_nonempty_lemma_share": candidate_report.get(
            "original_pos_nonempty_lemma_share",
            0.0,
        ),
        "any_pos_lemma_count": any_pos_count,
        "any_pos_lemma_share": _ratio(any_pos_count, candidate_count),
        "mapped_pos_lemma_count": mapped_pos_count,
        "mapped_pos_lemma_share": _ratio(mapped_pos_count, candidate_count),
        "weighted_lexical_bucket_lemma_count": weighted_lexical_count,
        "weighted_lexical_bucket_lemma_share": _ratio(weighted_lexical_count, candidate_count),
        "unresolved_lemma_count": max(0, candidate_count - any_pos_count),
        "unresolved_lemma_share": _ratio(max(0, candidate_count - any_pos_count), candidate_count),
        "ambiguous_raw_pos_lemma_count": ambiguous_count,
        "canonical_conflict_lemma_count": canonical_conflict_count,
        "source_error_count": source_error_count,
        "source_review_count": source_review_count,
    }


def _target_readiness(
    summary: Mapping[str, object],
    *,
    target_sizes: Sequence[int],
) -> list[dict[str, object]]:
    any_pos_count = int(summary.get("any_pos_lemma_count") or 0)
    mapped_pos_count = int(summary.get("mapped_pos_lemma_count") or 0)
    weighted_lexical_count = int(summary.get("weighted_lexical_bucket_lemma_count") or 0)
    rows: list[dict[str, object]] = []
    for target_size in target_sizes:
        target = max(1, int(target_size))
        rows.append(
            {
                "target_size": target,
                "any_pos_reaches_target": any_pos_count >= target,
                "mapped_pos_reaches_target": mapped_pos_count >= target,
                "weighted_lexical_bucket_reaches_target": weighted_lexical_count >= target,
                "any_pos_shortfall": max(0, target - any_pos_count),
                "mapped_pos_shortfall": max(0, target - mapped_pos_count),
                "weighted_lexical_bucket_shortfall": max(0, target - weighted_lexical_count),
            }
        )
    return rows


def _rank_band_coverage(
    lemma_reports: Sequence[Mapping[str, object]],
    *,
    target_sizes: Sequence[int],
) -> list[dict[str, object]]:
    total_count = len(lemma_reports)
    band_sizes = sorted(
        {
            size
            for size in (*target_sizes, 100, 250, 500, 1000, 2000, 5000, 10000)
            if 0 < int(size) <= max(1, total_count)
        }
    )
    rows: list[dict[str, object]] = []
    for band_size in band_sizes:
        scoped_rows = list(lemma_reports[:band_size])
        any_pos_count = sum(1 for row in scoped_rows if bool(row.get("has_any_pos")))
        mapped_pos_count = sum(1 for row in scoped_rows if bool(row.get("has_mapped_pos")))
        weighted_count = sum(
            1 for row in scoped_rows if bool(row.get("has_weighted_lexical_bucket"))
        )
        ambiguous_count = sum(1 for row in scoped_rows if bool(row.get("ambiguous_raw_pos")))
        rows.append(
            {
                "rank_band_top_n": band_size,
                "rows_considered": len(scoped_rows),
                "any_pos_lemma_count": any_pos_count,
                "any_pos_lemma_share": _ratio(any_pos_count, len(scoped_rows)),
                "mapped_pos_lemma_count": mapped_pos_count,
                "mapped_pos_lemma_share": _ratio(mapped_pos_count, len(scoped_rows)),
                "weighted_lexical_bucket_lemma_count": weighted_count,
                "weighted_lexical_bucket_lemma_share": _ratio(
                    weighted_count,
                    len(scoped_rows),
                ),
                "ambiguous_raw_pos_lemma_count": ambiguous_count,
                "ambiguous_raw_pos_lemma_share": _ratio(ambiguous_count, len(scoped_rows)),
            }
        )
    return rows


def _ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(min(1.0, max(0.0, numerator / denominator)), 6)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


if __name__ == "__main__":
    raise SystemExit(main())
