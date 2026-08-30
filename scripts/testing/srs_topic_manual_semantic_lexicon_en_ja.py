#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = PROJECT_ROOT / "scripts" / "testing"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from srs_topic_autotag_evidence_en_ja import (  # noqa: E402
    DEFAULT_CANDIDATES_CSV,
    _as_mapping,
    _coalesce_float,
    _evidence_row,
    _load_candidates,
    _mapping_rows,
    _normalize_ja_reading,
    _safe_float,
    _select_sample_rows,
    _source_summary,
    _string_list,
)


TEST_INPUTS_ROOT = PROJECT_ROOT / "docs" / "test_inputs"
TEST_OUTPUTS_ROOT = PROJECT_ROOT / "docs" / "test_outputs"
DEFAULT_LEXICON_JSON = TEST_INPUTS_ROOT / "srs_topic_manual_semantic_lexicon_en_ja.json"
DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / "srs_topic_manual_semantic_lexicon_en_ja_latest.json"
DEFAULT_MARKDOWN_OUT = TEST_OUTPUTS_ROOT / "srs_topic_manual_semantic_lexicon_en_ja_latest.md"
LANGUAGE_PAIR = "en-ja"
SOURCE_ID = "manual_semantic_lexicon"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Match product-owned en-ja semantic lists against corrected SRS "
            "candidates. This is a deterministic sidecar source for obvious "
            "closed-set topics and internal semantic facets."
        )
    )
    parser.add_argument("--candidates-csv", type=Path, default=DEFAULT_CANDIDATES_CSV)
    parser.add_argument("--lexicon-json", type=Path, default=DEFAULT_LEXICON_JSON)
    parser.add_argument("--top-n", type=int, default=73752)
    parser.add_argument("--sample-per-cell", type=int, default=4)
    parser.add_argument("--max-sample-rows", type=int, default=240)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--fail-on-missing", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_report(
        candidates_csv=_resolve_path(args.candidates_csv),
        lexicon_json=_resolve_path(args.lexicon_json),
        top_n=max(0, int(args.top_n)),
        sample_per_cell=max(0, int(args.sample_per_cell)),
        max_sample_rows=max(0, int(args.max_sample_rows)),
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
    if args.fail_on_missing and report["status"] != "ok":
        return 1
    return 0


def build_report(
    *,
    candidates_csv: Path = DEFAULT_CANDIDATES_CSV,
    lexicon_json: Path = DEFAULT_LEXICON_JSON,
    top_n: int = 73752,
    sample_per_cell: int = 4,
    max_sample_rows: int = 240,
    generated_at: str | None = None,
) -> dict[str, object]:
    generated_at = generated_at or _utc_now()
    lexicon = _load_json(lexicon_json)
    candidates = _load_candidates(candidates_csv, top_n=top_n)
    candidate_index = _candidate_index(candidates)
    evidence_rows: list[dict[str, object]] = []
    facet_rows: list[dict[str, object]] = []
    collection_reports: list[dict[str, object]] = []
    unmatched_rows: list[dict[str, object]] = []

    for collection in _mapping_rows(lexicon.get("collections")):
        collection_report = _process_collection(
            collection,
            candidate_index=candidate_index,
            evidence_rows=evidence_rows,
            facet_rows=facet_rows,
            unmatched_rows=unmatched_rows,
        )
        collection_reports.append(collection_report)

    evidence_rows = _dedupe_topic_rows(evidence_rows)
    facet_rows = _dedupe_facet_rows(facet_rows)
    review_sample = _select_sample_rows(
        evidence_rows,
        sample_per_cell=sample_per_cell,
        max_rows=max_sample_rows,
        max_rows_per_source=0,
    )
    facet_sample = facet_rows[:max_sample_rows]
    finding_level = "WARN" if unmatched_rows else "PASS"
    findings = [
        _finding(
            "PASS",
            "manual_semantic_lexicon_loaded",
            f"Loaded {len(_mapping_rows(lexicon.get('collections')))} semantic collection(s).",
        ),
        _finding(
            finding_level,
            "manual_semantic_unmatched_entries"
            if unmatched_rows
            else "manual_semantic_all_entries_resolved",
            f"{len(unmatched_rows)} lexicon entrie(s) were missing or ambiguous.",
        ),
    ]
    return {
        "schema_version": 1,
        "status": "review" if unmatched_rows else "ok",
        "decision": (
            "manual_semantic_lexicon_needs_entry_review"
            if unmatched_rows
            else "manual_semantic_lexicon_evidence_ready"
        ),
        "generated_at": generated_at,
        "language_pair": LANGUAGE_PAIR,
        "inputs": {
            "candidates_csv": _repo_path(candidates_csv),
            "lexicon_json": _repo_path(lexicon_json),
            "top_n": top_n,
        },
        "method": {
            "source": SOURCE_ID,
            "match_policy": (
                "Entries with readings require exact normalized reading; entries "
                "without readings resolve only when the lemma has one corrected candidate row."
            ),
            "promotion_state": "topic evidence rows can be product-safe only when the collection is marked promotion_eligible",
            "facet_policy": "facet rows are emitted for internal review and are not runtime topic overlay rows",
        },
        "summary": {
            "collection_count": len(collection_reports),
            "declared_entry_count": sum(
                int(row.get("declared_entry_count") or 0) for row in collection_reports
            ),
            "matched_entry_count": sum(
                int(row.get("matched_entry_count") or 0) for row in collection_reports
            ),
            "unmatched_entry_count": len(unmatched_rows),
            "topic_evidence_row_count": len(evidence_rows),
            "facet_row_count": len(facet_rows),
            "counts_by_topic": dict(
                sorted(Counter(str(row.get("topic") or "") for row in evidence_rows).items())
            ),
            "counts_by_facet": dict(
                sorted(Counter(str(row.get("facet_id") or "") for row in facet_rows).items())
            ),
        },
        "collection_reports": collection_reports,
        "source_summary": _source_summary(evidence_rows),
        "topic_summary": _topic_summary(evidence_rows),
        "facet_summary": _facet_summary(facet_rows),
        "evidence_rows": evidence_rows,
        "facet_rows": facet_rows,
        "review_sample": review_sample,
        "facet_sample": facet_sample,
        "unmatched_entries": unmatched_rows,
        "findings": findings,
        "limitations": [
            "This is a product-owned seed lexicon, not an exhaustive ontology.",
            "Facet rows intentionally do not imply user-facing topic preference support.",
            "Entries without readings are accepted only for unique candidate lemmas.",
        ],
    }


def _process_collection(
    collection: Mapping[str, object],
    *,
    candidate_index: Mapping[str, Sequence[Mapping[str, object]]],
    evidence_rows: list[dict[str, object]],
    facet_rows: list[dict[str, object]],
    unmatched_rows: list[dict[str, object]],
) -> dict[str, object]:
    collection_id = str(collection.get("id") or "").strip()
    target_family = str(collection.get("target_family") or "").strip()
    facet_id = str(collection.get("facet_id") or "").strip()
    entries = _collection_entries(collection)
    matched_count = 0
    missing_count = 0
    ambiguous_count = 0
    for raw_entry in entries:
        entry = _normalize_entry(raw_entry)
        resolved = _resolve_entry(entry, candidate_index=candidate_index)
        if not resolved:
            missing_count += 1
            unmatched_rows.append(_unmatched_row(collection_id, entry, reason="candidate_missing"))
            continue
        if len(resolved) > 1:
            ambiguous_count += 1
            unmatched_rows.append(
                _unmatched_row(
                    collection_id,
                    entry,
                    reason="candidate_ambiguous",
                    candidates=resolved,
                )
            )
            continue
        candidate = dict(resolved[0])
        matched_entry = {**entry, "match_mode": str(candidate.get("match_mode") or "")}
        matched_count += 1
        if target_family:
            evidence_rows.append(
                _topic_evidence_row(collection, entry=matched_entry, candidate=candidate)
            )
        if facet_id:
            facet_rows.append(_facet_row(collection, entry=matched_entry, candidate=candidate))
    return {
        "id": collection_id,
        "display_name": str(collection.get("display_name") or collection_id),
        "target_family": target_family,
        "facet_id": facet_id,
        "promotion_eligible": bool(collection.get("promotion_eligible")),
        "declared_entry_count": len(entries),
        "matched_entry_count": matched_count,
        "missing_entry_count": missing_count,
        "ambiguous_entry_count": ambiguous_count,
    }


def _topic_evidence_row(
    collection: Mapping[str, object],
    *,
    entry: Mapping[str, object],
    candidate: Mapping[str, object],
) -> dict[str, object]:
    collection_id = str(collection.get("id") or "")
    target_family = str(collection.get("target_family") or "")
    return _evidence_row(
        candidate=candidate,
        source=SOURCE_ID,
        topic=target_family,
        membership=_coalesce_float(collection.get("membership"), 1.0),
        confidence=_coalesce_float(collection.get("confidence"), 0.98),
        source_label=collection_id,
        evidence_label=f"Manual semantic lexicon: {collection_id}",
        sense={"match_mode": str(entry.get("match_mode") or "manual_semantic_unique_lemma")},
        review_posture=str(collection.get("review_posture") or "product_owned_closed_set"),
        license_note=str(
            collection.get("license_note") or "Product-owned manually curated semantic list."
        ),
        extra={
            "manual_semantic_collection_id": collection_id,
            "manual_semantic_display_name": str(collection.get("display_name") or collection_id),
            "manual_semantic_output_kind": "topic",
            "manual_semantic_promotion_eligible": bool(collection.get("promotion_eligible")),
            "manual_semantic_entry_note": str(entry.get("note") or ""),
            "manual_semantic_source_note": str(collection.get("source_note") or ""),
        },
    )


def _facet_row(
    collection: Mapping[str, object],
    *,
    entry: Mapping[str, object],
    candidate: Mapping[str, object],
) -> dict[str, object]:
    collection_id = str(collection.get("id") or "")
    facet_id = str(collection.get("facet_id") or "")
    return {
        "lemma": str(candidate.get("lemma") or ""),
        "reading": str(candidate.get("reading") or ""),
        "language_pair": LANGUAGE_PAIR,
        "facet_id": facet_id,
        "facet_value": collection_id,
        "facet_label": str(collection.get("display_name") or collection_id),
        "membership": round(_coalesce_float(collection.get("membership"), 1.0), 6),
        "confidence": round(_coalesce_float(collection.get("confidence"), 0.98), 6),
        "source": SOURCE_ID,
        "source_label": collection_id,
        "rank": candidate.get("rank"),
        "core_rank": candidate.get("core_rank"),
        "score": candidate.get("score"),
        "band": str(candidate.get("band") or ""),
        "candidate_state": str(candidate.get("candidate_state") or ""),
        "topic_stretch_allowed": str(candidate.get("topic_stretch_allowed") or ""),
        "match_mode": str(entry.get("match_mode") or "manual_semantic_unique_lemma"),
        "extra": {
            "manual_semantic_collection_id": collection_id,
            "manual_semantic_entry_note": str(entry.get("note") or ""),
        },
    }


def _resolve_entry(
    entry: Mapping[str, object],
    *,
    candidate_index: Mapping[str, Sequence[Mapping[str, object]]],
) -> list[Mapping[str, object]]:
    lemma = str(entry.get("lemma") or "").strip()
    reading = str(entry.get("reading") or "").strip()
    if not lemma:
        return []
    candidates = list(candidate_index.get(lemma, ()))
    if reading:
        normalized_reading = _normalize_ja_reading(reading)
        matches = [
            candidate
            for candidate in candidates
            if str(candidate.get("normalized_reading") or "") == normalized_reading
        ]
        for candidate in matches:
            candidate["match_mode"] = "manual_semantic_exact_reading"
        return matches
    if len(candidates) == 1:
        candidates[0]["match_mode"] = "manual_semantic_unique_lemma"
        return candidates
    return candidates


def _candidate_index(
    candidates: Sequence[Mapping[str, object]],
) -> dict[str, list[dict[str, object]]]:
    by_lemma: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in candidates:
        lemma = str(row.get("lemma") or "").strip()
        if lemma:
            by_lemma[lemma].append(dict(row))
    return dict(by_lemma)


def _collection_entries(collection: Mapping[str, object]) -> list[object]:
    entries = collection.get("entries")
    if isinstance(entries, Sequence) and not isinstance(entries, (str, bytes, bytearray)):
        return list(entries)
    return []


def _normalize_entry(value: object) -> dict[str, object]:
    if isinstance(value, str):
        return {"lemma": value}
    entry = dict(_as_mapping(value))
    return {
        "lemma": str(entry.get("lemma") or "").strip(),
        "reading": str(entry.get("reading") or "").strip(),
        "note": str(entry.get("note") or "").strip(),
    }


def _unmatched_row(
    collection_id: str,
    entry: Mapping[str, object],
    *,
    reason: str,
    candidates: Sequence[Mapping[str, object]] = (),
) -> dict[str, object]:
    return {
        "collection_id": collection_id,
        "lemma": str(entry.get("lemma") or ""),
        "reading": str(entry.get("reading") or ""),
        "reason": reason,
        "candidate_readings": [
            str(candidate.get("reading") or "")
            for candidate in candidates
            if str(candidate.get("reading") or "")
        ][:12],
    }


def _dedupe_topic_rows(rows: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    by_key: dict[tuple[str, str, str, str], dict[str, object]] = {}
    for row in rows:
        key = (
            str(row.get("lemma") or ""),
            str(row.get("reading") or ""),
            str(row.get("topic") or ""),
            str(row.get("source_label") or ""),
        )
        if all(key):
            by_key.setdefault(key, dict(row))
    return sorted(
        by_key.values(),
        key=lambda row: (
            str(row.get("topic") or ""),
            _safe_float(row.get("score")),
            str(row.get("lemma") or ""),
        ),
    )


def _dedupe_facet_rows(rows: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    by_key: dict[tuple[str, str, str, str], dict[str, object]] = {}
    for row in rows:
        key = (
            str(row.get("lemma") or ""),
            str(row.get("reading") or ""),
            str(row.get("facet_id") or ""),
            str(row.get("facet_value") or ""),
        )
        if all(key):
            by_key.setdefault(key, dict(row))
    return sorted(
        by_key.values(),
        key=lambda row: (
            str(row.get("facet_id") or ""),
            _safe_float(row.get("score")),
            str(row.get("lemma") or ""),
        ),
    )


def _topic_summary(rows: Sequence[Mapping[str, object]]) -> dict[str, dict[str, object]]:
    grouped: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("topic") or "")].append(row)
    return {
        topic: {
            "row_count": len(topic_rows),
            "lemma_count": len({str(row.get("lemma") or "") for row in topic_rows}),
        }
        for topic, topic_rows in sorted(grouped.items())
    }


def _facet_summary(rows: Sequence[Mapping[str, object]]) -> dict[str, dict[str, object]]:
    grouped: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("facet_id") or "")].append(row)
    return {
        facet: {
            "row_count": len(facet_rows),
            "lemma_count": len({str(row.get("lemma") or "") for row in facet_rows}),
        }
        for facet, facet_rows in sorted(grouped.items())
    }


def render_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# en-ja SRS Manual Semantic Lexicon Evidence",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Collections: `{summary.get('collection_count', 0)}`",
        f"- Declared entries: `{summary.get('declared_entry_count', 0)}`",
        f"- Matched entries: `{summary.get('matched_entry_count', 0)}`",
        f"- Unmatched entries: `{summary.get('unmatched_entry_count', 0)}`",
        f"- Topic evidence rows: `{summary.get('topic_evidence_row_count', 0)}`",
        f"- Facet rows: `{summary.get('facet_row_count', 0)}`",
        "",
        "## Collections",
        "",
        "| Collection | Topic | Facet | Promotion | Declared | Matched | Missing | Ambiguous |",
        "| --- | --- | --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for row in _mapping_rows(report.get("collection_reports")):
        lines.append(
            f"| `{row.get('id', '')}` | `{row.get('target_family', '')}` | "
            f"`{row.get('facet_id', '')}` | `{row.get('promotion_eligible', '')}` | "
            f"{row.get('declared_entry_count', 0)} | {row.get('matched_entry_count', 0)} | "
            f"{row.get('missing_entry_count', 0)} | {row.get('ambiguous_entry_count', 0)} |"
        )
    lines.extend(["", "## Topic Counts", "", "| Topic | Rows | Lemmas |", "| --- | ---: | ---: |"])
    for topic, row in _as_mapping(report.get("topic_summary")).items():
        topic_row = _as_mapping(row)
        lines.append(
            f"| `{topic}` | {topic_row.get('row_count', 0)} | {topic_row.get('lemma_count', 0)} |"
        )
    lines.extend(["", "## Facet Counts", "", "| Facet | Rows | Lemmas |", "| --- | ---: | ---: |"])
    for facet, row in _as_mapping(report.get("facet_summary")).items():
        facet_row = _as_mapping(row)
        lines.append(
            f"| `{facet}` | {facet_row.get('row_count', 0)} | {facet_row.get('lemma_count', 0)} |"
        )
    lines.extend(["", "## Topic Sample", ""])
    lines.extend(_topic_sample_table(_mapping_rows(report.get("review_sample"))))
    lines.extend(["", "## Facet Sample", ""])
    lines.extend(_facet_sample_table(_mapping_rows(report.get("facet_sample"))[:120]))
    lines.extend(["", "## Unmatched Entries", ""])
    lines.extend(_unmatched_table(_mapping_rows(report.get("unmatched_entries"))[:120]))
    lines.extend(["", "## Findings", ""])
    for finding in _mapping_rows(report.get("findings")):
        lines.append(
            f"- `{finding.get('level', '')}` `{finding.get('code', '')}`: {finding.get('message', '')}"
        )
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- {item}" for item in _string_list(report.get("limitations")))
    return "\n".join(lines) + "\n"


def _topic_sample_table(rows: Sequence[Mapping[str, object]]) -> list[str]:
    lines = [
        "| Topic | Lemma | Reading | Score | Collection | Match |",
        "| --- | --- | --- | ---: | --- | --- |",
    ]
    for row in rows:
        extra = _as_mapping(row.get("extra"))
        lines.append(
            f"| `{row.get('topic', '')}` | `{row.get('lemma', '')}` | `{row.get('reading', '')}` | "
            f"{_safe_float(row.get('score'), default=0.0):.3f} | "
            f"`{extra.get('manual_semantic_collection_id', '')}` | "
            f"`{row.get('match_mode', '')}` |"
        )
    return lines


def _facet_sample_table(rows: Sequence[Mapping[str, object]]) -> list[str]:
    lines = [
        "| Facet | Lemma | Reading | Score | Collection |",
        "| --- | --- | --- | ---: | --- |",
    ]
    for row in rows:
        lines.append(
            f"| `{row.get('facet_id', '')}` | `{row.get('lemma', '')}` | `{row.get('reading', '')}` | "
            f"{_safe_float(row.get('score'), default=0.0):.3f} | `{row.get('facet_value', '')}` |"
        )
    return lines


def _unmatched_table(rows: Sequence[Mapping[str, object]]) -> list[str]:
    lines = [
        "| Collection | Lemma | Reading | Reason | Candidate readings |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            f"| `{row.get('collection_id', '')}` | `{row.get('lemma', '')}` | "
            f"`{row.get('reading', '')}` | `{row.get('reason', '')}` | "
            f"`{', '.join(_string_list(row.get('candidate_readings'))[:8])}` |"
        )
    return lines


def _load_json(path: Path) -> Mapping[str, object]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return _as_mapping(payload)


def _finding(level: str, code: str, message: str) -> dict[str, object]:
    return {"level": level, "code": code, "message": message}


def _resolve_path(path: Path) -> Path:
    return Path(path).expanduser().resolve(strict=False)


def _repo_path(path: Path) -> str:
    resolved = Path(path).expanduser().resolve(strict=False)
    try:
        return str(resolved.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(resolved)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


if __name__ == "__main__":
    raise SystemExit(main())
