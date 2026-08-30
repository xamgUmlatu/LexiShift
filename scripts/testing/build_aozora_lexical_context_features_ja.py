#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import sqlite3
import sys
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PACK_ID = "freq-ja-aozora-word"
TOKEN_KEY_COLUMNS = (
    "surface",
    "base_form",
    "reading",
    "pronunciation",
    "pos_major",
    "pos_sub1",
    "pos_sub2",
    "pos_sub3",
    "conjugation_type",
    "conjugation_form",
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build reusable token-level Aozora lexical-context features for en-ja "
            "learner-difficulty experiments. This is a sidecar feature pack and "
            "does not wire anything into the accepted scorer."
        )
    )
    parser.add_argument(
        "--input-sqlite",
        type=Path,
        default=None,
        help="Aozora word sidecar SQLite. Defaults to the local LexiShift data root pack.",
    )
    parser.add_argument(
        "--audience-sqlite",
        type=Path,
        default=None,
        help=(
            "Optional work-audience metadata SQLite built by "
            "fetch_aozora_work_audience_metadata_ja.py. Used for work-axis rows only "
            "unless a future token-work bridge is available."
        ),
    )
    parser.add_argument(
        "--audience-run-id",
        default="",
        help="Optional specific run id from --audience-sqlite. Defaults to latest run.",
    )
    parser.add_argument(
        "--output-sqlite",
        type=Path,
        default=None,
        help=(
            "Output SQLite path. Defaults beside the local Aozora pack as "
            "lexical_context_features.sqlite."
        ),
    )
    parser.add_argument(
        "--surface",
        action="append",
        default=[],
        help="Exact surface or base_form to include. May be repeated for smoke probes.",
    )
    parser.add_argument(
        "--pos-major",
        action="append",
        default=[],
        help="Optional exact Aozora POS major filter, e.g. 名詞. May be repeated.",
    )
    parser.add_argument(
        "--min-token-count",
        type=int,
        default=1,
        help="Minimum Aozora token count to include. Defaults to 1.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Optional row limit for smoke builds. Full build uses 0.",
    )
    parser.add_argument(
        "--explain",
        action="append",
        default=[],
        help="Print summary rows for this surface/base_form after writing.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    input_sqlite = _resolve_input_sqlite(args.input_sqlite)
    output_sqlite = _resolve_output_sqlite(args.output_sqlite)
    if input_sqlite.resolve() == output_sqlite.resolve():
        raise SystemExit("--output-sqlite must not overwrite --input-sqlite")

    audience_sqlite = _resolve_path(args.audience_sqlite) if args.audience_sqlite else None
    external_features, audience_run_id = _load_external_audience_features(
        audience_sqlite,
        run_id=str(args.audience_run_id or ""),
    )
    run_id = _run_id(
        input_sqlite=input_sqlite,
        audience_sqlite=audience_sqlite,
        audience_run_id=audience_run_id,
        filters={
            "surface": tuple(args.surface),
            "pos_major": tuple(args.pos_major),
            "min_token_count": max(1, int(args.min_token_count)),
            "limit": max(0, int(args.limit)),
        },
    )

    temporary = output_sqlite.with_suffix(output_sqlite.suffix + ".tmp")
    if temporary.exists():
        temporary.unlink()
    output_sqlite.parent.mkdir(parents=True, exist_ok=True)
    token_rows = 0
    feature_rows = 0
    work_axis_rows = 0

    with sqlite3.connect(input_sqlite) as source, sqlite3.connect(temporary) as dest:
        source.row_factory = sqlite3.Row
        _validate_input_schema(source)
        _create_output_schema(dest)
        _insert_run(
            dest,
            run_id=run_id,
            input_sqlite=input_sqlite,
            audience_sqlite=audience_sqlite,
            audience_run_id=audience_run_id,
            args=args,
        )
        for work in source.execute("SELECT * FROM work_profile ORDER BY work_id"):
            rows = _work_axis_rows(work, external_features.get(str(work["work_id"] or ""), {}))
            for axis in rows:
                _insert_work_axis(dest, run_id=run_id, work=work, axis=axis)
            work_axis_rows += len(rows)

        for row in _iter_token_rows(
            source,
            surfaces=tuple(str(value) for value in args.surface if str(value).strip()),
            pos_major=tuple(str(value) for value in args.pos_major if str(value).strip()),
            min_token_count=max(1, int(args.min_token_count)),
            limit=max(0, int(args.limit)),
        ):
            summary = _token_summary(row)
            _insert_token_summary(dest, run_id=run_id, row=row, summary=summary)
            token_rows += 1
            for feature in _token_feature_rows(summary):
                _insert_token_feature(dest, run_id=run_id, row=row, feature=feature)
                feature_rows += 1

        _insert_metadata(
            dest,
            {
                "schema_version": "1",
                "pack_id": PACK_ID,
                "run_id": run_id,
                "generated_at_utc": _utc_now(),
                "input_sqlite": str(input_sqlite),
                "audience_sqlite": str(audience_sqlite or ""),
                "audience_run_id": audience_run_id,
                "token_rows": str(token_rows),
                "token_feature_rows": str(feature_rows),
                "work_axis_rows": str(work_axis_rows),
                "notes": (
                    "Sidecar lexical-context features only. Token features are derived from "
                    "Aozora token_context_profile broad work aggregates; optional rich "
                    "audience metadata is stored as work-axis evidence and is not yet "
                    "mapped to tokens without a token-work bridge."
                ),
            },
        )
        dest.commit()
    temporary.replace(output_sqlite)

    print(f"Wrote {output_sqlite}")
    print(f"- run_id={run_id}")
    print(
        f"- token_rows={token_rows} token_feature_rows={feature_rows} work_axis_rows={work_axis_rows}"
    )
    if args.explain:
        _print_explanations(output_sqlite, run_id=run_id, terms=tuple(args.explain))
    return 0


def _create_output_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE metadata (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        CREATE TABLE feature_run (
            run_id TEXT PRIMARY KEY,
            generated_at_utc TEXT NOT NULL,
            input_sqlite TEXT NOT NULL,
            audience_sqlite TEXT,
            audience_run_id TEXT,
            args_json TEXT NOT NULL,
            notes TEXT NOT NULL
        );

        CREATE TABLE work_audience_axis_score (
            run_id TEXT NOT NULL,
            work_id TEXT NOT NULL,
            title TEXT NOT NULL,
            axis_name TEXT NOT NULL,
            value_num REAL NOT NULL,
            confidence REAL NOT NULL,
            coverage REAL NOT NULL,
            source TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, work_id, axis_name)
        );

        CREATE TABLE token_audience_summary (
            run_id TEXT NOT NULL,
            surface TEXT NOT NULL,
            base_form TEXT NOT NULL,
            reading TEXT NOT NULL,
            pronunciation TEXT NOT NULL,
            pos_major TEXT NOT NULL,
            pos_sub1 TEXT NOT NULL,
            pos_sub2 TEXT NOT NULL,
            pos_sub3 TEXT NOT NULL,
            conjugation_type TEXT NOT NULL,
            conjugation_form TEXT NOT NULL,
            token_count INTEGER NOT NULL,
            work_count INTEGER NOT NULL,
            author_count INTEGER NOT NULL,
            rank_by_token INTEGER NOT NULL,
            pmw REAL NOT NULL,
            source_variant TEXT NOT NULL,
            context_coverage REAL NOT NULL,
            context_confidence REAL NOT NULL,
            accessibility_weighted_mean REAL NOT NULL,
            accessible_work_exposure REAL NOT NULL,
            hard_work_exposure REAL NOT NULL,
            modern_orthography_exposure REAL NOT NULL,
            old_orthography_exposure REAL NOT NULL,
            child_or_youth_exposure REAL NOT NULL,
            modern_child_exposure REAL NOT NULL,
            child_nonmodern_exposure REAL NOT NULL,
            modern_accessible_context REAL NOT NULL,
            modern_child_accessible_context REAL NOT NULL,
            old_literary_risk_context REAL NOT NULL,
            child_old_risk_context REAL NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (
                run_id,
                surface,
                base_form,
                reading,
                pronunciation,
                pos_major,
                pos_sub1,
                pos_sub2,
                pos_sub3,
                conjugation_type,
                conjugation_form
            )
        );

        CREATE TABLE token_audience_feature (
            run_id TEXT NOT NULL,
            surface TEXT NOT NULL,
            base_form TEXT NOT NULL,
            reading TEXT NOT NULL,
            pronunciation TEXT NOT NULL,
            pos_major TEXT NOT NULL,
            pos_sub1 TEXT NOT NULL,
            pos_sub2 TEXT NOT NULL,
            pos_sub3 TEXT NOT NULL,
            conjugation_type TEXT NOT NULL,
            conjugation_form TEXT NOT NULL,
            feature_name TEXT NOT NULL,
            value_num REAL NOT NULL,
            coverage REAL NOT NULL,
            confidence REAL NOT NULL,
            token_count INTEGER NOT NULL,
            work_count INTEGER NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (
                run_id,
                surface,
                base_form,
                reading,
                pronunciation,
                pos_major,
                pos_sub1,
                pos_sub2,
                pos_sub3,
                conjugation_type,
                conjugation_form,
                feature_name
            )
        );

        CREATE INDEX idx_work_axis_axis_value
            ON work_audience_axis_score(axis_name, value_num);
        CREATE INDEX idx_token_summary_surface
            ON token_audience_summary(surface, base_form, reading);
        CREATE INDEX idx_token_summary_rank
            ON token_audience_summary(rank_by_token);
        CREATE INDEX idx_token_feature_name_value
            ON token_audience_feature(feature_name, value_num);
        """
    )


def _insert_run(
    conn: sqlite3.Connection,
    *,
    run_id: str,
    input_sqlite: Path,
    audience_sqlite: Path | None,
    audience_run_id: str,
    args: argparse.Namespace,
) -> None:
    conn.execute(
        """
        INSERT INTO feature_run (
            run_id,
            generated_at_utc,
            input_sqlite,
            audience_sqlite,
            audience_run_id,
            args_json,
            notes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            _utc_now(),
            str(input_sqlite),
            str(audience_sqlite or ""),
            audience_run_id,
            _json_dumps(
                {
                    "surface": args.surface,
                    "pos_major": args.pos_major,
                    "min_token_count": args.min_token_count,
                    "limit": args.limit,
                }
            ),
            "Aozora lexical-context sidecar feature run.",
        ),
    )


def _insert_metadata(conn: sqlite3.Connection, values: dict[str, str]) -> None:
    conn.executemany(
        "INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)",
        sorted(values.items()),
    )


def _work_axis_rows(work: sqlite3.Row, external_features: dict[str, float]) -> list[dict[str, Any]]:
    work_id = str(work["work_id"] or "")
    ndc = str(work["ndc"] or "")
    token_count = _safe_int(work["token_count"]) or 0
    content_token_count = _safe_int(work["content_token_count"]) or 0
    accessibility = _clamp01(_safe_float(work["accessibility_percentile"]) or 0.0)
    common_share = _clamp01(_safe_float(work["common_content_share"]) or 0.0)
    mid_share = _clamp01(_safe_float(work["mid_content_share"]) or 0.0)
    tail_share = _clamp01(_safe_float(work["tail_content_share"]) or 0.0)
    rare_unique_share = _clamp01(_safe_float(work["rare_unique_content_share"]) or 0.0)
    modern = bool(work["modern_orthography"])
    child_ndc = bool(work["children_or_youth_ndc"])
    old_risk = _orthography_risk(str(work["orthography_type"] or ""))
    k911_risk = 1.0 if re.search(r"\bK911\b", ndc.replace("NDC", " ")) else 0.0
    lexical_confidence = _work_lexical_confidence(content_token_count)
    external_child = _external_child_signal(external_features)
    external_warning = _external_warning_signal(external_features)
    child_signal = _noisy_or([0.85 if child_ndc else 0.0, external_child])
    child_old_or_hard = child_signal * max(old_risk, 1.0 - accessibility, k911_risk)
    evidence_base = {
        "work_id": work_id,
        "ndc": ndc,
        "orthography_type": str(work["orthography_type"] or ""),
        "token_count": token_count,
        "content_token_count": content_token_count,
        "accessibility_band": str(work["accessibility_band"] or ""),
    }
    rows = [
        _axis(
            "work_accessibility_percentile",
            accessibility,
            lexical_confidence,
            "aozora_work_profile",
            evidence_base,
        ),
        _axis(
            "work_accessible_language",
            accessibility,
            lexical_confidence,
            "aozora_work_profile",
            evidence_base,
        ),
        _axis(
            "work_common_content_share",
            common_share,
            lexical_confidence,
            "aozora_work_profile",
            evidence_base,
        ),
        _axis(
            "work_mid_content_share",
            mid_share,
            lexical_confidence,
            "aozora_work_profile",
            evidence_base,
        ),
        _axis(
            "work_tail_content_share",
            tail_share,
            lexical_confidence,
            "aozora_work_profile",
            evidence_base,
        ),
        _axis(
            "work_lexical_rarity_risk",
            rare_unique_share,
            lexical_confidence,
            "aozora_work_profile",
            evidence_base,
        ),
        _axis(
            "work_modern_orthography",
            1.0 if modern else 0.0,
            1.0,
            "aozora_work_metadata",
            evidence_base,
        ),
        _axis("work_old_orthography_risk", old_risk, 1.0, "aozora_work_metadata", evidence_base),
        _axis(
            "work_child_or_youth_ndc",
            1.0 if child_ndc else 0.0,
            0.85 if child_ndc else 0.15,
            "aozora_work_metadata",
            evidence_base,
        ),
        _axis(
            "work_k911_poetry_risk",
            k911_risk,
            0.80 if k911_risk else 0.20,
            "aozora_work_metadata",
            evidence_base,
        ),
        _axis(
            "work_modern_child_accessible_prior",
            child_signal * (1.0 if modern else 0.0) * accessibility,
            max(lexical_confidence, child_signal),
            "aozora_combined",
            {**evidence_base, "child_signal": child_signal},
        ),
        _axis(
            "work_child_old_or_hard_prior",
            child_old_or_hard,
            max(lexical_confidence, child_signal),
            "aozora_combined",
            {**evidence_base, "child_signal": child_signal},
        ),
        _axis(
            "work_combined_child_or_school_audience",
            child_signal,
            0.90 if child_signal else 0.15,
            "aozora_combined",
            {**evidence_base, "external_features": external_features},
        ),
    ]
    if external_features:
        rows.extend(
            [
                _axis(
                    "work_external_child_or_school_audience",
                    external_child,
                    0.85 if external_child else 0.20,
                    "work_audience_metadata",
                    {"external_features": external_features},
                ),
                _axis(
                    "work_external_warning_or_adultish",
                    external_warning,
                    0.75 if external_warning else 0.20,
                    "work_audience_metadata",
                    {"external_features": external_features},
                ),
            ]
        )
    return rows


def _axis(
    name: str,
    value: float,
    confidence: float,
    source: str,
    evidence: dict[str, Any],
) -> dict[str, Any]:
    return {
        "axis_name": name,
        "value_num": _clamp01(value),
        "confidence": _clamp01(confidence),
        "coverage": 1.0,
        "source": source,
        "evidence_json": _json_dumps(evidence),
    }


def _insert_work_axis(
    conn: sqlite3.Connection,
    *,
    run_id: str,
    work: sqlite3.Row,
    axis: dict[str, Any],
) -> None:
    conn.execute(
        """
        INSERT INTO work_audience_axis_score (
            run_id,
            work_id,
            title,
            axis_name,
            value_num,
            confidence,
            coverage,
            source,
            evidence_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            str(work["work_id"] or ""),
            str(work["title"] or ""),
            str(axis["axis_name"]),
            float(axis["value_num"]),
            float(axis["confidence"]),
            float(axis["coverage"]),
            str(axis["source"]),
            str(axis["evidence_json"]),
        ),
    )


def _iter_token_rows(
    conn: sqlite3.Connection,
    *,
    surfaces: tuple[str, ...],
    pos_major: tuple[str, ...],
    min_token_count: int,
    limit: int,
):
    conditions = ["f.token_count >= ?"]
    params: list[Any] = [min_token_count]
    if surfaces:
        placeholders = ", ".join("?" for _value in surfaces)
        conditions.append(f"(f.surface IN ({placeholders}) OR f.base_form IN ({placeholders}))")
        params.extend(surfaces)
        params.extend(surfaces)
    if pos_major:
        placeholders = ", ".join("?" for _value in pos_major)
        conditions.append(f"f.pos_major IN ({placeholders})")
        params.extend(pos_major)
    limit_sql = "LIMIT ?" if limit else ""
    if limit:
        params.append(limit)
    query = f"""
        SELECT
            f.surface,
            f.base_form,
            f.reading,
            f.pronunciation,
            f.pos_major,
            f.pos_sub1,
            f.pos_sub2,
            f.pos_sub3,
            f.conjugation_type,
            f.conjugation_form,
            f.token_count AS frequency_token_count,
            f.work_count AS frequency_work_count,
            f.author_count,
            f.rank_by_token,
            f.pmw,
            f.source_variant,
            c.token_count AS context_token_count,
            c.work_count AS context_work_count,
            c.modern_token_count,
            c.modern_work_count,
            c.old_orthography_token_count,
            c.old_orthography_work_count,
            c.children_token_count,
            c.children_work_count,
            c.modern_children_token_count,
            c.modern_children_work_count,
            c.accessible_token_count,
            c.accessible_work_count,
            c.hard_token_count,
            c.hard_work_count,
            c.accessibility_weighted_mean,
            c.orthography_token_counts_json,
            c.orthography_work_counts_json,
            c.ndc_class_token_counts_json,
            c.ndc_class_work_counts_json
        FROM token_frequency AS f
        LEFT JOIN token_context_profile AS c
            ON c.surface = f.surface
            AND c.base_form = f.base_form
            AND c.reading = f.reading
            AND c.pronunciation = f.pronunciation
            AND c.pos_major = f.pos_major
            AND c.pos_sub1 = f.pos_sub1
            AND c.pos_sub2 = f.pos_sub2
            AND c.pos_sub3 = f.pos_sub3
            AND c.conjugation_type = f.conjugation_type
            AND c.conjugation_form = f.conjugation_form
        WHERE {" AND ".join(conditions)}
        ORDER BY f.rank_by_token, f.surface, f.base_form, f.reading
        {limit_sql}
    """
    yield from conn.execute(query, params)


def _token_summary(row: sqlite3.Row) -> dict[str, Any]:
    token_count = _safe_int(row["frequency_token_count"]) or 0
    context_token_count = _safe_int(row["context_token_count"]) or 0
    context_work_count = _safe_int(row["context_work_count"]) or 0
    work_count = _safe_int(row["frequency_work_count"]) or 0
    author_count = _safe_int(row["author_count"]) or 0
    denominator = max(1, token_count)
    accessibility = _clamp01(_safe_float(row["accessibility_weighted_mean"]) or 0.0)
    accessible = _ratio(row["accessible_token_count"], denominator)
    hard = _ratio(row["hard_token_count"], denominator)
    modern = _ratio(row["modern_token_count"], denominator)
    old = _ratio(row["old_orthography_token_count"], denominator)
    child = _ratio(row["children_token_count"], denominator)
    modern_child = _ratio(row["modern_children_token_count"], denominator)
    child_nonmodern = _clamp01(child - modern_child)
    coverage = (
        _clamp01(float(context_token_count) / float(denominator)) if context_token_count else 0.0
    )
    confidence = _context_confidence(
        token_count=token_count, work_count=work_count, author_count=author_count
    )
    evidence = {
        "context_token_count": context_token_count,
        "context_work_count": context_work_count,
        "modern_work_count": _safe_int(row["modern_work_count"]) or 0,
        "old_orthography_work_count": _safe_int(row["old_orthography_work_count"]) or 0,
        "children_work_count": _safe_int(row["children_work_count"]) or 0,
        "modern_children_work_count": _safe_int(row["modern_children_work_count"]) or 0,
        "accessible_work_count": _safe_int(row["accessible_work_count"]) or 0,
        "hard_work_count": _safe_int(row["hard_work_count"]) or 0,
        "orthography_token_counts": _loads_json(str(row["orthography_token_counts_json"] or "{}")),
        "ndc_class_token_counts": _loads_json(str(row["ndc_class_token_counts_json"] or "{}")),
    }
    return {
        "token_count": token_count,
        "work_count": work_count,
        "author_count": author_count,
        "rank_by_token": _safe_int(row["rank_by_token"]) or 0,
        "pmw": _safe_float(row["pmw"]) or 0.0,
        "source_variant": str(row["source_variant"] or ""),
        "context_coverage": coverage,
        "context_confidence": confidence,
        "accessibility_weighted_mean": accessibility,
        "accessible_work_exposure": accessible,
        "hard_work_exposure": hard,
        "modern_orthography_exposure": modern,
        "old_orthography_exposure": old,
        "child_or_youth_exposure": child,
        "modern_child_exposure": modern_child,
        "child_nonmodern_exposure": child_nonmodern,
        "modern_accessible_context": _clamp01(modern * accessibility),
        "modern_child_accessible_context": _clamp01(modern_child * accessibility),
        "old_literary_risk_context": _clamp01(old * (1.0 - accessibility)),
        "child_old_risk_context": _clamp01(child_nonmodern * (1.0 - accessibility)),
        "evidence_json": _json_dumps(evidence),
    }


def _insert_token_summary(
    conn: sqlite3.Connection,
    *,
    run_id: str,
    row: sqlite3.Row,
    summary: dict[str, Any],
) -> None:
    conn.execute(
        """
        INSERT INTO token_audience_summary (
            run_id,
            surface,
            base_form,
            reading,
            pronunciation,
            pos_major,
            pos_sub1,
            pos_sub2,
            pos_sub3,
            conjugation_type,
            conjugation_form,
            token_count,
            work_count,
            author_count,
            rank_by_token,
            pmw,
            source_variant,
            context_coverage,
            context_confidence,
            accessibility_weighted_mean,
            accessible_work_exposure,
            hard_work_exposure,
            modern_orthography_exposure,
            old_orthography_exposure,
            child_or_youth_exposure,
            modern_child_exposure,
            child_nonmodern_exposure,
            modern_accessible_context,
            modern_child_accessible_context,
            old_literary_risk_context,
            child_old_risk_context,
            evidence_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            *(str(row[column] or "") for column in TOKEN_KEY_COLUMNS),
            int(summary["token_count"]),
            int(summary["work_count"]),
            int(summary["author_count"]),
            int(summary["rank_by_token"]),
            float(summary["pmw"]),
            str(summary["source_variant"]),
            float(summary["context_coverage"]),
            float(summary["context_confidence"]),
            float(summary["accessibility_weighted_mean"]),
            float(summary["accessible_work_exposure"]),
            float(summary["hard_work_exposure"]),
            float(summary["modern_orthography_exposure"]),
            float(summary["old_orthography_exposure"]),
            float(summary["child_or_youth_exposure"]),
            float(summary["modern_child_exposure"]),
            float(summary["child_nonmodern_exposure"]),
            float(summary["modern_accessible_context"]),
            float(summary["modern_child_accessible_context"]),
            float(summary["old_literary_risk_context"]),
            float(summary["child_old_risk_context"]),
            str(summary["evidence_json"]),
        ),
    )


def _token_feature_rows(summary: dict[str, Any]) -> list[dict[str, Any]]:
    feature_names = (
        "aozora_accessibility_weighted_mean",
        "aozora_accessible_work_exposure",
        "aozora_hard_work_exposure",
        "aozora_modern_orthography_exposure",
        "aozora_old_orthography_exposure",
        "aozora_child_or_youth_exposure",
        "aozora_modern_child_exposure",
        "aozora_child_nonmodern_exposure",
        "aozora_modern_accessible_context",
        "aozora_modern_child_accessible_context",
        "aozora_old_literary_risk_context",
        "aozora_child_old_risk_context",
        "aozora_context_confidence",
        "aozora_context_coverage",
        "aozora_rank_percentile_proxy",
    )
    rank = max(1, int(summary["rank_by_token"]))
    rank_proxy = 1.0 / (1.0 + math.log10(float(rank)))
    values = {
        "aozora_accessibility_weighted_mean": summary["accessibility_weighted_mean"],
        "aozora_accessible_work_exposure": summary["accessible_work_exposure"],
        "aozora_hard_work_exposure": summary["hard_work_exposure"],
        "aozora_modern_orthography_exposure": summary["modern_orthography_exposure"],
        "aozora_old_orthography_exposure": summary["old_orthography_exposure"],
        "aozora_child_or_youth_exposure": summary["child_or_youth_exposure"],
        "aozora_modern_child_exposure": summary["modern_child_exposure"],
        "aozora_child_nonmodern_exposure": summary["child_nonmodern_exposure"],
        "aozora_modern_accessible_context": summary["modern_accessible_context"],
        "aozora_modern_child_accessible_context": summary["modern_child_accessible_context"],
        "aozora_old_literary_risk_context": summary["old_literary_risk_context"],
        "aozora_child_old_risk_context": summary["child_old_risk_context"],
        "aozora_context_confidence": summary["context_confidence"],
        "aozora_context_coverage": summary["context_coverage"],
        "aozora_rank_percentile_proxy": rank_proxy,
    }
    return [
        {
            "feature_name": name,
            "value_num": _clamp01(float(values[name])),
            "coverage": float(summary["context_coverage"]),
            "confidence": 1.0
            if name in {"aozora_context_confidence", "aozora_context_coverage"}
            else float(summary["context_confidence"]),
            "evidence_json": summary["evidence_json"],
        }
        for name in feature_names
    ]


def _insert_token_feature(
    conn: sqlite3.Connection,
    *,
    run_id: str,
    row: sqlite3.Row,
    feature: dict[str, Any],
) -> None:
    conn.execute(
        """
        INSERT INTO token_audience_feature (
            run_id,
            surface,
            base_form,
            reading,
            pronunciation,
            pos_major,
            pos_sub1,
            pos_sub2,
            pos_sub3,
            conjugation_type,
            conjugation_form,
            feature_name,
            value_num,
            coverage,
            confidence,
            token_count,
            work_count,
            evidence_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            *(str(row[column] or "") for column in TOKEN_KEY_COLUMNS),
            str(feature["feature_name"]),
            float(feature["value_num"]),
            float(feature["coverage"]),
            float(feature["confidence"]),
            _safe_int(row["frequency_token_count"]) or 0,
            _safe_int(row["frequency_work_count"]) or 0,
            str(feature["evidence_json"]),
        ),
    )


def _load_external_audience_features(
    sqlite_path: Path | None,
    *,
    run_id: str,
) -> tuple[dict[str, dict[str, float]], str]:
    if sqlite_path is None:
        return {}, ""
    if not sqlite_path.exists():
        raise SystemExit(f"Audience SQLite does not exist: {sqlite_path}")
    with sqlite3.connect(sqlite_path) as conn:
        conn.row_factory = sqlite3.Row
        if not _sqlite_table_exists(conn, "work_audience_feature"):
            raise SystemExit(f"Audience SQLite lacks work_audience_feature: {sqlite_path}")
        selected_run_id = run_id.strip() or _latest_audience_run_id(conn)
        if not selected_run_id:
            return {}, ""
        rows = conn.execute(
            """
            SELECT work_id, feature_name, value_num
            FROM work_audience_feature
            WHERE run_id = ?
            """,
            (selected_run_id,),
        ).fetchall()
    features: dict[str, dict[str, float]] = {}
    for row in rows:
        value = _safe_float(row["value_num"])
        if value is None:
            continue
        features.setdefault(str(row["work_id"] or ""), {})[str(row["feature_name"] or "")] = float(
            value
        )
    return features, selected_run_id


def _latest_audience_run_id(conn: sqlite3.Connection) -> str:
    if not _sqlite_table_exists(conn, "work_audience_run"):
        return ""
    row = conn.execute(
        """
        SELECT run_id
        FROM work_audience_run
        ORDER BY generated_at_utc DESC, run_id DESC
        LIMIT 1
        """
    ).fetchone()
    return str(row["run_id"] or "") if row else ""


def _external_child_signal(features: dict[str, float]) -> float:
    signals = []
    if features.get("yozora_card_match", 0.0) > 0:
        signals.append(0.85)
    if features.get("bungo_juvenile_listing_match_count", 0.0) > 0:
        signals.append(0.90)
    if features.get("ndl_opensearch_audience_item_count", 0.0) > 0:
        signals.append(0.65)
    if features.get("ndl_sru_audience_record_count", 0.0) > 0:
        signals.append(0.65)
    if (
        features.get("aozora_card_juvenile_term_count", 0.0)
        + features.get("aozora_card_school_term_count", 0.0)
    ) > 0:
        signals.append(0.55)
    if features.get("wikipedia_positive_term_count", 0.0) > 0:
        signals.append(0.25)
    if features.get("wikidata_positive_term_count", 0.0) > 0:
        signals.append(0.20)
    return _noisy_or(signals)


def _external_warning_signal(features: dict[str, float]) -> float:
    signals = []
    if features.get("aozora_card_warning_term_count", 0.0) > 0:
        signals.append(0.60)
    if features.get("wikipedia_warning_term_count", 0.0) > 0:
        signals.append(0.35)
    if features.get("wikidata_warning_term_count", 0.0) > 0:
        signals.append(0.30)
    return _noisy_or(signals)


def _print_explanations(sqlite_path: Path, *, run_id: str, terms: tuple[str, ...]) -> None:
    with sqlite3.connect(sqlite_path) as conn:
        conn.row_factory = sqlite3.Row
        for term in terms:
            rows = conn.execute(
                """
                SELECT
                    surface,
                    base_form,
                    reading,
                    pos_major,
                    token_count,
                    work_count,
                    rank_by_token,
                    ROUND(accessibility_weighted_mean, 3) AS access,
                    ROUND(accessible_work_exposure, 3) AS accessible,
                    ROUND(hard_work_exposure, 3) AS hard,
                    ROUND(modern_child_exposure, 3) AS modern_child,
                    ROUND(old_literary_risk_context, 3) AS old_risk,
                    ROUND(context_confidence, 3) AS confidence
                FROM token_audience_summary
                WHERE run_id = ? AND (surface = ? OR base_form = ?)
                ORDER BY token_count DESC, work_count DESC
                LIMIT 20
                """,
                (run_id, term, term),
            ).fetchall()
            print(f"\nProbe: {term}")
            if not rows:
                print("- no rows")
                continue
            for row in rows:
                print(
                    "- "
                    f"{row['surface']} / {row['base_form']} [{row['reading']}] "
                    f"{row['pos_major']} count={row['token_count']} works={row['work_count']} "
                    f"rank={row['rank_by_token']} access={row['access']} "
                    f"accessible={row['accessible']} hard={row['hard']} "
                    f"modern_child={row['modern_child']} old_risk={row['old_risk']} "
                    f"conf={row['confidence']}"
                )


def _validate_input_schema(conn: sqlite3.Connection) -> None:
    for table_name in ("work_profile", "token_frequency", "token_context_profile"):
        if not _sqlite_table_exists(conn, table_name):
            raise SystemExit(f"Input SQLite lacks required table: {table_name}")


def _sqlite_table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table_name,),
    ).fetchone()
    return bool(row)


def _resolve_input_sqlite(value: Path | None) -> Path:
    if value is not None:
        return _resolve_path(value)
    return _resolve_data_root() / "frequency_packs" / PACK_ID / "main.sqlite"


def _resolve_output_sqlite(value: Path | None) -> Path:
    if value is not None:
        return _resolve_path(value)
    return _resolve_data_root() / "frequency_packs" / PACK_ID / "lexical_context_features.sqlite"


def _resolve_path(value: Path) -> Path:
    if value.is_absolute():
        return value
    return (PROJECT_ROOT / value).resolve()


def _resolve_data_root() -> Path:
    home = Path.home()
    if sys.platform == "darwin":
        return home / "Library" / "Application Support" / "LexiShift" / "LexiShift"
    if sys.platform.startswith("win"):
        return Path.home() / "AppData" / "Roaming" / "LexiShift" / "LexiShift"
    return home / ".local" / "share" / "LexiShift" / "LexiShift"


def _run_id(
    *,
    input_sqlite: Path,
    audience_sqlite: Path | None,
    audience_run_id: str,
    filters: dict[str, Any],
) -> str:
    generated = _utc_now()
    compact_time = re.sub(r"[^0-9A-Za-z]+", "", generated)[:16]
    digest = hashlib.sha256(
        _json_dumps(
            {
                "generated_at_utc": generated,
                "input_sqlite": str(input_sqlite),
                "audience_sqlite": str(audience_sqlite or ""),
                "audience_run_id": audience_run_id,
                "filters": filters,
            }
        ).encode("utf-8")
    ).hexdigest()[:10]
    return f"aozora_lexctx_{compact_time}_{digest}"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _loads_json(value: str) -> Any:
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return {}


def _safe_int(value: Any) -> int | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return int(float(text))
    except ValueError:
        return None


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _ratio(value: Any, denominator: int) -> float:
    return _clamp01(float(_safe_int(value) or 0) / float(max(1, denominator)))


def _clamp01(value: float) -> float:
    return min(1.0, max(0.0, float(value)))


def _noisy_or(values: list[float]) -> float:
    miss = 1.0
    for value in values:
        miss *= 1.0 - _clamp01(value)
    return _clamp01(1.0 - miss)


def _context_confidence(*, token_count: int, work_count: int, author_count: int) -> float:
    token_confidence = 1.0 - math.exp(-float(max(0, token_count)) / 80.0)
    work_confidence = 1.0 - math.exp(-float(max(0, work_count)) / 6.0)
    author_confidence = 1.0 - math.exp(-float(max(0, author_count)) / 4.0)
    dispersion = math.sqrt(work_confidence * max(author_confidence, 0.20))
    return _clamp01(math.sqrt(token_confidence * dispersion))


def _work_lexical_confidence(content_token_count: int) -> float:
    return _clamp01(math.sqrt(1.0 - math.exp(-float(max(0, content_token_count)) / 300.0)))


def _orthography_risk(value: str) -> float:
    if value == "新字新仮名":
        return 0.0
    if value == "新字旧仮名":
        return 0.45
    if value == "旧字新仮名":
        return 0.55
    if value == "旧字旧仮名":
        return 0.90
    return 0.65


if __name__ == "__main__":
    raise SystemExit(main())
