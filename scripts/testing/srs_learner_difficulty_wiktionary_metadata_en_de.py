#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import gzip
import json
from pathlib import Path
import re
import sqlite3
import sys
import unicodedata
from typing import Iterable, Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / "core"
if str(CORE_ROOT) not in sys.path:
    sys.path.insert(0, str(CORE_ROOT))

from lexishift_core.helper.lp_capabilities import default_frequency_db_path  # noqa: E402
from lexishift_core.helper.paths import build_helper_paths  # noqa: E402


PAIR = "en-de"
DEFAULT_TOP_N = 75000
DEFAULT_SAMPLE_LIMIT = 20
DEFAULT_RAW_RELATIVE_PATH = Path("wiktionary-de-en") / "raw-wiktextract-data-de-en.jsonl.gz"
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_wiktionary_metadata_en_de_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_learner_difficulty_wiktionary_metadata_en_de_latest.md"
)

MARKED_TERMS = frozenset(
    {
        "archaic",
        "colloquial",
        "dated",
        "derogatory",
        "dialectal",
        "formal",
        "informal",
        "literary",
        "obsolete",
        "offensive",
        "rare",
        "regional",
        "slang",
        "uncommon",
        "vulgar",
    }
)
RARE_DATED_TERMS = frozenset({"archaic", "dated", "literary", "obsolete", "rare", "uncommon"})
COLLOQUIAL_TERMS = frozenset({"colloquial", "informal", "slang"})
SENSITIVE_TERMS = frozenset({"derogatory", "offensive", "vulgar"})
REGION_TERMS = frozenset(
    {
        "austrian",
        "austria",
        "bavarian",
        "bavaria",
        "germany",
        "northern",
        "swiss",
        "switzerland",
        "southern",
    }
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Extract German Wiktionary/Kaikki lexical metadata for en-de learner-difficulty "
            "experiments. This is a sidecar signal source; it does not change production "
            "ranking or runtime behavior."
        )
    )
    parser.add_argument("--frequency-db", type=Path)
    parser.add_argument("--raw-jsonl-gz", type=Path)
    parser.add_argument("--top-n", type=int, default=DEFAULT_TOP_N)
    parser.add_argument("--sample-limit", type=int, default=DEFAULT_SAMPLE_LIMIT)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument(
        "--max-raw-rows",
        type=int,
        default=0,
        help="Optional cap for smoke runs. Zero scans the full raw file.",
    )
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_report(
        frequency_db=args.frequency_db,
        raw_jsonl_gz=args.raw_jsonl_gz,
        top_n=max(1, int(args.top_n)),
        sample_limit=max(1, int(args.sample_limit)),
        max_raw_rows=max(0, int(args.max_raw_rows)),
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.markdown_out.write_text(render_markdown(report), encoding="utf-8")
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    if args.fail_on_review and report["status"] != "ok":
        return 1
    return 0


def build_report(
    *,
    frequency_db: Path | None = None,
    raw_jsonl_gz: Path | None = None,
    top_n: int = DEFAULT_TOP_N,
    sample_limit: int = DEFAULT_SAMPLE_LIMIT,
    generated_at: str | None = None,
    raw_entries: Sequence[Mapping[str, object]] | None = None,
    max_raw_rows: int = 0,
) -> dict[str, object]:
    paths = build_helper_paths()
    resolved_frequency_db = frequency_db or default_frequency_db_path(
        PAIR,
        frequency_packs_dir=paths.frequency_packs_dir,
    )
    resolved_raw = raw_jsonl_gz or paths.language_packs_dir / DEFAULT_RAW_RELATIVE_PATH
    candidate_rows = _load_frequency_rows(resolved_frequency_db, top_n=top_n)
    candidate_keys = {
        _normalize_key(row.get("lemma")): str(row.get("lemma") or "").strip()
        for row in candidate_rows
        if _normalize_key(row.get("lemma"))
    }

    if raw_entries is not None:
        extraction = _extract_metadata(raw_entries, candidate_keys=candidate_keys)
        raw_status = "provided"
    elif Path(resolved_raw).expanduser().is_file():
        extraction = _extract_metadata(
            _iter_raw_rows(Path(resolved_raw).expanduser(), max_rows=max_raw_rows),
            candidate_keys=candidate_keys,
        )
        raw_status = "read_file"
    else:
        extraction = {
            "raw_rows_seen": 0,
            "german_entry_rows_seen": 0,
            "matched_entry_rows_seen": 0,
            "by_lemma": {},
        }
        raw_status = "missing"

    by_lemma = _as_mapping(extraction.get("by_lemma"))
    summary = _summary(candidate_rows, by_lemma, extraction)
    findings = _build_findings(candidate_rows, by_lemma, raw_status)
    status = "ok" if not any(row["level"] == "FAIL" for row in findings) else "review"
    report: dict[str, object] = {
        "schema_version": 1,
        "pair": PAIR,
        "status": status,
        "decision": (
            "en_de_wiktionary_metadata_ready"
            if status == "ok"
            else "en_de_wiktionary_metadata_needs_review"
        ),
        "generated_at": generated_at or _utc_now(),
        "runtime_behavior_changed": False,
        "production_ranking_changed": False,
        "inputs": {
            "frequency_db": str(resolved_frequency_db) if resolved_frequency_db else None,
            "raw_jsonl_gz": str(resolved_raw) if resolved_raw else None,
            "raw_status": raw_status,
            "top_n": int(top_n),
            "sample_limit": int(sample_limit),
            "max_raw_rows": int(max_raw_rows),
        },
        "methodology": {
            "purpose": (
                "Expose mechanical German Wiktionary metadata for formula guards: "
                "marked usage, form/variant relations, entry/sense counts, regions, "
                "topics, forms, sounds, synonyms, and etymology presence."
            ),
            "source_policy": (
                "Uses the existing local Kaikki/Wiktionary raw dump. The source is "
                "Wiktionary-derived and already tracked in third-party data notices."
            ),
            "non_goals": [
                "Does not infer semantic topics from gloss text.",
                "Does not treat Wiktionary presence as learner-level evidence.",
                "Does not alter production ranking or runtime scoring.",
            ],
        },
        "summary": summary,
        "samples": _samples(by_lemma, sample_limit=sample_limit),
        "wiktionary_metadata_by_lemma": by_lemma,
        "findings": findings,
        "limitations": [
            "Wiktionary tags/categories are useful guard evidence but can be noisy.",
            "Exact lemma matching is used; inflected forms are not back-projected to lemmas here.",
            "This sidecar is intended for bounded formula experiments, not direct product policy.",
        ],
    }
    return report


def render_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# en-de Wiktionary Metadata Audit",
        "",
        f"- Status: `{report.get('status')}`",
        f"- Decision: `{report.get('decision')}`",
        f"- Generated: `{report.get('generated_at')}`",
        f"- Runtime behavior changed: `{report.get('runtime_behavior_changed')}`",
        f"- Production ranking changed: `{report.get('production_ranking_changed')}`",
        "",
        "## Coverage",
        "",
        f"- Candidate rows: `{summary.get('candidate_count', 0)}`",
        f"- Metadata-covered lemmas: `{summary.get('metadata_coverage_count', 0)}`",
        f"- Metadata coverage ratio: `{_pct(summary.get('metadata_coverage_ratio'))}`",
        f"- Raw rows seen: `{summary.get('raw_rows_seen', 0)}`",
        f"- German entry rows seen: `{summary.get('german_entry_rows_seen', 0)}`",
        f"- Matched entry rows seen: `{summary.get('matched_entry_rows_seen', 0)}`",
        "",
        "## Signal Counts",
        "",
        f"- Marked usage lemmas: `{summary.get('marked_usage_count', 0)}`",
        f"- Rare/dated/literary lemmas: `{summary.get('rare_dated_count', 0)}`",
        f"- Colloquial/slang lemmas: `{summary.get('colloquial_count', 0)}`",
        f"- Sensitive-register lemmas: `{summary.get('sensitive_count', 0)}`",
        f"- Region-marked lemmas: `{summary.get('region_count', 0)}`",
        f"- Form/alt-of lemmas: `{summary.get('form_or_alt_of_count', 0)}`",
        f"- Multi-sense lemmas: `{summary.get('multi_sense_count', 0)}`",
        "",
    ]
    for title, key in (
        ("Marked Usage Samples", "marked_usage"),
        ("Form/Alt-of Samples", "form_or_alt_of"),
        ("High-Sense Samples", "high_sense"),
        ("Coverage Samples", "coverage"),
    ):
        rows = _as_sequence(_as_mapping(report.get("samples")).get(key))
        if not rows:
            continue
        lines.extend(
            [
                f"## {title}",
                "",
                "| Lemma | Entries | Senses | POS | Marked | Region | Form/Alt | Topics |",
                "| --- | ---: | ---: | --- | --- | --- | ---: | --- |",
            ]
        )
        for raw in rows:
            row = _as_mapping(raw)
            lines.append(
                f"| `{row.get('lemma')}` | {row.get('entry_count', 0)} | "
                f"{row.get('sense_count', 0)} | "
                f"{', '.join(str(item) for item in _as_sequence(row.get('pos_values'))[:4])} | "
                f"{', '.join(str(item) for item in _as_sequence(row.get('marked_terms'))[:4]) or '-'} | "
                f"{', '.join(str(item) for item in _as_sequence(row.get('region_terms'))[:4]) or '-'} | "
                f"{int(row.get('form_of_count') or 0) + int(row.get('alt_of_count') or 0)} | "
                f"{', '.join(str(item) for item in _as_sequence(row.get('topics_sample'))[:4]) or '-'} |"
            )
        lines.append("")
    lines.extend(["## Findings", "", "| Level | Code | Message |", "| --- | --- | --- |"])
    for raw in _as_sequence(report.get("findings")):
        row = _as_mapping(raw)
        lines.append(f"| {row.get('level')} | `{row.get('code')}` | {row.get('message')} |")
    lines.append("")
    return "\n".join(lines)


def _extract_metadata(
    rows: Iterable[Mapping[str, object]],
    *,
    candidate_keys: Mapping[str, str],
) -> dict[str, object]:
    accumulator: dict[str, dict[str, object]] = {}
    raw_rows_seen = 0
    german_entry_rows_seen = 0
    matched_entry_rows_seen = 0
    for row in rows:
        raw_rows_seen += 1
        if str(row.get("lang_code") or "").strip().lower() != "de":
            continue
        german_entry_rows_seen += 1
        key = _normalize_key(row.get("word"))
        lemma = candidate_keys.get(key)
        if not lemma:
            continue
        matched_entry_rows_seen += 1
        meta = accumulator.setdefault(key, _empty_meta(lemma))
        _accumulate_entry(meta, row)
    by_lemma = {
        str(meta["lemma"]): _finalize_meta(meta)
        for _, meta in sorted(accumulator.items(), key=lambda item: str(item[1]["lemma"]).lower())
    }
    return {
        "raw_rows_seen": raw_rows_seen,
        "german_entry_rows_seen": german_entry_rows_seen,
        "matched_entry_rows_seen": matched_entry_rows_seen,
        "by_lemma": by_lemma,
    }


def _empty_meta(lemma: str) -> dict[str, object]:
    return {
        "lemma": lemma,
        "entry_count": 0,
        "sense_count": 0,
        "gloss_count": 0,
        "pos_values": set(),
        "tags": set(),
        "categories": set(),
        "topics": set(),
        "marked_terms": set(),
        "rare_dated_terms": set(),
        "colloquial_terms": set(),
        "sensitive_terms": set(),
        "region_terms": set(),
        "form_of_count": 0,
        "alt_of_count": 0,
        "forms_count": 0,
        "sounds_count": 0,
        "synonyms_count": 0,
        "derived_count": 0,
        "related_count": 0,
        "has_etymology": False,
    }


def _accumulate_entry(meta: dict[str, object], row: Mapping[str, object]) -> None:
    meta["entry_count"] = int(meta["entry_count"]) + 1
    pos = str(row.get("pos") or "").strip()
    if pos:
        _as_set(meta["pos_values"]).add(pos)
    entry_features = set(_strings_from(row.get("tags"))) | set(_strings_from(row.get("categories")))
    _accumulate_features(meta, entry_features)
    meta["forms_count"] = int(meta["forms_count"]) + len(_as_sequence(row.get("forms")))
    meta["sounds_count"] = int(meta["sounds_count"]) + len(_as_sequence(row.get("sounds")))
    meta["synonyms_count"] = int(meta["synonyms_count"]) + len(_as_sequence(row.get("synonyms")))
    meta["derived_count"] = int(meta["derived_count"]) + len(_as_sequence(row.get("derived")))
    meta["related_count"] = int(meta["related_count"]) + len(_as_sequence(row.get("related")))
    meta["has_etymology"] = bool(meta["has_etymology"]) or bool(
        str(row.get("etymology_text") or "").strip()
    )
    for sense in _mapping_rows(row.get("senses")):
        meta["sense_count"] = int(meta["sense_count"]) + 1
        glosses = _as_sequence(sense.get("glosses")) or _as_sequence(sense.get("raw_glosses"))
        meta["gloss_count"] = int(meta["gloss_count"]) + len(glosses)
        _as_set(meta["topics"]).update(_strings_from(sense.get("topics")))
        sense_features = (
            set(_strings_from(sense.get("tags")))
            | set(_strings_from(sense.get("raw_tags")))
            | set(_strings_from(sense.get("categories")))
        )
        _accumulate_features(meta, sense_features)
        meta["form_of_count"] = int(meta["form_of_count"]) + len(_as_sequence(sense.get("form_of")))
        meta["alt_of_count"] = int(meta["alt_of_count"]) + len(_as_sequence(sense.get("alt_of")))


def _accumulate_features(meta: dict[str, object], features: Iterable[str]) -> None:
    for feature in features:
        normalized = _normalize_feature(feature)
        if not normalized:
            continue
        if "category" in normalized or "terms" in normalized or normalized.startswith("german-"):
            _as_set(meta["categories"]).add(feature)
        else:
            _as_set(meta["tags"]).add(feature)
        markers = _marker_hits(normalized, MARKED_TERMS)
        _as_set(meta["marked_terms"]).update(markers)
        _as_set(meta["rare_dated_terms"]).update(markers & RARE_DATED_TERMS)
        _as_set(meta["colloquial_terms"]).update(markers & COLLOQUIAL_TERMS)
        _as_set(meta["sensitive_terms"]).update(markers & SENSITIVE_TERMS)
        _as_set(meta["region_terms"]).update(_marker_hits(normalized, REGION_TERMS))


def _finalize_meta(meta: Mapping[str, object]) -> dict[str, object]:
    pos_values = sorted(str(item) for item in _as_set(meta.get("pos_values")))
    tags = sorted(str(item) for item in _as_set(meta.get("tags")))
    categories = sorted(str(item) for item in _as_set(meta.get("categories")))
    topics = sorted(str(item) for item in _as_set(meta.get("topics")))
    marked_terms = sorted(str(item) for item in _as_set(meta.get("marked_terms")))
    rare_dated_terms = sorted(str(item) for item in _as_set(meta.get("rare_dated_terms")))
    colloquial_terms = sorted(str(item) for item in _as_set(meta.get("colloquial_terms")))
    sensitive_terms = sorted(str(item) for item in _as_set(meta.get("sensitive_terms")))
    region_terms = sorted(str(item) for item in _as_set(meta.get("region_terms")))
    return {
        "lemma": meta.get("lemma"),
        "entry_count": int(meta.get("entry_count") or 0),
        "sense_count": int(meta.get("sense_count") or 0),
        "gloss_count": int(meta.get("gloss_count") or 0),
        "pos_values": pos_values,
        "pos_count": len(pos_values),
        "tags_sample": tags[:12],
        "tag_count": len(tags),
        "categories_sample": categories[:12],
        "category_count": len(categories),
        "topics_sample": topics[:12],
        "topic_count": len(topics),
        "marked_usage_flag": bool(marked_terms),
        "marked_terms": marked_terms,
        "rare_dated_flag": bool(rare_dated_terms),
        "rare_dated_terms": rare_dated_terms,
        "colloquial_flag": bool(colloquial_terms),
        "colloquial_terms": colloquial_terms,
        "sensitive_flag": bool(sensitive_terms),
        "sensitive_terms": sensitive_terms,
        "region_terms": region_terms,
        "region_tag_count": len(region_terms),
        "form_of_count": int(meta.get("form_of_count") or 0),
        "alt_of_count": int(meta.get("alt_of_count") or 0),
        "forms_count": int(meta.get("forms_count") or 0),
        "sounds_count": int(meta.get("sounds_count") or 0),
        "synonyms_count": int(meta.get("synonyms_count") or 0),
        "derived_count": int(meta.get("derived_count") or 0),
        "related_count": int(meta.get("related_count") or 0),
        "has_etymology": bool(meta.get("has_etymology")),
    }


def _summary(
    candidate_rows: Sequence[Mapping[str, object]],
    by_lemma: Mapping[str, object],
    extraction: Mapping[str, object],
) -> dict[str, object]:
    metas = [_as_mapping(meta) for meta in by_lemma.values()]
    return {
        "candidate_count": len(candidate_rows),
        "metadata_coverage_count": len(metas),
        "metadata_coverage_ratio": _ratio(len(metas), len(candidate_rows)),
        "raw_rows_seen": int(extraction.get("raw_rows_seen") or 0),
        "german_entry_rows_seen": int(extraction.get("german_entry_rows_seen") or 0),
        "matched_entry_rows_seen": int(extraction.get("matched_entry_rows_seen") or 0),
        "marked_usage_count": sum(1 for meta in metas if meta.get("marked_usage_flag")),
        "rare_dated_count": sum(1 for meta in metas if meta.get("rare_dated_flag")),
        "colloquial_count": sum(1 for meta in metas if meta.get("colloquial_flag")),
        "sensitive_count": sum(1 for meta in metas if meta.get("sensitive_flag")),
        "region_count": sum(1 for meta in metas if int(meta.get("region_tag_count") or 0) > 0),
        "form_or_alt_of_count": sum(
            1
            for meta in metas
            if int(meta.get("form_of_count") or 0) + int(meta.get("alt_of_count") or 0) > 0
        ),
        "multi_sense_count": sum(1 for meta in metas if int(meta.get("sense_count") or 0) > 1),
        "pos_counts": dict(
            Counter(
                pos for meta in metas for pos in _as_sequence(meta.get("pos_values"))
            ).most_common()
        ),
        "marked_term_counts": dict(
            Counter(
                term for meta in metas for term in _as_sequence(meta.get("marked_terms"))
            ).most_common()
        ),
    }


def _samples(
    by_lemma: Mapping[str, object],
    *,
    sample_limit: int,
) -> dict[str, object]:
    metas = [_as_mapping(meta) for meta in by_lemma.values()]
    return {
        "coverage": metas[:sample_limit],
        "marked_usage": [meta for meta in metas if meta.get("marked_usage_flag")][:sample_limit],
        "form_or_alt_of": [
            meta
            for meta in metas
            if int(meta.get("form_of_count") or 0) + int(meta.get("alt_of_count") or 0) > 0
        ][:sample_limit],
        "high_sense": sorted(
            metas,
            key=lambda meta: (
                -int(meta.get("sense_count") or 0),
                str(meta.get("lemma") or "").lower(),
            ),
        )[:sample_limit],
    }


def _build_findings(
    candidate_rows: Sequence[Mapping[str, object]],
    by_lemma: Mapping[str, object],
    raw_status: str,
) -> list[dict[str, object]]:
    return [
        _finding(
            "PASS" if candidate_rows else "FAIL",
            "frequency_rows_available",
            f"Loaded {len(candidate_rows)} en-de frequency rows.",
        ),
        _finding(
            "PASS" if raw_status in {"read_file", "provided"} else "WARN",
            "wiktionary_raw_available",
            f"Wiktionary raw status: {raw_status}.",
        ),
        _finding(
            "PASS" if by_lemma else "WARN",
            "wiktionary_metadata_available",
            f"Extracted metadata for {len(by_lemma)} candidate lemmas.",
        ),
    ]


def _iter_raw_rows(path: Path, *, max_rows: int = 0) -> Iterable[Mapping[str, object]]:
    seen = 0
    with gzip.open(path, "rt", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if max_rows and seen >= max_rows:
                break
            seen += 1
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, Mapping):
                yield payload


def _load_frequency_rows(path: Path | None, *, top_n: int) -> list[dict[str, object]]:
    if path is None or not Path(path).expanduser().exists():
        return []
    conn = sqlite3.connect(Path(path).expanduser())
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """
            SELECT lemma, core_rank, pmw, pos
            FROM frequency
            WHERE lemma IS NOT NULL AND TRIM(lemma) != ''
            ORDER BY COALESCE(core_rank, 999999999), lemma
            LIMIT ?
            """,
            (int(top_n),),
        ).fetchall()
    finally:
        conn.close()
    return [
        {
            "lemma": str(row["lemma"]).strip(),
            "core_rank": _safe_float(row["core_rank"]),
            "pmw": _safe_float(row["pmw"]),
            "pos": str(row["pos"] or ""),
        }
        for row in rows
        if str(row["lemma"]).strip()
    ]


def _marker_hits(normalized: str, markers: frozenset[str]) -> set[str]:
    pieces = set(re.split(r"[-\s_]+", normalized))
    hits = {marker for marker in markers if marker in pieces or normalized == marker}
    for marker in markers:
        if f"-{marker}-" in f"-{normalized}-":
            hits.add(marker)
    return hits


def _strings_from(value: object) -> tuple[str, ...]:
    strings: list[str] = []
    for item in _as_sequence(value):
        if isinstance(item, str):
            strings.append(item)
        elif isinstance(item, Mapping):
            for key in ("word", "name", "tag", "category", "topic", "english", "sense"):
                raw = str(item.get(key) or "").strip()
                if raw:
                    strings.append(raw)
                    break
    return tuple(strings)


def _normalize_key(value: object) -> str:
    text = unicodedata.normalize("NFC", str(value or ""))
    text = text.strip().lower()
    text = re.sub(r"\s+", " ", text)
    return text


def _normalize_feature(value: object) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"[_\s]+", "-", text)
    text = re.sub(r"[^a-zäöüß-]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


def _mapping_rows(value: object) -> list[Mapping[str, object]]:
    return [row for row in _as_sequence(value) if isinstance(row, Mapping)]


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _as_sequence(value: object) -> Sequence[object]:
    return value if isinstance(value, Sequence) and not isinstance(value, (str, bytes)) else ()


def _as_set(value: object) -> set[object]:
    return value if isinstance(value, set) else set()


def _safe_float(value: object) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _ratio(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 6) if denominator else 0.0


def _pct(value: object) -> str:
    numeric = _safe_float(value)
    return "" if numeric is None else f"{numeric * 100:.1f}%"


def _finding(level: str, code: str, message: str) -> dict[str, object]:
    return {"level": level, "code": code, "message": message}


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


if __name__ == "__main__":
    raise SystemExit(main())
