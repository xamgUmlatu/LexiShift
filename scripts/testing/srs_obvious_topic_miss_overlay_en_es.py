#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEST_INPUTS_ROOT = PROJECT_ROOT / "docs" / "test_inputs"
TEST_OUTPUTS_ROOT = PROJECT_ROOT / "docs" / "test_outputs"
DEFAULT_REVIEW_LABELS = (
    TEST_INPUTS_ROOT / "srs_obvious_topic_miss_review_labels_en_es_spalex_10k.json"
)
DEFAULT_EXISTING_OVERLAYS = (
    TEST_OUTPUTS_ROOT / "srs_animals_plants_topic_overlay_en_es_spalex_10k_latest.json",
    TEST_OUTPUTS_ROOT / "srs_food_cooking_topic_overlay_en_es_spalex_10k_latest.json",
    TEST_OUTPUTS_ROOT / "srs_source_topic_overlay_en_es_spalex_10k_latest.json",
)
DEFAULT_ZIPF_BRIDGE = (
    TEST_OUTPUTS_ROOT / "semantic_veto_srs_zipf_bridge_en_es_spalex_10k_full_rulegen_latest.json"
)
DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / "srs_obvious_topic_miss_overlay_en_es_spalex_10k_latest.json"
DEFAULT_MARKDOWN_OUT = (
    TEST_OUTPUTS_ROOT / "srs_obvious_topic_miss_overlay_en_es_spalex_10k_latest.md"
)
ACCEPTED_DECISIONS = {"accept_strong_topic"}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a small reviewed overlay for obvious en-es SRS topic misses."
    )
    parser.add_argument("--review-labels-json", type=Path, default=DEFAULT_REVIEW_LABELS)
    parser.add_argument("--zipf-bridge-json", type=Path, default=DEFAULT_ZIPF_BRIDGE)
    parser.add_argument(
        "--existing-overlay-json",
        action="append",
        type=Path,
        default=[],
        help="Existing overlay JSON to avoid duplicate lemma/topic rows. May be repeated.",
    )
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    existing_paths = args.existing_overlay_json or list(DEFAULT_EXISTING_OVERLAYS)
    report = build_overlay(
        review_payload=_load_json(args.review_labels_json),
        zipf_bridge_payload=_load_json(args.zipf_bridge_json),
        existing_overlay_payloads=[
            payload
            for payload in (_load_json_if_exists(path) for path in existing_paths)
            if payload
        ],
        review_labels_path=args.review_labels_json,
        zipf_bridge_path=args.zipf_bridge_json,
        existing_overlay_paths=existing_paths,
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    args.markdown_out.write_text(render_markdown(report))
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    if args.fail_on_review and report["status"] != "ok":
        return 1
    return 0


def build_overlay(
    *,
    review_payload: Mapping[str, object],
    zipf_bridge_payload: Mapping[str, object],
    existing_overlay_payloads: Sequence[Mapping[str, object]],
    review_labels_path: Path | None = None,
    zipf_bridge_path: Path | None = None,
    existing_overlay_paths: Sequence[Path] = (),
    generated_at: str | None = None,
) -> dict[str, object]:
    bridge_by_target = _bridge_rows_by_target(zipf_bridge_payload)
    existing_pairs = _existing_lemma_topic_pairs(existing_overlay_payloads)
    rows: list[dict[str, object]] = []
    skipped_missing: list[dict[str, str]] = []
    skipped_existing: list[dict[str, str]] = []
    for label in _mapping_rows(review_payload.get("labels")):
        decision = str(label.get("decision") or "").strip()
        lemma = str(label.get("lemma") or "").strip()
        topic = str(label.get("topic") or "").strip()
        if decision not in ACCEPTED_DECISIONS or not lemma or not topic:
            continue
        if (lemma, topic) in existing_pairs:
            skipped_existing.append({"lemma": lemma, "topic": topic})
            continue
        bridge = _bridge_for_label(label, bridge_by_target.get(lemma, ()))
        if not bridge:
            skipped_missing.append({"lemma": lemma, "topic": topic})
            continue
        rows.append(
            _overlay_row(
                label=label,
                bridge=bridge,
                review_labels_path=review_labels_path,
            )
        )

    rows.sort(key=lambda row: (str(row["topic"]), str(row["lemma"]), str(row["review_id"])))
    counts_by_topic = Counter(str(row["topic"]) for row in rows)
    status = "ok" if rows and not skipped_missing else "review"
    return {
        "schema_version": 1,
        "status": status,
        "decision": (
            "srs_obvious_topic_miss_overlay_ready"
            if status == "ok"
            else "srs_obvious_topic_miss_overlay_needs_review"
        ),
        "generated_at": generated_at or _utc_now(),
        "overlay_id": "srs_obvious_topic_miss_overlay_en_es_spalex_10k_v1",
        "language_pair": "en-es",
        "inputs": {
            "review_labels_json": _repo_path(review_labels_path),
            "zipf_bridge_json": _repo_path(zipf_bridge_path),
            "existing_overlay_json": [_repo_path(path) for path in existing_overlay_paths],
        },
        "overlay_policy": {
            "promotion_state": "reviewed_obvious_miss_poc_candidate_not_product_overlay",
            "runtime_policy_change": "none",
            "source_download": "none",
            "source": "manual obvious-miss review checked against local Zipf bridge target lemmas",
            "membership": 1.0,
            "duplicate_policy": "omit if same lemma/topic exists in current overlay stack",
        },
        "summary": {
            "row_count": len(rows),
            "topic_count": len(counts_by_topic),
            "counts_by_topic": dict(sorted(counts_by_topic.items())),
            "skipped_existing_count": len(skipped_existing),
            "skipped_missing_count": len(skipped_missing),
        },
        "skipped_existing": skipped_existing,
        "skipped_missing_from_zipf_bridge": skipped_missing,
        "rows": rows,
        "limitations": [
            "This is a deliberately small reviewed patch for high-confidence obvious misses.",
            "It does not attempt broad taxonomy expansion or embeddings-based inference.",
            "Rows remain admission-preview overlay candidates until product overlay promotion.",
        ],
    }


def render_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# en-es Obvious Topic Miss Overlay",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Rows: `{summary.get('row_count', 0)}`",
        f"- Skipped existing: `{summary.get('skipped_existing_count', 0)}`",
        f"- Skipped missing: `{summary.get('skipped_missing_count', 0)}`",
        "",
        "## Topic Counts",
        "",
        "| Topic | Rows |",
        "| --- | ---: |",
    ]
    for topic, count in _as_mapping(summary.get("counts_by_topic")).items():
        lines.append(f"| `{topic}` | {count} |")
    lines.extend(
        [
            "",
            "## Rows",
            "",
            "| Topic | Lemma | Bridge Source | Zipf | Notes |",
            "| --- | --- | --- | ---: | --- |",
        ]
    )
    for row in _mapping_rows(report.get("rows")):
        notes = _as_mapping(row.get("provenance")).get("review_notes", "")
        bridge = _as_mapping(row.get("provenance")).get("bridge_source", "")
        lines.append(
            f"| `{row.get('topic', '')}` | `{row.get('lemma', '')}` | "
            f"`{bridge}` | {row.get('evidence_score', '')} | {notes} |"
        )
    if _mapping_rows(report.get("skipped_existing")):
        lines.extend(["", "## Skipped Existing", ""])
        for row in _mapping_rows(report.get("skipped_existing")):
            lines.append(f"- `{row.get('lemma')}` already has `{row.get('topic')}`")
    return "\n".join(lines) + "\n"


def _overlay_row(
    *,
    label: Mapping[str, object],
    bridge: Mapping[str, object],
    review_labels_path: Path | None,
) -> dict[str, object]:
    lemma = str(label.get("lemma") or "").strip()
    topic = str(label.get("topic") or "").strip()
    zipf = _safe_float(bridge.get("target_zipf_frequency_es"))
    return {
        "language_pair": "en-es",
        "lemma": lemma,
        "topic": topic,
        "review_id": str(label.get("review_id") or f"srs-obvious-topic:{topic}:{lemma}"),
        "membership": 1.0,
        "confidence_label": "strong",
        "evidence_score": round(zipf or 0.0, 6),
        "evidence_band": str(bridge.get("target_zipf_band_es") or ""),
        "source_channel": "curated_overlay",
        "source_label": "obvious_topic_miss_review",
        "review_state": "agent_labeled_pending_user_approval",
        "provenance": {
            "promotion_state": "reviewed_obvious_miss_poc_candidate_not_product_overlay",
            "review_labels": _repo_path(review_labels_path),
            "review_notes": str(label.get("notes") or ""),
            "bridge_source": str(bridge.get("source") or ""),
            "bridge_source_zipf": bridge.get("source_zipf_frequency_en"),
            "bridge_target_zipf": bridge.get("target_zipf_frequency_es"),
        },
    }


def _bridge_rows_by_target(
    payload: Mapping[str, object],
) -> dict[str, tuple[Mapping[str, object], ...]]:
    grouped: dict[str, list[Mapping[str, object]]] = {}
    for row in _mapping_rows(payload.get("full_source_target_pairs")):
        target = str(row.get("target") or "").strip()
        if not target:
            continue
        grouped.setdefault(target, []).append(row)
    return {
        target: tuple(
            sorted(
                rows,
                key=lambda row: (
                    -_safe_float(row.get("target_zipf_frequency_es")),
                    str(row.get("source") or ""),
                ),
            )
        )
        for target, rows in grouped.items()
    }


def _bridge_for_label(
    label: Mapping[str, object],
    bridge_rows: Sequence[Mapping[str, object]],
) -> Mapping[str, object] | None:
    requested_source = str(label.get("bridge_source") or "").strip()
    if requested_source:
        for row in bridge_rows:
            if str(row.get("source") or "").strip() == requested_source:
                return row
        return None
    return bridge_rows[0] if bridge_rows else None


def _existing_lemma_topic_pairs(payloads: Sequence[Mapping[str, object]]) -> set[tuple[str, str]]:
    pairs: set[tuple[str, str]] = set()
    for payload in payloads:
        if str(payload.get("status") or "") != "ok":
            continue
        for row in _mapping_rows(payload.get("rows")):
            lemma = str(row.get("lemma") or "").strip()
            topic = str(row.get("topic") or "").strip()
            if lemma and topic:
                pairs.add((lemma, topic))
    return pairs


def _load_json(path: Path) -> Mapping[str, object]:
    return _as_mapping(json.loads(path.expanduser().read_text(encoding="utf-8")))


def _load_json_if_exists(path: Path) -> Mapping[str, object] | None:
    return _load_json(path) if path.exists() else None


def _repo_path(path: Path | None) -> str:
    if path is None:
        return ""
    try:
        return str(Path(path).resolve(strict=False).relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _mapping_rows(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, list):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def _safe_float(value: object) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


if __name__ == "__main__":
    raise SystemExit(main())
