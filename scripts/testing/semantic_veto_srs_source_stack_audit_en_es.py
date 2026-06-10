#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import unicodedata
from typing import Iterable, Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / "core"
TEST_OUTPUTS_ROOT = PROJECT_ROOT / "docs" / "test_outputs"
if str(CORE_ROOT) not in sys.path:
    sys.path.insert(0, str(CORE_ROOT))

from lexishift_core.pos.normalization import normalize_pos  # noqa: E402
from semantic_veto_srs_source_stack_audit_rendering import (  # noqa: E402
    build_findings,
    build_summary,
    recommended_next_steps,
    render_source_stack_markdown,
)


DEFAULT_PAIR = "en-es"
DEFAULT_TARGET_SIZES = (2000, 5000, 10000)
DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / "semantic_veto_srs_source_stack_audit_en_es_latest.json"
DEFAULT_MARKDOWN_OUT = TEST_OUTPUTS_ROOT / "semantic_veto_srs_source_stack_audit_en_es_latest.md"
DEFAULT_SPALEX_SOURCE_URL = "https://figshare.com/articles/dataset/Word_information/5924794"
DEFAULT_SPALEX_DOI = "10.6084/m9.figshare.5924794.v4"
DEFAULT_SPALEX_LICENSE_NAME = "CC BY 4.0"
DEFAULT_SPALEX_LICENSE_URL = "https://creativecommons.org/licenses/by/4.0/"
DEFAULT_DATA_ROOT = Path.home() / "Library/Application Support/LexiShift/LexiShift"
DEFAULT_CURRENT_FREQUENCY_DB = DEFAULT_DATA_ROOT / "frequency_packs" / "freq-es-cde" / "main.sqlite"
DEFAULT_KAIKKI_FORWARD_DB = (
    DEFAULT_DATA_ROOT / "language_packs" / "wiktionary-es-en" / "main.sqlite"
)
DEFAULT_KAIKKI_REVERSE_DB = DEFAULT_DATA_ROOT / "language_packs" / "wiktionary-en-es.sqlite"
SPALEX_REQUIRED_COLUMNS = (
    "spelling",
    "count_total",
    "percent_total",
    "prevalence_total",
    "count_nts",
    "percent_nts",
    "prevalence_nts",
    "count_ntl",
    "percent_ntl",
    "prevalence_ntl",
    "freq",
    "zipf",
)
KAIKKI_MEDICINE_TOPIC_TERMS = {
    "anatomy",
    "dentistry",
    "health",
    "medicine",
    "pathology",
}
KAIKKI_MEDICINE_SUBSTRINGS = (
    "anatom",
    "dent",
    "disease",
    "health",
    "medic",
    "patholog",
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Audit SPALEX + Kaikki as a practical en-es SRS expansion source stack. "
            "The script reads already-downloaded inputs and does not fetch large data."
        )
    )
    parser.add_argument(
        "--spalex-csv",
        type=Path,
        required=True,
        help="Path to SPALEX word_info.csv.",
    )
    parser.add_argument(
        "--current-frequency-db",
        type=Path,
        default=DEFAULT_CURRENT_FREQUENCY_DB,
        help="Current freq-es-cde SQLite baseline.",
    )
    parser.add_argument(
        "--kaikki-forward-db",
        type=Path,
        default=DEFAULT_KAIKKI_FORWARD_DB,
        help="Kaikki/Wiktionary Spanish-headword forward SQLite.",
    )
    parser.add_argument(
        "--kaikki-reverse-db",
        type=Path,
        default=DEFAULT_KAIKKI_REVERSE_DB,
        help="Kaikki/Wiktionary English-headword reverse SQLite.",
    )
    parser.add_argument("--pair", default=DEFAULT_PAIR)
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
    report = build_source_stack_audit_report(
        spalex_csv=args.spalex_csv,
        current_frequency_db=args.current_frequency_db,
        kaikki_forward_db=args.kaikki_forward_db,
        kaikki_reverse_db=args.kaikki_reverse_db,
        pair=args.pair,
        target_sizes=args.target_size or DEFAULT_TARGET_SIZES,
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.markdown_out.write_text(render_source_stack_markdown(report), encoding="utf-8")
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    if args.fail_on_error and report["summary"]["status"] == "error":
        return 1
    return 0


def build_source_stack_audit_report(
    *,
    spalex_csv: Path,
    current_frequency_db: Path,
    kaikki_forward_db: Path,
    kaikki_reverse_db: Path,
    pair: str = DEFAULT_PAIR,
    target_sizes: Sequence[int] = DEFAULT_TARGET_SIZES,
    generated_at: str | None = None,
) -> dict[str, object]:
    normalized_targets = tuple(sorted({max(1, int(size)) for size in target_sizes}))
    spalex = audit_spalex_csv(spalex_csv, target_sizes=normalized_targets)
    current = audit_current_frequency_db(current_frequency_db)
    kaikki_forward = audit_kaikki_forward_db(kaikki_forward_db)
    kaikki_reverse = audit_kaikki_reverse_db(kaikki_reverse_db)
    stack = audit_combined_source_stack(
        spalex=spalex,
        current=current,
        kaikki_forward=kaikki_forward,
        kaikki_reverse=kaikki_reverse,
        target_sizes=normalized_targets,
    )
    findings = build_findings(spalex, current, kaikki_forward, kaikki_reverse, stack)
    return {
        "schema_version": 1,
        "pair": str(pair or DEFAULT_PAIR).strip().lower() or DEFAULT_PAIR,
        "generated_at": generated_at or _utc_now(),
        "decision": "spalex_kaikki_source_stack_audited",
        "runtime_policy_change": "none",
        "large_downloads": "none",
        "inputs": {
            "spalex_csv": str(Path(spalex_csv).expanduser().resolve(strict=False)),
            "current_frequency_db": str(
                Path(current_frequency_db).expanduser().resolve(strict=False)
            ),
            "kaikki_forward_db": str(Path(kaikki_forward_db).expanduser().resolve(strict=False)),
            "kaikki_reverse_db": str(Path(kaikki_reverse_db).expanduser().resolve(strict=False)),
            "target_sizes": list(normalized_targets),
        },
        "source_metadata": {
            "spalex": {
                "source_url": DEFAULT_SPALEX_SOURCE_URL,
                "doi": DEFAULT_SPALEX_DOI,
                "license_name": DEFAULT_SPALEX_LICENSE_NAME,
                "license_url": DEFAULT_SPALEX_LICENSE_URL,
                "role": "candidate_frontier_frequency_prevalence",
            },
            "kaikki": {
                "source_url": "https://kaikki.org/dictionary/rawdata.html",
                "source_family": "Wiktionary/Wiktextract/Kaikki",
                "license_posture": "review_required_cc_by_sa_gfdl_obligations",
                "role": "pos_gloss_dictionary_topic_enrichment",
            },
            "freq_es_cde": {
                "role": "current_seed_baseline_and_function_word_coverage",
            },
        },
        "methodology": {
            "spalex_ordering": "distinct clean spellings sorted by Zipf descending, then prevalence descending",
            "combined_frontier": (
                "current freq-es-cde distinct lemmas first, then SPALEX ranked clean spellings "
                "not already present"
            ),
            "kaikki_enrichment": (
                "SPALEX/CDE candidates are looked up against installed wiktionary-es-en "
                "headwords, POS, gloss rows, sense topics, tags, categories, and reverse "
                "wiktionary-en-es Spanish translation targets."
            ),
            "not_a_default_behavior_claim": (
                "The audit checks source suitability only. It does not change SRS admission, "
                "rulegen ranking, semantic-veto behavior, or publication policy."
            ),
        },
        "summary": build_summary(spalex, current, kaikki_forward, kaikki_reverse, stack, findings),
        "spalex": _strip_internal_rows(spalex),
        "current_frequency": _strip_internal_rows(current),
        "kaikki_forward": _strip_internal_rows(kaikki_forward),
        "kaikki_reverse": _strip_internal_rows(kaikki_reverse),
        "combined_stack": stack,
        "findings": findings,
        "recommended_next_steps": recommended_next_steps(findings),
    }


def audit_spalex_csv(path: Path, *, target_sizes: Sequence[int]) -> dict[str, object]:
    resolved = Path(path).expanduser().resolve(strict=False)
    base: dict[str, object] = {
        "path": str(resolved),
        "exists": resolved.exists(),
        "status": "ok",
        "issues": [],
        "target_readiness": [],
        "_ranked_lemmas": [],
    }
    if not resolved.exists() or not resolved.is_file():
        base["status"] = "error"
        base["issues"] = ["spalex_csv_missing"]
        return base

    rows: list[dict[str, object]] = []
    try:
        with resolved.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            columns = list(reader.fieldnames or [])
            for raw_row in reader:
                lemma = _normalize_lemma(raw_row.get("spelling"))
                row = {
                    "lemma": lemma,
                    "zipf": _to_float(raw_row.get("zipf")),
                    "freq": _to_float(raw_row.get("freq")),
                    "prevalence_total": _to_float(raw_row.get("prevalence_total")),
                    "percent_total": _to_float(raw_row.get("percent_total")),
                    "surface_clean": _is_clean_surface(lemma),
                    "raw": raw_row,
                }
                rows.append(row)
    except (OSError, UnicodeError, csv.Error) as exc:
        base["status"] = "error"
        base["issues"] = [f"spalex_csv_unreadable:{exc.__class__.__name__}"]
        return base

    required_missing = [column for column in SPALEX_REQUIRED_COLUMNS if column not in columns]
    distinct = _dedupe_spalex_rows(rows)
    clean_rows = [row for row in distinct if bool(row["surface_clean"])]
    ranked = sorted(
        clean_rows,
        key=lambda row: (
            _float_or_floor(row["zipf"]),
            _float_or_floor(row["prevalence_total"]),
            str(row["lemma"]),
        ),
        reverse=True,
    )
    issues: list[str] = []
    if required_missing:
        issues.append("missing_required_columns")
    if not ranked:
        issues.append("no_clean_spalex_rows")
    base.update(
        {
            "status": "review" if issues else "ok",
            "issues": issues,
            "columns": columns,
            "required_columns_missing": required_missing,
            "csv_size_bytes": resolved.stat().st_size,
            "csv_md5": _md5(resolved),
            "row_count": len(rows),
            "distinct_spelling_count": len(distinct),
            "clean_distinct_spelling_count": len(clean_rows),
            "column_coverage": {
                "freq": _coverage(rows, "freq"),
                "zipf": _coverage(rows, "zipf"),
                "percent_total": _coverage(rows, "percent_total"),
                "prevalence_total": _coverage(rows, "prevalence_total"),
            },
            "value_ranges": {
                "zipf": _range(rows, "zipf"),
                "freq": _range(rows, "freq"),
                "percent_total": _range(rows, "percent_total"),
                "prevalence_total": _range(rows, "prevalence_total"),
            },
            "top_20_by_zipf": [str(row["lemma"]) for row in ranked[:20]],
            "bottom_20_by_zipf": [str(row["lemma"]) for row in ranked[-20:]],
            "target_readiness": [
                {
                    "target_size": target,
                    "reaches_target": len(ranked) >= target,
                    "clean_distinct_spelling_count": len(ranked),
                }
                for target in target_sizes
            ],
            "_ranked_lemmas": [str(row["lemma"]) for row in ranked],
        }
    )
    return base


def audit_current_frequency_db(path: Path) -> dict[str, object]:
    resolved = _resolve_optional_pack_sqlite(path) or Path(path).expanduser().resolve(strict=False)
    base: dict[str, object] = {
        "path": str(resolved),
        "exists": resolved.exists(),
        "status": "ok",
        "issues": [],
        "_lemmas": [],
        "_pos_by_lemma": {},
    }
    if not resolved.exists() or not resolved.is_file():
        base["status"] = "error"
        base["issues"] = ["current_frequency_db_missing"]
        return base
    try:
        with sqlite3.connect(resolved) as conn:
            columns = _column_names(conn, "frequency")
            if "lemma" not in columns:
                base["status"] = "error"
                base["issues"] = ["current_frequency_missing_lemma_column"]
                return base
            order_column = "id" if "id" in columns else "rowid"
            rows = [
                (_normalize_lemma(lemma), pos)
                for lemma, pos in conn.execute(
                    f"""
                    SELECT lemma, {("pos" if "pos" in columns else "''")} FROM frequency
                    WHERE TRIM(COALESCE(lemma, '')) != ''
                    ORDER BY {order_column}
                    """
                )
            ]
    except sqlite3.Error as exc:
        base["status"] = "error"
        base["issues"] = [f"current_frequency_sqlite_error:{exc.__class__.__name__}"]
        return base
    lemmas: list[str] = []
    seen: set[str] = set()
    pos_by_lemma: dict[str, str] = {}
    for lemma, pos in rows:
        if not lemma or lemma in seen:
            continue
        seen.add(lemma)
        lemmas.append(lemma)
        pos_by_lemma[lemma] = str(pos or "")
    mapped_pos_count = sum(
        1
        for lemma, raw_pos in pos_by_lemma.items()
        if normalize_pos(
            raw_pos,
            language_pair=DEFAULT_PAIR,
            source_provider="freq-es-cde",
            source_profile="freq-es-cde",
        ).mapped
    )
    base.update(
        {
            "row_count": len(rows),
            "distinct_lemma_count": len(lemmas),
            "mapped_pos_count": mapped_pos_count,
            "mapped_pos_share": _share(mapped_pos_count, len(lemmas)),
            "top_20_by_current_order": lemmas[:20],
            "_lemmas": lemmas,
            "_pos_by_lemma": pos_by_lemma,
        }
    )
    return base


def audit_kaikki_forward_db(path: Path) -> dict[str, object]:
    resolved = _resolve_optional_pack_sqlite(path) or Path(path).expanduser().resolve(strict=False)
    base: dict[str, object] = {
        "path": str(resolved),
        "exists": resolved.exists(),
        "status": "ok",
        "issues": [],
        "_headwords": set(),
        "_gloss_headwords": set(),
        "_pos_by_lemma": {},
        "_topics_by_lemma": {},
        "_tags_by_lemma": {},
        "_categories_by_lemma": {},
    }
    if not resolved.exists() or not resolved.is_file():
        base["status"] = "error"
        base["issues"] = ["kaikki_forward_db_missing"]
        return base
    try:
        with sqlite3.connect(resolved) as conn:
            headword_table = _first_existing_table(conn, ("entries", "entry_meta"))
            if not headword_table:
                base["status"] = "error"
                base["issues"] = ["kaikki_forward_missing_headword_table"]
                return base
            entry_count = _count_rows(conn, headword_table)
            headwords = {
                _normalize_lemma(row[0])
                for row in conn.execute(
                    f"SELECT DISTINCT headword_lc FROM {headword_table} "
                    "WHERE TRIM(COALESCE(headword_lc, '')) != ''"
                )
            }
            gloss_headwords = {
                _normalize_lemma(row[0])
                for row in conn.execute(
                    "SELECT DISTINCT headword_lc FROM sense_glosses "
                    "WHERE TRIM(COALESCE(translation_lc, '')) != ''"
                )
            }
            pos_by_lemma: dict[str, list[str]] = defaultdict(list)
            for headword, raw_pos in conn.execute(
                "SELECT headword_lc, pos FROM entry_meta "
                "WHERE TRIM(COALESCE(headword_lc, '')) != ''"
            ):
                pos_by_lemma[_normalize_lemma(headword)].append(str(raw_pos or ""))
            topics_by_lemma: dict[str, set[str]] = defaultdict(set)
            tags_by_lemma: dict[str, set[str]] = defaultdict(set)
            categories_by_lemma: dict[str, set[str]] = defaultdict(set)
            for headword, tags_json, categories_json in conn.execute(
                "SELECT headword_lc, tags_json, categories_json FROM entry_meta"
            ):
                lemma = _normalize_lemma(headword)
                tags_by_lemma[lemma].update(_json_string_list(tags_json))
                categories_by_lemma[lemma].update(_json_string_list(categories_json))
            for headword, topics_json, tags_json, categories_json in conn.execute(
                "SELECT headword_lc, topics_json, tags_json, categories_json FROM sense_glosses"
            ):
                lemma = _normalize_lemma(headword)
                topics_by_lemma[lemma].update(_json_string_list(topics_json))
                tags_by_lemma[lemma].update(_json_string_list(tags_json))
                categories_by_lemma[lemma].update(_json_string_list(categories_json))
            meta = _sqlite_metadata(conn)
    except sqlite3.Error as exc:
        base["status"] = "error"
        base["issues"] = [f"kaikki_forward_sqlite_error:{exc.__class__.__name__}"]
        return base
    mapped_headwords = 0
    lexical_bucket_headwords = 0
    canonical_counter: Counter[str] = Counter()
    raw_counter: Counter[str] = Counter()
    for lemma, raw_values in pos_by_lemma.items():
        normalized = [
            normalize_pos(
                raw_pos,
                language_pair=DEFAULT_PAIR,
                source_provider="wiktionary-es-en",
                source_profile="wiktionary",
            )
            for raw_pos in raw_values
        ]
        if any(row.mapped for row in normalized):
            mapped_headwords += 1
        if any(row.bucket != "other" for row in normalized):
            lexical_bucket_headwords += 1
        canonical_counter.update(row.canonical for row in normalized)
        raw_counter.update(raw_values)
    base.update(
        {
            "entry_row_count": entry_count,
            "distinct_headword_count": len(headwords),
            "distinct_gloss_headword_count": len(gloss_headwords),
            "pos_headword_count": len(pos_by_lemma),
            "mapped_pos_headword_count": mapped_headwords,
            "lexical_bucket_headword_count": lexical_bucket_headwords,
            "topic_headword_count": sum(1 for values in topics_by_lemma.values() if values),
            "tag_headword_count": sum(1 for values in tags_by_lemma.values() if values),
            "category_headword_count": sum(1 for values in categories_by_lemma.values() if values),
            "top_canonical_pos": canonical_counter.most_common(20),
            "top_raw_pos": raw_counter.most_common(20),
            "top_topics": _counter_from_value_sets(topics_by_lemma).most_common(20),
            "metadata": meta,
            "_headwords": headwords,
            "_gloss_headwords": gloss_headwords,
            "_pos_by_lemma": dict(pos_by_lemma),
            "_topics_by_lemma": {lemma: set(values) for lemma, values in topics_by_lemma.items()},
            "_tags_by_lemma": {lemma: set(values) for lemma, values in tags_by_lemma.items()},
            "_categories_by_lemma": {
                lemma: set(values) for lemma, values in categories_by_lemma.items()
            },
        }
    )
    return base


def _resolve_optional_pack_sqlite(path: Path | None) -> Path | None:
    if path is None:
        return None
    requested = Path(path).expanduser().resolve(strict=False)
    if requested.is_file():
        return requested
    if requested.suffix == ".sqlite":
        managed = requested.parent / requested.stem / "main.sqlite"
        if managed.is_file():
            return managed.expanduser().resolve(strict=False)
    if requested.is_dir():
        managed = requested / "main.sqlite"
        if managed.is_file():
            return managed.expanduser().resolve(strict=False)
    return None


def audit_kaikki_reverse_db(path: Path) -> dict[str, object]:
    resolved = Path(path).expanduser().resolve(strict=False)
    base: dict[str, object] = {
        "path": str(resolved),
        "exists": resolved.exists(),
        "status": "ok",
        "issues": [],
        "_translation_targets": set(),
    }
    if not resolved.exists() or not resolved.is_file():
        base["status"] = "error"
        base["issues"] = ["kaikki_reverse_db_missing"]
        return base
    try:
        with sqlite3.connect(resolved) as conn:
            entry_count = _count_rows(conn, "entries")
            headwords = {
                _normalize_lemma(row[0])
                for row in conn.execute(
                    "SELECT DISTINCT headword_lc FROM entries "
                    "WHERE TRIM(COALESCE(headword_lc, '')) != ''"
                )
            }
            targets = {
                _normalize_lemma(row[0])
                for row in conn.execute(
                    "SELECT DISTINCT translation_lc FROM entries "
                    "WHERE TRIM(COALESCE(translation_lc, '')) != ''"
                )
            }
            meta = _sqlite_metadata(conn)
    except sqlite3.Error as exc:
        base["status"] = "error"
        base["issues"] = [f"kaikki_reverse_sqlite_error:{exc.__class__.__name__}"]
        return base
    base.update(
        {
            "entry_row_count": entry_count,
            "distinct_english_headword_count": len(headwords),
            "distinct_spanish_translation_target_count": len(targets),
            "metadata": meta,
            "_translation_targets": targets,
        }
    )
    return base


def audit_combined_source_stack(
    *,
    spalex: Mapping[str, object],
    current: Mapping[str, object],
    kaikki_forward: Mapping[str, object],
    kaikki_reverse: Mapping[str, object],
    target_sizes: Sequence[int],
) -> dict[str, object]:
    current_lemmas = list(current.get("_lemmas") or [])
    current_pos = dict(current.get("_pos_by_lemma") or {})
    spalex_ranked = list(spalex.get("_ranked_lemmas") or [])
    cde_set = set(current_lemmas)
    spalex_set = set(spalex_ranked)
    combined_rows = _combined_frontier_rows(current_lemmas, spalex_ranked)
    headwords = set(kaikki_forward.get("_headwords") or set())
    gloss_headwords = set(kaikki_forward.get("_gloss_headwords") or set())
    kaikki_pos = dict(kaikki_forward.get("_pos_by_lemma") or {})
    topics_by_lemma = dict(kaikki_forward.get("_topics_by_lemma") or {})
    tags_by_lemma = dict(kaikki_forward.get("_tags_by_lemma") or {})
    categories_by_lemma = dict(kaikki_forward.get("_categories_by_lemma") or {})
    reverse_targets = set(kaikki_reverse.get("_translation_targets") or set())
    target_readiness = []
    for target_size in target_sizes:
        rows = combined_rows[:target_size]
        lemmas = [row["lemma"] for row in rows]
        baseline_count = sum(1 for row in rows if row["source"] == "freq-es-cde")
        spalex_added_count = sum(1 for row in rows if row["source"] == "spalex")
        mapped_count = 0
        lexical_count = 0
        canonical_counter: Counter[str] = Counter()
        raw_counter: Counter[str] = Counter()
        for lemma in lemmas:
            normalized_pos_rows = []
            if lemma in current_pos:
                normalized_pos_rows.append(
                    normalize_pos(
                        current_pos[lemma],
                        language_pair=DEFAULT_PAIR,
                        source_provider="freq-es-cde",
                        source_profile="freq-es-cde",
                    )
                )
            normalized_pos_rows.extend(
                normalize_pos(
                    raw_pos,
                    language_pair=DEFAULT_PAIR,
                    source_provider="wiktionary-es-en",
                    source_profile="wiktionary",
                )
                for raw_pos in kaikki_pos.get(lemma, [])
            )
            if any(row.mapped for row in normalized_pos_rows):
                mapped_count += 1
            if any(row.bucket != "other" for row in normalized_pos_rows):
                lexical_count += 1
            canonical_counter.update(row.canonical for row in normalized_pos_rows)
            raw_counter.update(row.raw for row in normalized_pos_rows)
        topic_count = sum(1 for lemma in lemmas if topics_by_lemma.get(lemma))
        metadata_count = sum(
            1
            for lemma in lemmas
            if topics_by_lemma.get(lemma)
            or tags_by_lemma.get(lemma)
            or categories_by_lemma.get(lemma)
        )
        medicine_count = sum(
            1
            for lemma in lemmas
            if _has_medicine_signal(
                topics_by_lemma.get(lemma, set()),
                categories_by_lemma.get(lemma, set()),
            )
        )
        target_readiness.append(
            {
                "target_size": target_size,
                "reaches_target": len(rows) >= target_size,
                "baseline_rows": baseline_count,
                "spalex_added_rows": spalex_added_count,
                "kaikki_headword_count": sum(1 for lemma in lemmas if lemma in headwords),
                "kaikki_headword_share": _share(
                    sum(1 for lemma in lemmas if lemma in headwords), len(rows)
                ),
                "kaikki_gloss_count": sum(1 for lemma in lemmas if lemma in gloss_headwords),
                "kaikki_gloss_share": _share(
                    sum(1 for lemma in lemmas if lemma in gloss_headwords), len(rows)
                ),
                "pos_mapped_from_cde_or_kaikki_count": mapped_count,
                "pos_mapped_from_cde_or_kaikki_share": _share(mapped_count, len(rows)),
                "lexical_bucket_count": lexical_count,
                "lexical_bucket_share": _share(lexical_count, len(rows)),
                "explicit_topic_count": topic_count,
                "explicit_topic_share": _share(topic_count, len(rows)),
                "any_kaikki_metadata_count": metadata_count,
                "any_kaikki_metadata_share": _share(metadata_count, len(rows)),
                "medicine_signal_count": medicine_count,
                "medicine_signal_share": _share(medicine_count, len(rows)),
                "reverse_spanish_target_count": sum(
                    1 for lemma in lemmas if lemma in reverse_targets
                ),
                "reverse_spanish_target_share": _share(
                    sum(1 for lemma in lemmas if lemma in reverse_targets), len(rows)
                ),
                "sample_missing_kaikki_headwords": [
                    lemma for lemma in lemmas if lemma not in headwords
                ][:25],
                "top_canonical_pos": canonical_counter.most_common(15),
                "top_raw_pos": raw_counter.most_common(15),
            }
        )
    return {
        "combined_distinct_candidate_count": len(combined_rows),
        "current_cde_distinct_count": len(cde_set),
        "spalex_distinct_clean_count": len(spalex_ranked),
        "cde_in_spalex_count": len(cde_set & spalex_set),
        "cde_missing_from_spalex_count": len(cde_set - spalex_set),
        "cde_missing_from_spalex_sample": sorted(cde_set - spalex_set)[:50],
        "spalex_not_in_cde_count": len(spalex_set - cde_set),
        "target_readiness": target_readiness,
    }


def _combined_frontier_rows(
    current_lemmas: Sequence[str], spalex_ranked: Sequence[str]
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    seen: set[str] = set()
    for lemma in current_lemmas:
        if lemma and lemma not in seen:
            seen.add(lemma)
            rows.append({"lemma": lemma, "source": "freq-es-cde"})
    for lemma in spalex_ranked:
        if lemma and lemma not in seen:
            seen.add(lemma)
            rows.append({"lemma": lemma, "source": "spalex"})
    return rows


def _dedupe_spalex_rows(rows: Iterable[Mapping[str, object]]) -> list[dict[str, object]]:
    best: dict[str, dict[str, object]] = {}
    for row in rows:
        lemma = str(row.get("lemma") or "")
        if not lemma:
            continue
        old = best.get(lemma)
        if old is None:
            best[lemma] = dict(row)
            continue
        current_key = (
            _float_or_floor(row.get("zipf")),
            _float_or_floor(row.get("prevalence_total")),
        )
        old_key = (
            _float_or_floor(old.get("zipf")),
            _float_or_floor(old.get("prevalence_total")),
        )
        if current_key > old_key:
            best[lemma] = dict(row)
    return list(best.values())


def _column_names(conn: sqlite3.Connection, table_name: str) -> list[str]:
    return [str(row[1]) for row in conn.execute(f"PRAGMA table_info({table_name})")]


def _first_existing_table(conn: sqlite3.Connection, table_names: Sequence[str]) -> str:
    for table_name in table_names:
        exists = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
            (table_name,),
        ).fetchone()
        if exists:
            return table_name
    return ""


def _count_rows(conn: sqlite3.Connection, table_name: str) -> int:
    return int(conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0])


def _sqlite_metadata(conn: sqlite3.Connection) -> dict[str, object]:
    try:
        row = conn.execute("SELECT value FROM meta WHERE key = 'metadata'").fetchone()
    except sqlite3.Error:
        return {}
    if not row:
        return {}
    try:
        parsed = json.loads(str(row[0] or "{}"))
    except json.JSONDecodeError:
        return {"raw_metadata": str(row[0] or "")}
    return parsed if isinstance(parsed, dict) else {}


def _json_string_list(value: object) -> set[str]:
    text = str(value or "").strip()
    if not text or text == "[]":
        return set()
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return set()
    if not isinstance(parsed, list):
        return set()
    return {_normalize_lemma(item) for item in parsed if _normalize_lemma(item)}


def _counter_from_value_sets(values_by_lemma: Mapping[str, set[str]]) -> Counter[str]:
    counter: Counter[str] = Counter()
    for values in values_by_lemma.values():
        counter.update(values)
    return counter


def _has_medicine_signal(topics: object, categories: object) -> bool:
    values = set(topics or set()) | set(categories or set())
    if values & KAIKKI_MEDICINE_TOPIC_TERMS:
        return True
    return any(any(marker in value for marker in KAIKKI_MEDICINE_SUBSTRINGS) for value in values)


def _strip_internal_rows(value: object) -> object:
    if isinstance(value, dict):
        return {
            key: _strip_internal_rows(item)
            for key, item in value.items()
            if not str(key).startswith("_")
        }
    if isinstance(value, list):
        return [_strip_internal_rows(item) for item in value]
    if isinstance(value, set):
        return sorted(value)
    return value


def _normalize_lemma(value: object) -> str:
    return unicodedata.normalize("NFC", str(value or "").strip().lower())


def _is_clean_surface(value: object) -> bool:
    text = _normalize_lemma(value)
    return bool(text) and all(character.isalpha() for character in text)


def _to_float(value: object) -> float | None:
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return None


def _float_or_floor(value: object) -> float:
    parsed = _to_float(value)
    return parsed if parsed is not None else -999999.0


def _coverage(rows: Sequence[Mapping[str, object]], key: str) -> dict[str, object]:
    count = sum(1 for row in rows if row.get(key) is not None)
    return {"nonempty_count": count, "share": _share(count, len(rows))}


def _range(rows: Sequence[Mapping[str, object]], key: str) -> dict[str, float | None]:
    values = [row.get(key) for row in rows if isinstance(row.get(key), int | float)]
    if not values:
        return {"min": None, "max": None}
    return {"min": min(values), "max": max(values)}


def _share(count: int, total: int) -> float:
    return float(count / total) if total else 0.0


def _md5(path: Path) -> str:
    digest = hashlib.md5()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


if __name__ == "__main__":
    raise SystemExit(main())
