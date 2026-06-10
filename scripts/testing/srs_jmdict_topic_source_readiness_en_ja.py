#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
import sys
from typing import Mapping, Sequence
import xml.etree.ElementTree as ET


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / "core"
sys.path.insert(0, str(CORE_ROOT))

from lexishift_core.lexicon.word_package import normalize_reading  # noqa: E402
from lexishift_core.pos.normalization import normalize_pos  # noqa: E402


DEFAULT_DATA_ROOT = Path.home() / "Library/Application Support/LexiShift/LexiShift"
DEFAULT_FREQUENCY_DB = DEFAULT_DATA_ROOT / "frequency_packs" / "freq-ja-bccwj.sqlite"
DEFAULT_JMDICT = DEFAULT_DATA_ROOT / "language_packs" / "JMdict_e"
DEFAULT_TAXONOMY_JSON = (
    PROJECT_ROOT / "docs" / "test_inputs" / "srs_topic_preference_taxonomy_en_ja.json"
)
DEFAULT_JSON_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "srs_jmdict_topic_source_readiness_en_ja_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "srs_jmdict_topic_source_readiness_en_ja_latest.md"
)
DEFAULT_TOP_N = 10000
CANDIDATE_POS_BUCKETS = frozenset({"noun", "verb", "adjective", "adverb"})
STRONG_MATCH_MODES = frozenset({"exact", "alias"})
MAX_EXAMPLES_PER_FAMILY = 8

ORTHOGRAPHIC_ALIASES = {
    "\u70ba\u308b": ("\u3059\u308b",),
    "\u5c45\u308b": ("\u3044\u308b",),
    "\u6709\u308b": ("\u3042\u308b",),
    "\u6210\u308b": ("\u306a\u308b",),
    "\u7121\u3044": ("\u306a\u3044",),
    "\u826f\u3044": ("\u3088\u3044", "\u3044\u3044"),
    "\u5176\u306e": ("\u305d\u306e",),
    "\u6b64\u306e": ("\u3053\u306e",),
    "\u5176\u308c": ("\u305d\u308c",),
    "\u6b64\u308c": ("\u3053\u308c",),
}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Audit how much of the en-ja BCCWJ SRS frontier can be linked to "
            "trusted JMDict domain/topic fields. This is read-only and does not "
            "write admission overlays."
        )
    )
    parser.add_argument("--frequency-db", type=Path, default=DEFAULT_FREQUENCY_DB)
    parser.add_argument("--jmdict", type=Path, default=DEFAULT_JMDICT)
    parser.add_argument("--taxonomy-json", type=Path, default=DEFAULT_TAXONOMY_JSON)
    parser.add_argument("--top-n", type=int, default=DEFAULT_TOP_N)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_report(
        frequency_db=_resolve_path(args.frequency_db),
        jmdict_path=_resolve_path(args.jmdict),
        taxonomy_json=_resolve_path(args.taxonomy_json),
        top_n=max(1, int(args.top_n)),
    )
    json_out = _resolve_path(args.json_out)
    markdown_out = _resolve_path(args.markdown_out)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown_out.write_text(render_markdown(report), encoding="utf-8")
    print(f"Wrote JSON artifact to {json_out}")
    print(f"Wrote Markdown artifact to {markdown_out}")
    if args.fail_on_review and report["status"] != "ok":
        return 1
    return 0


def build_report(
    *,
    frequency_db: Path = DEFAULT_FREQUENCY_DB,
    jmdict_path: Path = DEFAULT_JMDICT,
    taxonomy_json: Path = DEFAULT_TAXONOMY_JSON,
    top_n: int = DEFAULT_TOP_N,
    generated_at: str | None = None,
) -> dict[str, object]:
    generated_at = generated_at or _utc_now()
    taxonomy = _load_json(taxonomy_json) if taxonomy_json.exists() else {}
    families = _taxonomy_families(taxonomy)
    trusted_mapping, review_mapping = _taxonomy_mappings(taxonomy)
    frontier = _load_frequency_frontier(frequency_db, top_n=top_n) if frequency_db.exists() else []
    term_index = _build_term_index(frontier)
    jmdict_audit = (
        _audit_jmdict(jmdict_path=jmdict_path, term_index=term_index)
        if jmdict_path.exists() and frontier
        else _empty_jmdict_audit()
    )
    row_reports = _build_row_reports(
        frontier=frontier,
        jmdict_rows=jmdict_audit["rows"],
        trusted_mapping=trusted_mapping,
        review_mapping=review_mapping,
    )
    family_reports = _build_family_reports(
        families=families,
        row_reports=row_reports,
    )
    source_summary = _source_summary(
        frontier=frontier,
        row_reports=row_reports,
        jmdict_audit=jmdict_audit,
        families=families,
    )
    findings = _findings(
        frequency_db=frequency_db,
        jmdict_path=jmdict_path,
        taxonomy_json=taxonomy_json,
        source_summary=source_summary,
        family_reports=family_reports,
        families=families,
    )
    status = "ok" if not any(row["level"] == "FAIL" for row in findings) else "review"
    return {
        "schema_version": 1,
        "status": status,
        "decision": (
            "srs_jmdict_topic_source_readiness_completed"
            if status == "ok"
            else "srs_jmdict_topic_source_readiness_needs_review"
        ),
        "generated_at": generated_at,
        "language_pair": "en-ja",
        "inputs": {
            "frequency_db": _repo_or_home_path(frequency_db),
            "jmdict": _repo_or_home_path(jmdict_path),
            "taxonomy_json": _repo_or_home_path(taxonomy_json),
            "top_n": int(top_n),
        },
        "method": {
            "frontier": "top BCCWJ frequency rows ordered by core_rank/rank",
            "candidate_pos_buckets": sorted(CANDIDATE_POS_BUCKETS),
            "trusted_topic_channel": "JMDict <field> labels mapped by product taxonomy",
            "strong_match_modes": sorted(STRONG_MATCH_MODES),
            "weaker_match_mode": "reading",
            "promotion_posture": (
                "source-readiness only; topic overlays and admission lift still need "
                "review packet, labels, and SRS admission validation"
            ),
        },
        "source_summary": source_summary,
        "family_reports": family_reports,
        "topic_candidate_inventory": _topic_candidate_inventory(row_reports),
        "top_jmdict_fields": _counter_rows(jmdict_audit["field_counter"], limit=30),
        "top_jmdict_misc_labels": _counter_rows(jmdict_audit["misc_counter"], limit=20),
        "top_jmdict_dialect_labels": _counter_rows(jmdict_audit["dialect_counter"], limit=20),
        "findings": findings,
    }


def _load_frequency_frontier(frequency_db: Path, *, top_n: int) -> list[dict[str, object]]:
    with sqlite3.connect(frequency_db) as conn:
        conn.row_factory = sqlite3.Row
        columns = {str(row[1]) for row in conn.execute("PRAGMA table_info(frequency)")}
        select_columns = [
            column
            for column in (
                "rank",
                "lform",
                "lemma",
                "pos",
                "sublemma",
                "wtype",
                "frequency",
                "pmw",
                "core_rank",
                "core_frequency",
                "core_pmw",
            )
            if column in columns
        ]
        rank_expr = _rank_expression(columns)
        sql = f"SELECT {', '.join(select_columns)} FROM frequency ORDER BY {rank_expr} ASC LIMIT ?"
        rows = conn.execute(sql, (int(top_n),)).fetchall()
    frontier: list[dict[str, object]] = []
    for index, row in enumerate(rows, start=1):
        raw = dict(row)
        pos_raw = _clean_str(raw.get("pos"))
        normalized_pos = normalize_pos(
            pos_raw,
            language_pair="en-ja",
            source_provider="freq-ja-bccwj",
            source_kind="frequency",
        )
        exact_terms, alias_terms, reading_terms = _row_terms(raw)
        frontier.append(
            {
                "row_index": index,
                "rank": _safe_number(raw.get("rank")),
                "core_rank": _safe_number(raw.get("core_rank")),
                "lemma": _clean_str(raw.get("lemma")),
                "lform": _clean_str(raw.get("lform")),
                "sublemma": _clean_str(raw.get("sublemma")),
                "wtype": _clean_str(raw.get("wtype")),
                "pos": pos_raw,
                "normalized_pos": {
                    "canonical": normalized_pos.canonical,
                    "bucket": normalized_pos.bucket,
                    "matched_rule": normalized_pos.matched_rule,
                    "mapped": normalized_pos.mapped,
                },
                "candidate_like": normalized_pos.bucket in CANDIDATE_POS_BUCKETS,
                "terms": {
                    "exact": sorted(exact_terms),
                    "alias": sorted(alias_terms),
                    "reading": sorted(reading_terms),
                },
                "frequency": _safe_number(raw.get("frequency")),
                "pmw": _safe_number(raw.get("pmw")),
                "core_frequency": _safe_number(raw.get("core_frequency")),
                "core_pmw": _safe_number(raw.get("core_pmw")),
            }
        )
    return frontier


def _rank_expression(columns: set[str]) -> str:
    if "core_rank" in columns and "rank" in columns:
        return "COALESCE(core_rank, rank)"
    if "core_rank" in columns:
        return "core_rank"
    if "rank" in columns:
        return "rank"
    return "rowid"


def _row_terms(row: Mapping[str, object]) -> tuple[set[str], set[str], set[str]]:
    exact_terms = {_clean_str(row.get("lemma")), _clean_str(row.get("sublemma"))}
    exact_terms = {term for term in exact_terms if term}
    normalized_exact_terms = {
        normalize_reading(term, language_tag="ja") for term in exact_terms if term
    }
    exact_terms.update(
        term for term in normalized_exact_terms if term and term != _clean_str(row.get("lform"))
    )
    alias_terms: set[str] = set()
    for term in exact_terms:
        alias_terms.update(ORTHOGRAPHIC_ALIASES.get(term, ()))
    reading_terms = {_clean_str(row.get("lform"))}
    reading_terms = {normalize_reading(term, language_tag="ja") for term in reading_terms if term}
    reading_terms = {term for term in reading_terms if term and term not in exact_terms}
    alias_terms = {term for term in alias_terms if term and term not in exact_terms}
    return exact_terms, alias_terms, reading_terms


def _build_term_index(
    frontier: Sequence[Mapping[str, object]],
) -> dict[str, list[tuple[int, str]]]:
    term_index: dict[str, list[tuple[int, str]]] = defaultdict(list)
    for row in frontier:
        row_index = int(row["row_index"])
        terms = _as_mapping(row.get("terms"))
        for mode in ("exact", "alias", "reading"):
            for term in _string_list(terms.get(mode)):
                term_index[term].append((row_index, mode))
    return dict(term_index)


def _audit_jmdict(
    *,
    jmdict_path: Path,
    term_index: Mapping[str, Sequence[tuple[int, str]]],
) -> dict[str, object]:
    row_matches: dict[int, dict[str, object]] = defaultdict(_empty_row_match)
    field_counter: Counter[str] = Counter()
    misc_counter: Counter[str] = Counter()
    dialect_counter: Counter[str] = Counter()
    matched_entries = 0
    parsed_entries = 0
    for _event, elem in ET.iterparse(jmdict_path, events=("end",)):
        if elem.tag != "entry":
            continue
        parsed_entries += 1
        entry_terms = _jmdict_entry_terms(elem)
        hits = _entry_hits(entry_terms=entry_terms, term_index=term_index)
        if hits:
            matched_entries += 1
            fields = sorted(_element_texts(elem, "sense/field"))
            misc = sorted(_element_texts(elem, "sense/misc"))
            dialects = sorted(_element_texts(elem, "sense/dial"))
            pos = sorted(_element_texts(elem, "sense/pos"))
            glosses = _first_values(_element_texts(elem, "sense/gloss"), limit=8)
            field_counter.update(fields)
            misc_counter.update(misc)
            dialect_counter.update(dialects)
            for row_index, match in hits.items():
                row_match = row_matches[row_index]
                row_match["entry_count"] = int(row_match["entry_count"]) + 1
                row_match["match_modes"].update(match["modes"])
                row_match["matched_terms"].update(match["terms"])
                row_match["fields"].update(fields)
                row_match["misc"].update(misc)
                row_match["dialects"].update(dialects)
                row_match["pos"].update(pos)
                row_match["glosses"].update(glosses)
                strength = (
                    "strong"
                    if any(mode in STRONG_MATCH_MODES for mode in match["modes"])
                    else "reading_only"
                )
                bucket = row_match["buckets"][strength]
                bucket["entry_count"] = int(bucket["entry_count"]) + 1
                bucket["match_modes"].update(match["modes"])
                bucket["matched_terms"].update(match["terms"])
                bucket["fields"].update(fields)
                bucket["misc"].update(misc)
                bucket["dialects"].update(dialects)
                bucket["pos"].update(pos)
                bucket["glosses"].update(glosses)
        elem.clear()
    rows = {
        row_index: {
            "entry_count": row_match["entry_count"],
            "match_modes": sorted(row_match["match_modes"], key=_match_mode_sort_key),
            "matched_terms": sorted(row_match["matched_terms"]),
            "fields": sorted(row_match["fields"]),
            "misc": sorted(row_match["misc"]),
            "dialects": sorted(row_match["dialects"]),
            "pos": sorted(row_match["pos"]),
            "glosses": sorted(row_match["glosses"])[:12],
            "buckets": {
                strength: _serialize_match_bucket(bucket)
                for strength, bucket in row_match["buckets"].items()
            },
        }
        for row_index, row_match in row_matches.items()
    }
    return {
        "parsed_entries": parsed_entries,
        "matched_entries": matched_entries,
        "rows": rows,
        "field_counter": field_counter,
        "misc_counter": misc_counter,
        "dialect_counter": dialect_counter,
    }


def _empty_row_match() -> dict[str, object]:
    return {
        "entry_count": 0,
        "match_modes": set(),
        "matched_terms": set(),
        "fields": set(),
        "misc": set(),
        "dialects": set(),
        "pos": set(),
        "glosses": set(),
        "buckets": {
            "strong": _empty_match_bucket(),
            "reading_only": _empty_match_bucket(),
        },
    }


def _empty_match_bucket() -> dict[str, object]:
    return {
        "entry_count": 0,
        "match_modes": set(),
        "matched_terms": set(),
        "fields": set(),
        "misc": set(),
        "dialects": set(),
        "pos": set(),
        "glosses": set(),
    }


def _serialize_match_bucket(bucket: Mapping[str, object]) -> dict[str, object]:
    return {
        "entry_count": int(bucket.get("entry_count") or 0),
        "match_modes": sorted(_as_set(bucket.get("match_modes")), key=_match_mode_sort_key),
        "matched_terms": sorted(_as_set(bucket.get("matched_terms"))),
        "fields": sorted(_as_set(bucket.get("fields"))),
        "misc": sorted(_as_set(bucket.get("misc"))),
        "dialects": sorted(_as_set(bucket.get("dialects"))),
        "pos": sorted(_as_set(bucket.get("pos"))),
        "glosses": sorted(_as_set(bucket.get("glosses")))[:12],
    }


def _jmdict_entry_terms(elem: ET.Element) -> dict[str, set[str]]:
    terms: dict[str, set[str]] = defaultdict(set)
    surfaces = set(_element_texts(elem, "k_ele/keb"))
    readings = {
        normalize_reading(term, language_tag="ja") for term in _element_texts(elem, "r_ele/reb")
    }
    for surface in surfaces:
        if surface:
            terms[surface].add("surface")
    for reading in readings:
        if not reading:
            continue
        terms[reading].add("reading")
        if not surfaces:
            terms[reading].add("reading_no_surface")
    return dict(terms)


def _entry_hits(
    *,
    entry_terms: Mapping[str, set[str]],
    term_index: Mapping[str, Sequence[tuple[int, str]]],
) -> dict[int, dict[str, set[str]]]:
    hits: dict[int, dict[str, set[str]]] = {}
    for term, entry_term_kinds in entry_terms.items():
        for row_index, mode in term_index.get(term, ()):
            resolved_mode = _resolve_jmdict_match_mode(
                row_mode=mode,
                entry_term_kinds=entry_term_kinds,
            )
            if not resolved_mode:
                continue
            row_hit = hits.setdefault(row_index, {"modes": set(), "terms": set()})
            row_hit["modes"].add(resolved_mode)
            row_hit["terms"].add(term)
    return hits


def _resolve_jmdict_match_mode(
    *,
    row_mode: str,
    entry_term_kinds: set[str],
) -> str:
    if row_mode in STRONG_MATCH_MODES:
        if "surface" in entry_term_kinds or "reading_no_surface" in entry_term_kinds:
            return row_mode
        return ""
    if row_mode == "reading" and "reading" in entry_term_kinds:
        return "reading"
    return ""


def _element_texts(elem: ET.Element, path: str) -> list[str]:
    return [_clean_str(child.text) for child in elem.findall(path) if _clean_str(child.text)]


def _build_row_reports(
    *,
    frontier: Sequence[Mapping[str, object]],
    jmdict_rows: Mapping[int, Mapping[str, object]],
    trusted_mapping: Mapping[str, Sequence[dict[str, object]]],
    review_mapping: Mapping[str, Sequence[dict[str, object]]],
) -> list[dict[str, object]]:
    row_reports: list[dict[str, object]] = []
    for row in frontier:
        row_index = int(row["row_index"])
        jmdict = _as_mapping(jmdict_rows.get(row_index))
        buckets = _as_mapping(jmdict.get("buckets"))
        strong_bucket = _as_mapping(buckets.get("strong"))
        reading_bucket = _as_mapping(buckets.get("reading_only"))
        strong_trusted_families, strong_source_labels_by_family = _mapped_families(
            labels=_string_list(strong_bucket.get("fields")),
            mapping=trusted_mapping,
        )
        reading_trusted_families, reading_source_labels_by_family = _mapped_families(
            labels=_string_list(reading_bucket.get("fields")),
            mapping=trusted_mapping,
        )
        reading_source_labels_by_family = {
            family_id: labels
            for family_id, labels in reading_source_labels_by_family.items()
            if family_id not in strong_source_labels_by_family
        }
        reading_trusted_families = sorted(reading_source_labels_by_family)
        trusted_families = sorted({*strong_trusted_families, *reading_trusted_families})
        trusted_source_labels_by_family = _merge_label_maps(
            strong_source_labels_by_family,
            reading_source_labels_by_family,
        )
        strong_review_families, strong_review_source_labels_by_family = _mapped_families(
            labels=[
                *_string_list(strong_bucket.get("misc")),
                *_string_list(strong_bucket.get("dialects")),
            ],
            mapping=review_mapping,
        )
        reading_review_families, reading_review_source_labels_by_family = _mapped_families(
            labels=[
                *_string_list(reading_bucket.get("misc")),
                *_string_list(reading_bucket.get("dialects")),
            ],
            mapping=review_mapping,
        )
        reading_review_source_labels_by_family = {
            family_id: labels
            for family_id, labels in reading_review_source_labels_by_family.items()
            if family_id not in strong_review_source_labels_by_family
        }
        reading_review_families = sorted(reading_review_source_labels_by_family)
        review_families = sorted({*strong_review_families, *reading_review_families})
        review_source_labels_by_family = _merge_label_maps(
            strong_review_source_labels_by_family,
            reading_review_source_labels_by_family,
        )
        match_modes = _string_list(jmdict.get("match_modes"))
        strong_match = any(mode in STRONG_MATCH_MODES for mode in match_modes)
        row_reports.append(
            {
                "row_index": row_index,
                "rank": row.get("core_rank") or row.get("rank"),
                "lemma": row.get("lemma"),
                "lform": row.get("lform"),
                "pos": row.get("pos"),
                "pos_bucket": _as_mapping(row.get("normalized_pos")).get("bucket"),
                "candidate_like": bool(row.get("candidate_like")),
                "jmdict_entry_count": int(jmdict.get("entry_count") or 0),
                "jmdict_match_modes": match_modes,
                "jmdict_strong_match": bool(strong_match),
                "jmdict_matched_terms": _string_list(jmdict.get("matched_terms")),
                "jmdict_fields": _string_list(jmdict.get("fields")),
                "jmdict_misc": _string_list(jmdict.get("misc")),
                "jmdict_dialects": _string_list(jmdict.get("dialects")),
                "jmdict_glosses": _string_list(jmdict.get("glosses"))[:8],
                "trusted_topic_families": trusted_families,
                "trusted_topic_families_by_strength": {
                    "strong": strong_trusted_families,
                    "reading_only": reading_trusted_families,
                },
                "trusted_topic_source_labels": _flatten_label_map(trusted_source_labels_by_family),
                "trusted_topic_source_labels_by_family": trusted_source_labels_by_family,
                "trusted_topic_source_labels_by_family_strength": {
                    "strong": strong_source_labels_by_family,
                    "reading_only": reading_source_labels_by_family,
                },
                "review_only_families": review_families,
                "review_only_families_by_strength": {
                    "strong": strong_review_families,
                    "reading_only": reading_review_families,
                },
                "review_only_source_labels": _flatten_label_map(review_source_labels_by_family),
                "review_only_source_labels_by_family": review_source_labels_by_family,
                "jmdict_match_modes_by_strength": {
                    "strong": _string_list(strong_bucket.get("match_modes")),
                    "reading_only": _string_list(reading_bucket.get("match_modes")),
                },
                "jmdict_matched_terms_by_strength": {
                    "strong": _string_list(strong_bucket.get("matched_terms")),
                    "reading_only": _string_list(reading_bucket.get("matched_terms")),
                },
                "jmdict_glosses_by_strength": {
                    "strong": _string_list(strong_bucket.get("glosses")),
                    "reading_only": _string_list(reading_bucket.get("glosses")),
                },
            }
        )
    return row_reports


def _mapped_families(
    *,
    labels: Sequence[str],
    mapping: Mapping[str, Sequence[dict[str, object]]],
) -> tuple[list[str], dict[str, list[str]]]:
    family_ids: set[str] = set()
    source_labels_by_family: dict[str, set[str]] = defaultdict(set)
    for label in labels:
        for mapped in mapping.get(_normalize_label(label), ()):
            family_id = _clean_str(mapped.get("target_family"))
            if family_id:
                family_ids.add(family_id)
                source_labels_by_family[family_id].add(
                    _clean_str(mapped.get("source_label")) or label
                )
    return sorted(family_ids), {
        family_id: sorted(source_labels)
        for family_id, source_labels in sorted(source_labels_by_family.items())
    }


def _flatten_label_map(value: Mapping[str, Sequence[str]]) -> list[str]:
    labels: set[str] = set()
    for row in value.values():
        labels.update(_string_list(row))
    return sorted(labels)


def _merge_label_maps(
    *values: Mapping[str, Sequence[str]],
) -> dict[str, list[str]]:
    merged: dict[str, set[str]] = defaultdict(set)
    for value in values:
        for family_id, labels in value.items():
            merged[family_id].update(_string_list(labels))
    return {family_id: sorted(labels) for family_id, labels in sorted(merged.items())}


def _build_family_reports(
    *,
    families: Mapping[str, Mapping[str, object]],
    row_reports: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    reports: list[dict[str, object]] = []
    for family_id, family in families.items():
        strong_rows = [
            row
            for row in row_reports
            if bool(row.get("candidate_like"))
            and family_id
            in _string_list(
                _as_mapping(row.get("trusted_topic_families_by_strength")).get("strong")
            )
        ]
        reading_rows = [
            row
            for row in row_reports
            if bool(row.get("candidate_like"))
            and family_id
            in _string_list(
                _as_mapping(row.get("trusted_topic_families_by_strength")).get("reading_only")
            )
        ]
        rows = [*strong_rows, *reading_rows]
        source_label_counter: Counter[str] = Counter()
        for row in rows:
            labels_by_strength = _as_mapping(
                row.get("trusted_topic_source_labels_by_family_strength")
            )
            for strength in ("strong", "reading_only"):
                labels_by_family = _as_mapping(labels_by_strength.get(strength))
                source_label_counter.update(_string_list(labels_by_family.get(family_id)))
        reports.append(
            {
                "family_id": family_id,
                "display_name": family.get("display_name") or family_id,
                "axis": family.get("axis") or "topic",
                "taxonomy_readiness_state": family.get("readiness_state") or "",
                "trusted_rows": len(rows),
                "trusted_candidate_like_rows": len(rows),
                "strong_match_candidate_like_rows": len(strong_rows),
                "reading_only_candidate_like_rows": len(reading_rows),
                "top_source_labels": _counter_rows(source_label_counter, limit=8),
                "examples": _family_examples(
                    family_id=family_id,
                    rows=strong_rows or reading_rows,
                    limit=MAX_EXAMPLES_PER_FAMILY,
                ),
            }
        )
    return reports


def _family_examples(
    *,
    family_id: str,
    rows: Sequence[Mapping[str, object]],
    limit: int,
) -> list[dict[str, object]]:
    sorted_rows = sorted(rows, key=lambda row: float(row.get("rank") or 9999999))
    examples: list[dict[str, object]] = []
    for row in sorted_rows[:limit]:
        labels_by_family = _as_mapping(row.get("trusted_topic_source_labels_by_family"))
        examples.append(
            {
                "rank": row.get("rank"),
                "lemma": row.get("lemma"),
                "lform": row.get("lform"),
                "pos": row.get("pos"),
                "match_modes": _string_list(row.get("jmdict_match_modes")),
                "matched_terms": _string_list(row.get("jmdict_matched_terms"))[:4],
                "source_labels": _string_list(labels_by_family.get(family_id))[:4],
                "glosses": _string_list(row.get("jmdict_glosses"))[:4],
            }
        )
    return examples


def _source_summary(
    *,
    frontier: Sequence[Mapping[str, object]],
    row_reports: Sequence[Mapping[str, object]],
    jmdict_audit: Mapping[str, object],
    families: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    frontier_count = len(frontier)
    candidate_like_count = sum(1 for row in frontier if bool(row.get("candidate_like")))
    jmdict_rows = [row for row in row_reports if int(row.get("jmdict_entry_count") or 0) > 0]
    jmdict_candidate_rows = [row for row in jmdict_rows if bool(row.get("candidate_like"))]
    strong_jmdict_candidate_rows = [
        row for row in jmdict_candidate_rows if bool(row.get("jmdict_strong_match"))
    ]
    trusted_rows = [row for row in row_reports if _string_list(row.get("trusted_topic_families"))]
    trusted_candidate_rows = [row for row in trusted_rows if bool(row.get("candidate_like"))]
    trusted_strong_candidate_rows = [
        row
        for row in trusted_candidate_rows
        if _string_list(_as_mapping(row.get("trusted_topic_families_by_strength")).get("strong"))
    ]
    review_rows = [row for row in row_reports if _string_list(row.get("review_only_families"))]
    review_candidate_rows = [row for row in review_rows if bool(row.get("candidate_like"))]
    family_with_strong_candidates = {
        family_id
        for row in trusted_strong_candidate_rows
        for family_id in _string_list(
            _as_mapping(row.get("trusted_topic_families_by_strength")).get("strong")
        )
    }
    return {
        "frontier_rows": frontier_count,
        "candidate_like_rows": candidate_like_count,
        "jmdict_parsed_entries": int(jmdict_audit.get("parsed_entries") or 0),
        "jmdict_matched_entries": int(jmdict_audit.get("matched_entries") or 0),
        "jmdict_matched_rows": len(jmdict_rows),
        "jmdict_matched_candidate_like_rows": len(jmdict_candidate_rows),
        "jmdict_strong_matched_candidate_like_rows": len(strong_jmdict_candidate_rows),
        "trusted_topic_rows": len(trusted_rows),
        "trusted_topic_candidate_like_rows": len(trusted_candidate_rows),
        "trusted_topic_strong_match_candidate_like_rows": len(trusted_strong_candidate_rows),
        "review_only_rows": len(review_rows),
        "review_only_candidate_like_rows": len(review_candidate_rows),
        "families_total": len(families),
        "families_with_strong_candidate_rows": len(family_with_strong_candidates),
        "candidate_like_jmdict_match_rate": _ratio(
            len(jmdict_candidate_rows), candidate_like_count
        ),
        "candidate_like_strong_jmdict_match_rate": _ratio(
            len(strong_jmdict_candidate_rows), candidate_like_count
        ),
        "candidate_like_trusted_topic_rate": _ratio(
            len(trusted_candidate_rows), candidate_like_count
        ),
        "candidate_like_trusted_strong_topic_rate": _ratio(
            len(trusted_strong_candidate_rows), candidate_like_count
        ),
    }


def _topic_candidate_inventory(
    row_reports: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    inventory: list[dict[str, object]] = []
    for row in row_reports:
        if not bool(row.get("candidate_like")):
            continue
        labels_by_strength = _as_mapping(row.get("trusted_topic_source_labels_by_family_strength"))
        match_modes_by_strength = _as_mapping(row.get("jmdict_match_modes_by_strength"))
        matched_terms_by_strength = _as_mapping(row.get("jmdict_matched_terms_by_strength"))
        glosses_by_strength = _as_mapping(row.get("jmdict_glosses_by_strength"))
        for strength in ("strong", "reading_only"):
            labels_by_family = _as_mapping(labels_by_strength.get(strength))
            for family_id, raw_labels in labels_by_family.items():
                source_labels = _string_list(raw_labels)
                if not family_id or not source_labels:
                    continue
                inventory.append(
                    {
                        "family_id": family_id,
                        "row_index": row.get("row_index"),
                        "rank": row.get("rank"),
                        "lemma": row.get("lemma"),
                        "lform": row.get("lform"),
                        "pos": row.get("pos"),
                        "pos_bucket": row.get("pos_bucket"),
                        "match_strength": strength,
                        "jmdict_match_modes": _string_list(match_modes_by_strength.get(strength)),
                        "jmdict_matched_terms": _string_list(
                            matched_terms_by_strength.get(strength)
                        )[:8],
                        "source_labels": source_labels,
                        "jmdict_glosses": _string_list(glosses_by_strength.get(strength))[:8],
                    }
                )
    return sorted(
        inventory,
        key=lambda item: (
            str(item.get("family_id") or ""),
            0 if item.get("match_strength") == "strong" else 1,
            float(item.get("rank") or 9999999),
            str(item.get("lemma") or ""),
        ),
    )


def _findings(
    *,
    frequency_db: Path,
    jmdict_path: Path,
    taxonomy_json: Path,
    source_summary: Mapping[str, object],
    family_reports: Sequence[Mapping[str, object]],
    families: Mapping[str, Mapping[str, object]],
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    findings.append(
        _finding(
            "PASS" if frequency_db.exists() else "FAIL",
            "bccwj_frequency_db_present",
            f"BCCWJ frequency DB path: {_repo_or_home_path(frequency_db)}",
        )
    )
    findings.append(
        _finding(
            "PASS" if jmdict_path.exists() else "FAIL",
            "jmdict_present",
            f"JMDict path: {_repo_or_home_path(jmdict_path)}",
        )
    )
    findings.append(
        _finding(
            "PASS" if taxonomy_json.exists() else "FAIL",
            "taxonomy_present",
            f"Taxonomy path: {_repo_or_home_path(taxonomy_json)}",
        )
    )
    strong_topic_count = int(
        source_summary.get("trusted_topic_strong_match_candidate_like_rows") or 0
    )
    findings.append(
        _finding(
            "PASS" if strong_topic_count > 0 else "WARN",
            "trusted_jmdict_topics_present",
            f"Strong matched candidate-like rows with trusted topic fields: {strong_topic_count}",
        )
    )
    source_ready_family_ids = {
        family_id
        for family_id, family in families.items()
        if _clean_str(family.get("readiness_state")) in {"source_ready_candidate"}
    }
    missing_source_ready = sorted(
        str(report.get("family_id"))
        for report in family_reports
        if str(report.get("family_id")) in source_ready_family_ids
        and int(report.get("strong_match_candidate_like_rows") or 0) == 0
    )
    findings.append(
        _finding(
            "PASS" if not missing_source_ready else "WARN",
            "source_ready_families_have_candidates",
            (
                "All source-ready taxonomy families have strong candidate rows."
                if not missing_source_ready
                else "Source-ready families lacking strong candidate rows: "
                + ", ".join(missing_source_ready)
            ),
        )
    )
    return findings


def render_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("source_summary"))
    lines = [
        "# en-ja JMDict Topic Source Readiness",
        "",
        f"- status: `{report.get('status')}`",
        f"- decision: `{report.get('decision')}`",
        f"- generated_at: `{report.get('generated_at')}`",
        f"- language_pair: `{report.get('language_pair')}`",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
    ]
    for key in (
        "frontier_rows",
        "candidate_like_rows",
        "jmdict_matched_candidate_like_rows",
        "jmdict_strong_matched_candidate_like_rows",
        "trusted_topic_candidate_like_rows",
        "trusted_topic_strong_match_candidate_like_rows",
        "families_total",
        "families_with_strong_candidate_rows",
        "candidate_like_jmdict_match_rate",
        "candidate_like_strong_jmdict_match_rate",
        "candidate_like_trusted_topic_rate",
        "candidate_like_trusted_strong_topic_rate",
    ):
        lines.append(f"| `{key}` | `{summary.get(key)}` |")
    lines.extend(
        [
            "",
            "Strong matches are exact BCCWJ lemma/sublemma matches plus a small set "
            "of deterministic orthographic aliases. Reading-only matches are useful "
            "inventory but remain homophone-sensitive and need review before lift.",
            "",
            "## Family Coverage",
            "",
            "| Family | Taxonomy state | Strong candidate rows | Reading-only candidate rows | Top labels | Examples |",
            "| --- | --- | ---: | ---: | --- | --- |",
        ]
    )
    for family in _as_sequence(report.get("family_reports")):
        family_map = _as_mapping(family)
        labels = ", ".join(
            f"`{row.get('label')}` ({row.get('count')})"
            for row in _as_sequence(family_map.get("top_source_labels"))[:4]
        )
        examples = "; ".join(
            _format_example(_as_mapping(example))
            for example in _as_sequence(family_map.get("examples"))[:3]
        )
        lines.append(
            "| "
            f"`{family_map.get('family_id')}` | "
            f"`{family_map.get('taxonomy_readiness_state')}` | "
            f"`{family_map.get('strong_match_candidate_like_rows')}` | "
            f"`{family_map.get('reading_only_candidate_like_rows')}` | "
            f"{labels or '-'} | "
            f"{examples or '-'} |"
        )
    lines.extend(["", "## Findings", ""])
    for finding in _as_sequence(report.get("findings")):
        row = _as_mapping(finding)
        lines.append(f"- `{row.get('level')}` `{row.get('code')}`: {row.get('message')}")
    lines.extend(["", "## Next Gate", ""])
    lines.append(
        "This artifact only proves source-readiness. Promotion still needs a "
        "pair-local review packet, accepted labels or overlay rows, and "
        "admission-preview evidence that selected en-ja topics actually move SRS "
        "samples."
    )
    lines.append("")
    return "\n".join(lines)


def _format_example(example: Mapping[str, object]) -> str:
    lemma = example.get("lemma") or ""
    rank = example.get("rank") or ""
    labels = ", ".join(f"`{label}`" for label in _string_list(example.get("source_labels"))[:2])
    return f"`{lemma}` rank `{rank}` {labels}".strip()


def _taxonomy_families(taxonomy: Mapping[str, object]) -> dict[str, Mapping[str, object]]:
    families: dict[str, Mapping[str, object]] = {}
    for row in _as_sequence(taxonomy.get("families")):
        family = _as_mapping(row)
        family_id = _clean_str(family.get("id"))
        if family_id:
            families[family_id] = family
    return families


def _taxonomy_mappings(
    taxonomy: Mapping[str, object],
) -> tuple[dict[str, list[dict[str, object]]], dict[str, list[dict[str, object]]]]:
    trusted_channels = set(
        _string_list(_as_mapping(taxonomy.get("channel_policy")).get("trusted_mapping_channels"))
    )
    review_channels = set(
        _string_list(_as_mapping(taxonomy.get("channel_policy")).get("review_only_channels"))
    )
    trusted: dict[str, list[dict[str, object]]] = defaultdict(list)
    review: dict[str, list[dict[str, object]]] = defaultdict(list)
    for raw in _as_sequence(taxonomy.get("source_label_mappings")):
        row = dict(_as_mapping(raw))
        label = _normalize_label(row.get("source_label"))
        channel = _clean_str(row.get("source_channel"))
        if not label or not channel:
            continue
        if channel in trusted_channels:
            trusted[label].append(row)
        elif channel in review_channels:
            review[label].append(row)
    return dict(trusted), dict(review)


def _empty_jmdict_audit() -> dict[str, object]:
    return {
        "parsed_entries": 0,
        "matched_entries": 0,
        "rows": {},
        "field_counter": Counter(),
        "misc_counter": Counter(),
        "dialect_counter": Counter(),
    }


def _counter_rows(counter: object, *, limit: int) -> list[dict[str, object]]:
    if not isinstance(counter, Counter):
        return []
    return [
        {"label": label, "count": count} for label, count in counter.most_common(max(0, int(limit)))
    ]


def _finding(level: str, code: str, message: str) -> dict[str, str]:
    return {"level": level, "code": code, "message": message}


def _first_values(values: Sequence[str], *, limit: int) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
        if len(result) >= limit:
            break
    return result


def _load_json(path: Path) -> dict[str, object]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, Mapping):
        raise ValueError(f"Expected JSON object in {path}")
    return dict(payload)


def _resolve_path(path: Path) -> Path:
    if path.is_absolute():
        return path
    if path.parts and path.parts[0] == "..":
        candidates = (
            PROJECT_ROOT / "scripts" / path,
            Path.cwd() / path,
            PROJECT_ROOT / path,
        )
    else:
        candidates = (
            PROJECT_ROOT / path,
            Path.cwd() / path,
            PROJECT_ROOT / "scripts" / path,
        )
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved.exists() or resolved.parent.exists():
            return resolved
    return candidates[0].resolve()


def _repo_or_home_path(path: Path) -> str:
    resolved = path.resolve()
    for root, prefix in ((PROJECT_ROOT.resolve(), ""), (Path.home().resolve(), "~/")):
        try:
            relative = resolved.relative_to(root)
        except ValueError:
            continue
        return f"{prefix}{relative.as_posix()}" if prefix else relative.as_posix()
    return str(resolved)


def _clean_str(value: object) -> str:
    return str(value or "").strip()


def _normalize_label(value: object) -> str:
    return _clean_str(value).casefold()


def _safe_number(value: object) -> int | float | None:
    if value is None or value == "":
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number.is_integer():
        return int(number)
    return number


def _ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(float(numerator) / float(denominator), 6)


def _string_list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [_clean_str(value)] if _clean_str(value) else []
    if isinstance(value, Sequence):
        return [_clean_str(item) for item in value if _clean_str(item)]
    return [_clean_str(value)] if _clean_str(value) else []


def _as_set(value: object) -> set[str]:
    if isinstance(value, set):
        return {_clean_str(item) for item in value if _clean_str(item)}
    return set(_string_list(value))


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _as_sequence(value: object) -> Sequence[object]:
    return value if isinstance(value, Sequence) and not isinstance(value, str) else []


def _match_mode_sort_key(value: object) -> tuple[int, str]:
    text = _clean_str(value)
    return ({"exact": 0, "alias": 1, "reading": 2}.get(text, 9), text)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


if __name__ == "__main__":
    raise SystemExit(main())
