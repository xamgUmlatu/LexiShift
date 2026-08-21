#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEST_OUTPUTS_ROOT = PROJECT_ROOT / "docs" / "test_outputs"
DEFAULT_OVERLAYS = (
    TEST_OUTPUTS_ROOT / "srs_topic_manual_semantic_lexicon_en_de_latest.json",
    TEST_OUTPUTS_ROOT / "srs_wikidata_natural_taxonomy_topic_overlay_en_de_latest.json",
    TEST_OUTPUTS_ROOT / "srs_wikidata_science_topic_overlay_en_de_latest.json",
    TEST_OUTPUTS_ROOT / "srs_topic_direct_translation_reviewed_en_de_latest.json",
    TEST_OUTPUTS_ROOT / "srs_topic_direct_translation_broad_review_batch001_en_de_latest.json",
    TEST_OUTPUTS_ROOT / "srs_topic_direct_translation_broad_review_batch002_en_de_latest.json",
)
DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / "srs_topic_reviewed_overlay_merged_en_de_latest.json"
DEFAULT_MARKDOWN_OUT = TEST_OUTPUTS_ROOT / "srs_topic_reviewed_overlay_merged_en_de_latest.md"
LANGUAGE_PAIR = "en-de"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Merge reviewed en-de topic overlay artifacts into one preferred runtime "
            "candidate. This does not infer new topics or mutate installed SRS state."
        )
    )
    parser.add_argument(
        "--overlay-json",
        action="append",
        type=Path,
        default=[],
        help="Reviewed topic overlay JSON. May be repeated. Defaults to the current en-de overlay stack.",
    )
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    overlay_paths = args.overlay_json if args.overlay_json else list(DEFAULT_OVERLAYS)
    report = build_overlay(overlay_paths=overlay_paths)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.markdown_out.write_text(render_markdown(report), encoding="utf-8")
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    return 0


def build_overlay(
    *,
    overlay_paths: Sequence[Path],
    generated_at: str | None = None,
) -> dict[str, object]:
    loaded_payloads: list[Mapping[str, object]] = []
    missing_paths: list[str] = []
    invalid_paths: list[str] = []
    for path in overlay_paths:
        payload = _load_json_if_ready(path)
        if payload is None:
            if Path(path).expanduser().exists():
                invalid_paths.append(_repo_path(path))
            else:
                missing_paths.append(_repo_path(path))
            continue
        loaded_payloads.append(payload)

    rows_by_key: dict[tuple[str, str, str], dict[str, object]] = {}
    duplicate_count = 0
    source_overlay_ids: list[str] = []
    for payload in loaded_payloads:
        overlay_id = str(payload.get("overlay_id") or "").strip()
        if overlay_id:
            source_overlay_ids.append(overlay_id)
        for row in _mapping_rows(payload.get("rows")):
            normalized = _normalized_row(row, source_overlay_id=overlay_id)
            if normalized is None:
                continue
            key = (
                str(normalized["language_pair"]),
                str(normalized["lemma"]),
                str(normalized["topic"]),
            )
            existing = rows_by_key.get(key)
            if existing is None:
                rows_by_key[key] = normalized
                continue
            duplicate_count += 1
            rows_by_key[key] = _preferred_row(existing, normalized)

    rows = sorted(
        rows_by_key.values(),
        key=lambda row: (
            str(row.get("topic") or ""),
            -_safe_float(row.get("membership")),
            str(row.get("lemma") or ""),
        ),
    )
    summary = _summary(rows)
    return {
        "schema_version": 1,
        "status": "ok" if rows else "review",
        "decision": "srs_topic_reviewed_overlay_merged_en_de_ready"
        if rows
        else "srs_topic_reviewed_overlay_merged_en_de_needs_review",
        "generated_at": generated_at or _utc_now(),
        "language_pair": LANGUAGE_PAIR,
        "overlay_id": "srs_topic_reviewed_overlay_merged_en_de_v1",
        "overlay_policy": {
            "promotion_state": "reviewed_overlay_candidate_not_default",
            "runtime_policy_change": "none",
            "source_download": "none",
            "merge_policy": "dedupe_by_language_pair_lemma_topic_prefer_runtime_eligible",
            "input_overlay_ids": sorted(dict.fromkeys(source_overlay_ids)),
        },
        "inputs": {
            "overlay_json": [_repo_path(path) for path in overlay_paths],
            "loaded_overlay_count": len(loaded_payloads),
            "missing_overlay_json": missing_paths,
            "invalid_overlay_json": invalid_paths,
        },
        "summary": {
            **summary,
            "duplicate_row_count": duplicate_count,
        },
        "rows": rows,
    }


def render_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# en-de Reviewed Topic Overlay Merge",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Row count: `{summary.get('row_count', 0)}`",
        f"- Runtime-effective row count: `{summary.get('runtime_effective_row_count', 0)}`",
        f"- Topic count: `{summary.get('topic_count', 0)}`",
        f"- Duplicate rows resolved: `{summary.get('duplicate_row_count', 0)}`",
        "",
        "## Runtime-Effective Counts",
        "",
        "| Topic | Runtime Rows | Raw Rows |",
        "| --- | ---: | ---: |",
    ]
    raw_counts = _as_mapping(summary.get("counts_by_topic"))
    runtime_counts = _as_mapping(summary.get("runtime_effective_counts_by_topic"))
    for topic in sorted(set(raw_counts) | set(runtime_counts)):
        lines.append(
            f"| `{topic}` | {int(runtime_counts.get(topic) or 0)} | "
            f"{int(raw_counts.get(topic) or 0)} |"
        )
    lines.extend(["", "## Inputs", ""])
    inputs = _as_mapping(report.get("inputs"))
    for path in _string_list(inputs.get("overlay_json")):
        lines.append(f"- `{path}`")
    return "\n".join(lines) + "\n"


def _normalized_row(
    row: Mapping[str, object],
    *,
    source_overlay_id: str,
) -> dict[str, object] | None:
    pair = str(row.get("language_pair") or "").strip()
    lemma = str(row.get("lemma") or "").strip()
    topic = str(row.get("topic") or "").strip()
    if pair != LANGUAGE_PAIR or not lemma or not topic:
        return None
    next_row = dict(row)
    next_row["language_pair"] = pair
    next_row["lemma"] = lemma
    next_row["topic"] = topic
    provenance = dict(_as_mapping(next_row.get("provenance")))
    if source_overlay_id:
        provenance.setdefault("source_overlay_ids", [])
        source_ids = provenance.get("source_overlay_ids")
        if isinstance(source_ids, list) and source_overlay_id not in source_ids:
            source_ids.append(source_overlay_id)
    next_row["provenance"] = provenance
    return next_row


def _preferred_row(left: Mapping[str, object], right: Mapping[str, object]) -> dict[str, object]:
    left_score = _row_priority(left)
    right_score = _row_priority(right)
    winner = dict(right if right_score > left_score else left)
    provenance = dict(_as_mapping(winner.get("provenance")))
    source_ids: list[str] = []
    for row in (left, right):
        for source_id in _string_list(_as_mapping(row.get("provenance")).get("source_overlay_ids")):
            if source_id not in source_ids:
                source_ids.append(source_id)
    if source_ids:
        provenance["source_overlay_ids"] = source_ids
    winner["provenance"] = provenance
    return winner


def _row_priority(row: Mapping[str, object]) -> tuple[int, float, float, float]:
    membership = _safe_float(row.get("membership"))
    confidence_label = str(row.get("confidence_label") or "").strip()
    confidence_rank = 2 if confidence_label == "strong" else 1 if confidence_label else 0
    evidence = _safe_float(row.get("evidence_score"))
    rank = _safe_float(row.get("corpus_rank"), default=999999.0)
    return (confidence_rank, membership, evidence, -rank)


def _summary(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    counts_by_topic = Counter(str(row.get("topic") or "") for row in rows)
    runtime_rows = [
        row
        for row in rows
        if _safe_float(row.get("membership")) >= 1.0
        and str(row.get("review_state") or "").strip()
        not in {"rejected", "reject_wrong_topic", "reject_secondary_or_obscure_sense"}
    ]
    runtime_counts = Counter(str(row.get("topic") or "") for row in runtime_rows)
    counts_by_confidence = Counter(str(row.get("confidence_label") or "") for row in rows)
    runtime_confidence = Counter(str(row.get("confidence_label") or "") for row in runtime_rows)
    return {
        "row_count": len(rows),
        "runtime_effective_row_count": len(runtime_rows),
        "unique_lemma_count": len({str(row.get("lemma") or "") for row in rows}),
        "runtime_effective_unique_lemma_count": len(
            {str(row.get("lemma") or "") for row in runtime_rows}
        ),
        "topic_count": len(counts_by_topic),
        "runtime_effective_topic_count": len(runtime_counts),
        "counts_by_topic": dict(sorted(counts_by_topic.items())),
        "runtime_effective_counts_by_topic": dict(sorted(runtime_counts.items())),
        "counts_by_confidence": dict(sorted(counts_by_confidence.items())),
        "runtime_effective_counts_by_confidence": dict(sorted(runtime_confidence.items())),
    }


def _load_json_if_ready(path: Path) -> Mapping[str, object] | None:
    resolved = Path(path).expanduser()
    if not resolved.exists():
        return None
    try:
        payload = json.loads(resolved.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, Mapping):
        return None
    if str(payload.get("status") or "").strip() != "ok":
        return None
    return payload


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _mapping_rows(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def _string_list(value: object) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    return [str(item) for item in value if str(item).strip()]


def _safe_float(value: object, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _repo_path(path: Path | None) -> str:
    if path is None:
        return ""
    resolved = Path(path).expanduser()
    try:
        return str(resolved.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(resolved)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


if __name__ == "__main__":
    raise SystemExit(main())
