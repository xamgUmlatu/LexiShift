#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
from typing import Mapping, Sequence
from urllib.request import Request, urlopen


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEST_INPUTS_ROOT = PROJECT_ROOT / "docs" / "test_inputs"
TEST_OUTPUTS_ROOT = PROJECT_ROOT / "docs" / "test_outputs"
DEFAULT_DATA_ROOT = Path.home() / "Library/Application Support/LexiShift/LexiShift"
DEFAULT_REGISTRY_JSON = TEST_INPUTS_ROOT / "srs_topic_source_registry_en_es.json"
DEFAULT_FREQUENCY_DB = DEFAULT_DATA_ROOT / "frequency_packs" / "freq-es-spalex-v1" / "main.sqlite"
DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / "srs_topic_todosloscorpus_overlay_en_es_latest.json"
DEFAULT_MARKDOWN_OUT = TEST_OUTPUTS_ROOT / "srs_topic_todosloscorpus_overlay_en_es_latest.md"
LANGUAGE_PAIR = "en-es"
SOURCE_PROVIDER = "Lingwars/todosloscorpus"
SOURCE_CHANNEL = "cc0_static_topic_list"
OVERLAY_ID = "srs_topic_todosloscorpus_overlay_en_es_v1"
USER_AGENT = "LexiShift topic source builder/0.1"
DEFAULT_EXTRACT_FIELDS = ("name",)
METADATA_KEYS = {
    "author",
    "authors",
    "comment",
    "comments",
    "description",
    "homepage",
    "license",
    "source",
    "sources",
    "url",
    "urls",
}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build an en-es topic overlay from reviewed CC0 static Spanish word lists "
            "in Lingwars/todosloscorpus. Rows are exact-matched to SPALEX."
        )
    )
    parser.add_argument("--registry-json", type=Path, default=DEFAULT_REGISTRY_JSON)
    parser.add_argument("--frequency-db", type=Path, default=DEFAULT_FREQUENCY_DB)
    parser.add_argument(
        "--source-root",
        type=Path,
        help="Optional local root for tests; source_url values may be relative paths.",
    )
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_report(
        registry_json=args.registry_json,
        frequency_db=args.frequency_db,
        source_root=args.source_root,
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
    registry_json: Path = DEFAULT_REGISTRY_JSON,
    frequency_db: Path = DEFAULT_FREQUENCY_DB,
    source_root: Path | None = None,
    generated_at: str | None = None,
) -> dict[str, object]:
    registry = _load_json(registry_json)
    frequency_rows = _load_frequency_rows(frequency_db)
    rows_by_key: dict[tuple[str, str], dict[str, object]] = {}
    source_summaries: list[dict[str, object]] = []
    unmatched_entries: list[dict[str, object]] = []
    filtered_entries: list[dict[str, object]] = []
    skipped_sources: list[dict[str, object]] = []
    fetch_errors: list[dict[str, object]] = []
    duplicate_row_count = 0

    for source in _mapping_rows(registry.get("sources")):
        source_id = str(source.get("id") or "").strip()
        if str(source.get("provider") or "").strip() != SOURCE_PROVIDER:
            skipped_sources.append(_skipped_source(source, reason="provider_not_supported"))
            continue
        if str(source.get("ingest_state") or "").strip() != "direct_runtime":
            skipped_sources.append(_skipped_source(source, reason="not_direct_runtime"))
            continue
        topic = str(source.get("target_family") or "").strip()
        if not source_id or not topic:
            skipped_sources.append(_skipped_source(source, reason="missing_source_id_or_topic"))
            continue
        try:
            payload = _load_source_payload(source, source_root=source_root)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            fetch_errors.append(
                {
                    "source_id": source_id,
                    "source_url": str(source.get("source_url") or ""),
                    "error": str(exc),
                }
            )
            continue
        extracted = _extract_source_entries(
            payload,
            extract_fields=_source_extract_fields(source),
            filters=_as_mapping(source.get("filters")),
        )
        normalized_entries = _dedupe_preserve_order(_normalize_lemma(entry) for entry in extracted)
        excluded_lemmas = set(_source_excluded_lemmas(source))
        matched_count = 0
        unmatched_count = 0
        for lemma in normalized_entries:
            if lemma in excluded_lemmas:
                filtered_entries.append(
                    {
                        "source_id": source_id,
                        "lemma": lemma,
                        "topic": topic,
                        "corpus_rank": frequency_rows.get(lemma, {}).get("source_rank"),
                        "reason": "source_excluded_lemma",
                    }
                )
                continue
            frequency = frequency_rows.get(lemma)
            if frequency is None:
                unmatched_count += 1
                unmatched_entries.append(
                    {
                        "source_id": source_id,
                        "lemma": lemma,
                        "topic": topic,
                        "reason": "lemma_not_in_frequency_corpus",
                    }
                )
                continue
            filter_reason = _corpus_rank_filter_reason(source, frequency)
            if filter_reason:
                filtered_entries.append(
                    {
                        "source_id": source_id,
                        "lemma": lemma,
                        "topic": topic,
                        "corpus_rank": frequency.get("source_rank"),
                        "reason": filter_reason,
                    }
                )
                continue
            matched_count += 1
            row = _overlay_row(
                source=source,
                lemma=lemma,
                frequency=frequency,
                topic=topic,
            )
            key = (str(row["lemma"]), str(row["topic"]))
            existing = rows_by_key.get(key)
            if existing is None:
                rows_by_key[key] = row
                continue
            duplicate_row_count += 1
            rows_by_key[key] = _merge_duplicate_rows(existing, row)
        source_summaries.append(
            {
                "id": source_id,
                "target_family": topic,
                "input_entry_count": len(extracted),
                "normalized_entry_count": len(normalized_entries),
                "matched_count": matched_count,
                "unmatched_count": unmatched_count,
                "membership": _safe_float(source.get("membership"), default=1.0),
                "confidence": _safe_float(source.get("confidence"), default=0.95),
            }
        )

    rows = sorted(
        rows_by_key.values(),
        key=lambda row: (
            str(row.get("topic") or ""),
            _safe_float(row.get("corpus_rank"), default=999999.0),
            str(row.get("lemma") or ""),
        ),
    )
    summary = _summary(
        rows,
        source_summaries=source_summaries,
        unmatched_entries=unmatched_entries,
        filtered_entries=filtered_entries,
        skipped_sources=skipped_sources,
        fetch_errors=fetch_errors,
        duplicate_row_count=duplicate_row_count,
    )
    status = "ok" if rows and not fetch_errors else "review"
    return {
        "schema_version": 1,
        "status": status,
        "decision": (
            "todosloscorpus_static_topic_overlay_ready"
            if status == "ok"
            else "todosloscorpus_static_topic_overlay_needs_review"
        ),
        "generated_at": generated_at or _utc_now(),
        "language_pair": LANGUAGE_PAIR,
        "overlay_id": OVERLAY_ID,
        "overlay_policy": {
            "promotion_state": "reviewed_cc0_static_overlay_candidate_not_default",
            "runtime_policy_change": "none",
            "source_download": "static_json_urls_from_registry",
            "match_policy": "lowercase_exact_lemma_in_frequency_corpus",
            "license_policy": "direct_runtime_rows_only_from_registry_sources_marked_cc0",
        },
        "inputs": {
            "registry_json": _repo_path(registry_json),
            "frequency_db": str(frequency_db),
            "source_root": str(source_root) if source_root else "",
        },
        "source_license": {
            "provider": SOURCE_PROVIDER,
            "declared_license": "CC0",
            "homepage": "https://github.com/Lingwars/todosloscorpus",
        },
        "summary": summary,
        "sources": source_summaries,
        "skipped_sources": skipped_sources[:200],
        "fetch_errors": fetch_errors,
        "filtered_entries": filtered_entries[:300],
        "unmatched_entries": unmatched_entries[:300],
        "rows": rows,
    }


def render_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# en-es Todos Los Corpus Topic Overlay",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Runtime rows: `{summary.get('row_count', 0)}`",
        f"- Unique lemmas: `{summary.get('unique_lemma_count', 0)}`",
        f"- Matched entries: `{summary.get('matched_entry_count', 0)}`",
        f"- Unmatched entries: `{summary.get('unmatched_entry_count', 0)}`",
        f"- Filtered matched entries: `{summary.get('filtered_entry_count', 0)}`",
        f"- Duplicate rows resolved: `{summary.get('duplicate_row_count', 0)}`",
        f"- Skipped sources: `{summary.get('skipped_source_count', 0)}`",
        f"- Fetch errors: `{summary.get('fetch_error_count', 0)}`",
        "",
        "## Runtime Topic Counts",
        "",
        "| Topic | Rows |",
        "| --- | ---: |",
    ]
    for topic, count in sorted(_as_mapping(summary.get("counts_by_topic")).items()):
        lines.append(f"| `{topic}` | {int(count)} |")
    lines.extend(
        [
            "",
            "## Source Counts",
            "",
            "| Source | Topic | Input | Normalized | Matched | Unmatched |",
            "| --- | --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in _mapping_rows(report.get("sources")):
        lines.append(
            f"| `{row.get('id', '')}` | `{row.get('target_family', '')}` | "
            f"{int(row.get('input_entry_count') or 0)} | "
            f"{int(row.get('normalized_entry_count') or 0)} | "
            f"{int(row.get('matched_count') or 0)} | "
            f"{int(row.get('unmatched_count') or 0)} |"
        )
    filtered = _mapping_rows(report.get("filtered_entries"))
    if filtered:
        lines.extend(["", "## Filtered Matched Sample", ""])
        for row in filtered[:50]:
            lines.append(
                f"- `{row.get('lemma', '')}` -> `{row.get('topic', '')}` "
                f"({row.get('source_id', '')}; {row.get('reason', '')}; "
                f"rank={row.get('corpus_rank', '')})"
            )
    unmatched = _mapping_rows(report.get("unmatched_entries"))
    if unmatched:
        lines.extend(["", "## Unmatched Sample", ""])
        for row in unmatched[:50]:
            lines.append(
                f"- `{row.get('lemma', '')}` -> `{row.get('topic', '')}` "
                f"({row.get('source_id', '')})"
            )
    skipped = _mapping_rows(report.get("skipped_sources"))
    if skipped:
        lines.extend(["", "## Skipped Sources", ""])
        for row in skipped[:50]:
            lines.append(
                f"- `{row.get('source_id', '')}`: {row.get('reason', '')} "
                f"-> `{row.get('target_family', '')}`"
            )
    return "\n".join(lines) + "\n"


def _overlay_row(
    *,
    source: Mapping[str, object],
    lemma: str,
    frequency: Mapping[str, object],
    topic: str,
) -> dict[str, object]:
    source_id = str(source.get("id") or "").strip()
    membership = _safe_float(source.get("membership"), default=1.0)
    confidence = _safe_float(source.get("confidence"), default=0.95)
    review_id = _review_id(source_id, lemma, topic)
    return {
        "language_pair": LANGUAGE_PAIR,
        "lemma": lemma,
        "topic": topic,
        "membership": round(membership, 6),
        "confidence_label": "strong" if membership >= 1.0 and confidence >= 0.9 else "light",
        "review_state": "source_license_reviewed_static_list",
        "review_id": review_id,
        "source_channel": SOURCE_CHANNEL,
        "source_label": source_id,
        "facet_id": source_id,
        "evidence_score": round(confidence, 6),
        "corpus_rank": frequency.get("source_rank"),
        "pmw": frequency.get("pmw"),
        "pos": str(frequency.get("pos") or ""),
        "pos_canonical": str(frequency.get("pos_canonical") or ""),
        "provenance": {
            "source_overlay_ids": [OVERLAY_ID],
            "provider": SOURCE_PROVIDER,
            "source_id": source_id,
            "source_url": str(source.get("source_url") or ""),
            "license": str(source.get("license") or ""),
            "license_note": "Source registry marks this static list as CC0.",
            "match_policy": "lowercase_exact_lemma_in_frequency_corpus",
            "notes": str(source.get("notes") or ""),
        },
    }


def _extract_source_entries(
    payload: object,
    *,
    extract_fields: Sequence[str] = DEFAULT_EXTRACT_FIELDS,
    filters: Mapping[str, object],
) -> list[str]:
    entries: list[str] = []
    field_set = {str(field).strip() for field in extract_fields if str(field).strip()}

    def walk(value: object) -> None:
        if isinstance(value, str):
            entries.append(value)
            return
        if isinstance(value, Mapping):
            matched_field = False
            for field in field_set:
                field_value = value.get(field)
                if isinstance(field_value, str):
                    if not _passes_filters(value, filters):
                        return
                    entries.append(field_value)
                    matched_field = True
                elif isinstance(field_value, (Mapping, Sequence)) and not isinstance(
                    field_value, (str, bytes, bytearray)
                ):
                    walk(field_value)
                    matched_field = True
            if matched_field:
                return
            for key, child in value.items():
                if str(key) in METADATA_KEYS:
                    continue
                walk(child)
            return
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            for child in value:
                walk(child)

    walk(payload)
    return [entry for entry in entries if _normalize_lemma(entry)]


def _source_extract_fields(source: Mapping[str, object]) -> tuple[str, ...]:
    fields = _string_list(source.get("extract_fields"))
    if fields:
        return tuple(fields)
    return DEFAULT_EXTRACT_FIELDS


def _source_excluded_lemmas(source: Mapping[str, object]) -> tuple[str, ...]:
    return tuple(_normalize_lemma(lemma) for lemma in _string_list(source.get("exclude_lemmas")))


def _passes_filters(value: Mapping[str, object], filters: Mapping[str, object]) -> bool:
    for key, expected in filters.items():
        if str(value.get(str(key)) or "") != str(expected):
            return False
    return True


def _string_list(value: object) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _corpus_rank_filter_reason(
    source: Mapping[str, object],
    frequency: Mapping[str, object],
) -> str:
    rank = _safe_float(frequency.get("source_rank"), default=0.0)
    min_rank = _safe_float(source.get("min_corpus_rank"), default=0.0)
    if min_rank > 0.0 and rank < min_rank:
        return f"corpus_rank_below_min:{int(min_rank)}"
    max_rank = _safe_float(source.get("max_corpus_rank"), default=0.0)
    if max_rank > 0.0 and rank > max_rank:
        return f"corpus_rank_above_max:{int(max_rank)}"
    return ""


def _normalize_lemma(value: object) -> str:
    lemma = str(value or "").strip().lower()
    if not lemma or lemma.startswith(("http://", "https://")):
        return ""
    return " ".join(lemma.split())


def _dedupe_preserve_order(values: Sequence[str] | object) -> list[str]:
    seen: set[str] = set()
    rows: list[str] = []
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        rows.append(value)
    return rows


def _merge_duplicate_rows(
    left: Mapping[str, object],
    right: Mapping[str, object],
) -> dict[str, object]:
    winner = dict(left if _row_priority(left) >= _row_priority(right) else right)
    provenance = dict(_as_mapping(winner.get("provenance")))
    source_ids: list[str] = []
    for row in (left, right):
        source_id = str(_as_mapping(row.get("provenance")).get("source_id") or "").strip()
        if source_id and source_id not in source_ids:
            source_ids.append(source_id)
    if source_ids:
        provenance["source_ids"] = source_ids
    winner["provenance"] = provenance
    return winner


def _row_priority(row: Mapping[str, object]) -> tuple[float, float, float]:
    return (
        _safe_float(row.get("membership")),
        _safe_float(row.get("evidence_score")),
        -_safe_float(row.get("corpus_rank"), default=999999.0),
    )


def _summary(
    rows: Sequence[Mapping[str, object]],
    *,
    source_summaries: Sequence[Mapping[str, object]],
    unmatched_entries: Sequence[Mapping[str, object]],
    filtered_entries: Sequence[Mapping[str, object]],
    skipped_sources: Sequence[Mapping[str, object]],
    fetch_errors: Sequence[Mapping[str, object]],
    duplicate_row_count: int,
) -> dict[str, object]:
    counts_by_topic = Counter(str(row.get("topic") or "") for row in rows)
    confidence_counts = Counter(str(row.get("confidence_label") or "unknown") for row in rows)
    unique_lemmas = {str(row.get("lemma") or "").strip() for row in rows if row.get("lemma")}
    return {
        "row_count": len(rows),
        "runtime_effective_row_count": len(rows),
        "unique_lemma_count": len(unique_lemmas),
        "topic_count": len(counts_by_topic),
        "runtime_effective_topic_count": len(counts_by_topic),
        "counts_by_topic": dict(sorted(counts_by_topic.items())),
        "runtime_effective_counts_by_topic": dict(sorted(counts_by_topic.items())),
        "counts_by_confidence": dict(sorted(confidence_counts.items())),
        "runtime_effective_counts_by_confidence": dict(sorted(confidence_counts.items())),
        "source_count": len(source_summaries),
        "input_entry_count": sum(
            int(row.get("input_entry_count") or 0) for row in source_summaries
        ),
        "normalized_entry_count": sum(
            int(row.get("normalized_entry_count") or 0) for row in source_summaries
        ),
        "matched_entry_count": sum(int(row.get("matched_count") or 0) for row in source_summaries),
        "unmatched_entry_count": len(unmatched_entries),
        "filtered_entry_count": len(filtered_entries),
        "skipped_source_count": len(skipped_sources),
        "fetch_error_count": len(fetch_errors),
        "duplicate_row_count": duplicate_row_count,
    }


def _load_source_payload(source: Mapping[str, object], *, source_root: Path | None) -> object:
    source_url = str(source.get("source_url") or "").strip()
    if not source_url:
        raise ValueError("source_url is required")
    if source_url.startswith(("http://", "https://")):
        request = Request(source_url, headers={"User-Agent": USER_AGENT})
        with urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    path = Path(source_url)
    if source_root is not None and not path.is_absolute():
        path = Path(source_root).expanduser() / path
    return json.loads(path.expanduser().read_text(encoding="utf-8"))


def _load_frequency_rows(path: Path) -> dict[str, dict[str, object]]:
    db_path = Path(path).expanduser()
    if not db_path.exists():
        raise FileNotFoundError(f"Missing frequency DB: {db_path}")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """
            SELECT lemma, source_rank, pmw, pos, pos_canonical
            FROM frequency
            WHERE lemma IS NOT NULL AND TRIM(lemma) != ''
            """
        ).fetchall()
    finally:
        conn.close()
    return {
        str(row["lemma"]).strip().lower(): {
            "source_rank": _safe_float(row["source_rank"], default=0.0),
            "pmw": _safe_float(row["pmw"], default=0.0),
            "pos": str(row["pos"] or ""),
            "pos_canonical": str(row["pos_canonical"] or ""),
        }
        for row in rows
        if str(row["lemma"]).strip()
    }


def _skipped_source(source: Mapping[str, object], *, reason: str) -> dict[str, object]:
    return {
        "source_id": str(source.get("id") or ""),
        "provider": str(source.get("provider") or ""),
        "target_family": str(source.get("target_family") or ""),
        "ingest_state": str(source.get("ingest_state") or ""),
        "reason": reason,
    }


def _review_id(source_id: str, lemma: str, topic: str) -> str:
    digest = hashlib.sha1(f"{source_id}\\0{lemma}\\0{topic}".encode("utf-8")).hexdigest()[:12]
    return f"srs-enes-tlc-topic-{digest}"


def _load_json(path: Path) -> Mapping[str, object]:
    payload = json.loads(Path(path).expanduser().read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"Expected JSON object at {path}")
    return payload


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _repo_path(path: Path | None) -> str:
    if path is None:
        return ""
    resolved = Path(path).expanduser()
    try:
        return str(resolved.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(resolved)


def _safe_float(value: object, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _mapping_rows(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    return [row for row in value if isinstance(row, Mapping)]


if __name__ == "__main__":
    raise SystemExit(main())
