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
DEFAULT_CANDIDATE_JSON = (
    TEST_OUTPUTS_ROOT / "srs_topic_direct_translation_overlay_en_de_latest.json"
)
DEFAULT_STRONG_JSON = (
    TEST_OUTPUTS_ROOT / "srs_topic_direct_translation_overlay_en_de_strong_latest.json"
)
DEFAULT_REVIEW_JSON = (
    TEST_INPUTS_ROOT / "srs_topic_direct_translation_broad_review_en_de_batch001.json"
)
DEFAULT_JSON_OUT = (
    TEST_OUTPUTS_ROOT / "srs_topic_direct_translation_broad_review_batch001_en_de_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    TEST_OUTPUTS_ROOT / "srs_topic_direct_translation_broad_review_batch001_en_de_latest.md"
)
LANGUAGE_PAIR = "en-de"
SOURCE_CHANNEL = "product_reviewed_broad_direct_translation_topic_overlay"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Apply product review decisions to one deterministic batch of lower-confidence "
            "en-de direct-translation topic candidates. This does not merge accepted rows "
            "into the runtime overlay."
        )
    )
    parser.add_argument("--candidate-json", type=Path, default=DEFAULT_CANDIDATE_JSON)
    parser.add_argument("--strong-json", type=Path, default=DEFAULT_STRONG_JSON)
    parser.add_argument("--review-json", type=Path, default=DEFAULT_REVIEW_JSON)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_report(
        candidate_json=args.candidate_json,
        strong_json=args.strong_json,
        review_json=args.review_json,
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
    candidate_json: Path = DEFAULT_CANDIDATE_JSON,
    strong_json: Path = DEFAULT_STRONG_JSON,
    review_json: Path = DEFAULT_REVIEW_JSON,
    generated_at: str | None = None,
) -> dict[str, object]:
    candidate_payload = _load_json(candidate_json)
    strong_payload = _load_json(strong_json)
    review_payload = _load_json(review_json)
    if str(candidate_payload.get("status") or "") != "ok":
        raise ValueError(f"Candidate artifact is not ok: {candidate_json}")
    if str(strong_payload.get("status") or "") != "ok":
        raise ValueError(f"Strong artifact is not ok: {strong_json}")
    if str(review_payload.get("status") or "") != "ok":
        raise ValueError(f"Review artifact is not ok: {review_json}")

    strong_keys = {
        _row_key(row)
        for row in _mapping_rows(strong_payload.get("rows"))
        if _row_key(row) is not None
    }
    broad_rows = [
        row
        for row in _mapping_rows(candidate_payload.get("rows"))
        if _row_key(row) is not None
        and _row_key(row) not in strong_keys
        and str(row.get("confidence_label") or "") == "direct_translation_review"
    ]
    broad_rows = sorted(
        broad_rows,
        key=lambda row: (
            str(row.get("topic") or ""),
            _safe_float(row.get("corpus_rank"), default=999999.0),
            str(row.get("lemma") or ""),
        ),
    )

    batch_config = _as_mapping(review_payload.get("batch"))
    start_index = max(1, int(_safe_float(batch_config.get("start_index"), default=1.0)))
    limit = max(1, int(_safe_float(batch_config.get("limit"), default=250.0)))
    batch_rows = broad_rows[start_index - 1 : start_index - 1 + limit]
    batch_keys = {_row_key(row) for row in batch_rows if _row_key(row) is not None}

    decisions = _decision_rows_by_key(review_payload)
    accepted_rows: list[dict[str, object]] = []
    rejected_rows: list[dict[str, object]] = []
    skipped_rows: list[dict[str, object]] = []
    missing_decisions: list[dict[str, object]] = []
    extra_decisions: list[dict[str, object]] = []

    for row in batch_rows:
        key = _row_key(row)
        if key is None:
            continue
        decision = decisions.get(key)
        if decision is None:
            missing_decisions.append(_review_stub(row))
            continue
        decision_type = str(decision.get("decision") or "").strip()
        if decision_type == "accept":
            accepted_rows.append(_accepted_row(row, decision))
        elif decision_type == "reject":
            rejected_rows.append(_reviewed_nonaccepted_row(row, decision))
        elif decision_type == "skip":
            skipped_rows.append(_reviewed_nonaccepted_row(row, decision))
        else:
            missing_decisions.append(_review_stub(row))

    for key, decision in sorted(decisions.items()):
        if key not in batch_keys:
            extra_decisions.append(
                {
                    "topic": key[0],
                    "lemma": key[1],
                    "decision": decision.get("decision", ""),
                    "category": decision.get("category", ""),
                    "reason": decision.get("reason", ""),
                }
            )

    batch_id = int(_safe_float(batch_config.get("batch_id"), default=1.0))
    overlay_id = f"srs_topic_direct_translation_broad_review_batch{batch_id:03d}_en_de_v1"
    status = "ok" if batch_rows and not missing_decisions and not extra_decisions else "review"
    return {
        "schema_version": 1,
        "status": status,
        "decision": (
            f"srs_topic_direct_translation_broad_review_batch{batch_id:03d}_en_de_ready"
            if status == "ok"
            else f"srs_topic_direct_translation_broad_review_batch{batch_id:03d}_en_de_needs_review"
        ),
        "generated_at": generated_at or _utc_now(),
        "language_pair": LANGUAGE_PAIR,
        "overlay_id": overlay_id,
        "overlay_policy": {
            "promotion_state": "reviewed_broad_candidate_not_merged",
            "runtime_policy_change": "none",
            "review_id": str(review_payload.get("review_id") or ""),
            "acceptance_policy": _as_mapping(review_payload.get("acceptance_policy")),
        },
        "inputs": {
            "candidate_json": _repo_path(candidate_json),
            "strong_json": _repo_path(strong_json),
            "review_json": _repo_path(review_json),
        },
        "batch": {
            "start_index": start_index,
            "limit": limit,
            "batch_id": batch_id,
            "selected_row_count": len(batch_rows),
            "broad_only_total": len(broad_rows),
            "sort_policy": "topic_then_corpus_rank_then_lemma",
        },
        "summary": _summary(
            accepted_rows=accepted_rows,
            rejected_rows=rejected_rows,
            skipped_rows=skipped_rows,
            missing_decisions=missing_decisions,
            extra_decisions=extra_decisions,
        ),
        "rows": accepted_rows,
        "rejected_rows": rejected_rows,
        "skipped_rows": skipped_rows,
        "missing_decisions": missing_decisions,
        "extra_decisions": extra_decisions,
    }


def render_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    batch = _as_mapping(report.get("batch"))
    batch_id = int(_safe_float(batch.get("batch_id"), default=1.0))
    lines = [
        f"# en-de Broad Direct Translation Topic Review Batch {batch_id:03d}",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Broad-only total: `{batch.get('broad_only_total', 0)}`",
        f"- Batch start/limit: `{batch.get('start_index', 0)}` / `{batch.get('limit', 0)}`",
        f"- Accepted rows: `{summary.get('accepted_row_count', 0)}`",
        f"- Rejected rows: `{summary.get('rejected_row_count', 0)}`",
        f"- Skipped rows: `{summary.get('skipped_row_count', 0)}`",
        f"- Missing decisions: `{summary.get('missing_decision_count', 0)}`",
        f"- Extra decisions: `{summary.get('extra_decision_count', 0)}`",
        "",
        "## Counts By Decision",
        "",
        "| Decision | Rows |",
        "| --- | ---: |",
        f"| `accept` | {int(summary.get('accepted_row_count', 0))} |",
        f"| `reject` | {int(summary.get('rejected_row_count', 0))} |",
        f"| `skip` | {int(summary.get('skipped_row_count', 0))} |",
        "",
        "## Accepted Counts",
        "",
        "| Topic | Rows |",
        "| --- | ---: |",
    ]
    for topic, count in sorted(_as_mapping(summary.get("accepted_counts_by_topic")).items()):
        lines.append(f"| `{topic}` | {int(count)} |")

    lines.extend(["", "## Accepted Rows", ""])
    lines.extend(_decision_table(_mapping_rows(report.get("rows"))))
    lines.extend(["", "## Rejected Rows", ""])
    lines.extend(_decision_table(_mapping_rows(report.get("rejected_rows"))))
    lines.extend(["", "## Skipped Rows", ""])
    lines.extend(_decision_table(_mapping_rows(report.get("skipped_rows"))))
    return "\n".join(lines) + "\n"


def _decision_table(rows: Sequence[Mapping[str, object]]) -> list[str]:
    lines = [
        "| Topic | Lemma | Rank | Source | German | Category | Reason |",
        "| --- | --- | ---: | --- | --- | --- | --- |",
    ]
    for row in rows:
        provenance = _as_mapping(row.get("provenance"))
        source = f"{provenance.get('translation_route', '')}:{provenance.get('source_lemma', '')}"
        lines.append(
            "| "
            f"`{_escape_md(row.get('topic', ''))}` | "
            f"`{_escape_md(row.get('lemma', ''))}` | "
            f"{_safe_float(row.get('corpus_rank'), default=0):.0f} | "
            f"`{_escape_md(source)}` | "
            f"`{_escape_md(provenance.get('raw_german_translation', ''))}` | "
            f"`{_escape_md(row.get('review_category', ''))}` | "
            f"{_escape_md(row.get('review_note', ''))} |"
        )
    if not rows:
        lines.append("| - | - | - | - | - | - | - |")
    return lines


def _accepted_row(
    candidate: Mapping[str, object], decision: Mapping[str, object]
) -> dict[str, object]:
    row = dict(candidate)
    provenance = dict(_as_mapping(row.get("provenance")))
    overlay_id = str(decision.get("overlay_id") or "")
    provenance["source_overlay_ids"] = _append_unique(
        _string_list(provenance.get("source_overlay_ids")),
        str(row.get("source_label") or ""),
        overlay_id,
    )
    provenance["reviewed_overlay_id"] = overlay_id
    provenance["review_policy"] = "manual_accept_from_broad_direct_translation_batch001"
    provenance["promotion_state"] = "reviewed_broad_candidate_not_merged"
    row["membership"] = _safe_float(decision.get("membership"), default=1.0)
    row["confidence_label"] = str(decision.get("confidence_label") or "reviewed_broad")
    row["evidence_score"] = max(_safe_float(row.get("evidence_score")), 0.82)
    row["review_state"] = "product_reviewed_broad_direct_translation"
    row["review_category"] = str(decision.get("category") or "")
    row["review_note"] = str(decision.get("reason") or "")
    row["source_channel"] = SOURCE_CHANNEL
    row["source_label"] = "en_de_reviewed_broad_direct_translation_topic"
    row["provenance"] = provenance
    return row


def _reviewed_nonaccepted_row(
    candidate: Mapping[str, object], decision: Mapping[str, object]
) -> dict[str, object]:
    row = dict(candidate)
    row["membership"] = 0.0
    row["evidence_score"] = 0.0
    row["review_state"] = str(decision.get("decision") or "review")
    row["review_category"] = str(decision.get("category") or "")
    row["review_note"] = str(decision.get("reason") or "")
    row["source_channel"] = SOURCE_CHANNEL
    return row


def _decision_rows_by_key(
    payload: Mapping[str, object],
) -> dict[tuple[str, str], dict[str, object]]:
    categories = _as_mapping(payload.get("decision_categories"))
    batch_config = _as_mapping(payload.get("batch"))
    batch_id = int(_safe_float(batch_config.get("batch_id"), default=1.0))
    overlay_id = f"srs_topic_direct_translation_broad_review_batch{batch_id:03d}_en_de_v1"
    out: dict[tuple[str, str], dict[str, object]] = {}
    for decision_type in ("accept", "reject", "skip"):
        for row in _mapping_rows(payload.get(f"{decision_type}_decisions")):
            topic = str(row.get("topic") or "").strip()
            lemma = str(row.get("lemma") or "").strip()
            category_id = str(row.get("category") or "").strip()
            category = _as_mapping(categories.get(category_id))
            if not topic or not lemma:
                continue
            out[(topic, lemma)] = {
                "decision": decision_type,
                "category": category_id,
                "reason": str(row.get("reason") or category.get("reason") or ""),
                "membership": row.get("membership", category.get("membership", 1.0)),
                "confidence_label": row.get(
                    "confidence_label", category.get("confidence_label", "reviewed_broad")
                ),
                "overlay_id": overlay_id,
            }
    return out


def _row_key(row: Mapping[str, object]) -> tuple[str, str] | None:
    if str(row.get("language_pair") or "").strip() != LANGUAGE_PAIR:
        return None
    topic = str(row.get("topic") or "").strip()
    lemma = str(row.get("lemma") or "").strip()
    if not topic or not lemma:
        return None
    return topic, lemma


def _review_stub(row: Mapping[str, object]) -> dict[str, object]:
    return {
        "topic": str(row.get("topic") or ""),
        "lemma": str(row.get("lemma") or ""),
        "corpus_rank": row.get("corpus_rank"),
    }


def _summary(
    *,
    accepted_rows: Sequence[Mapping[str, object]],
    rejected_rows: Sequence[Mapping[str, object]],
    skipped_rows: Sequence[Mapping[str, object]],
    missing_decisions: Sequence[Mapping[str, object]],
    extra_decisions: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    accepted_counts = Counter(str(row.get("topic") or "") for row in accepted_rows)
    rejected_counts = Counter(str(row.get("topic") or "") for row in rejected_rows)
    skipped_counts = Counter(str(row.get("topic") or "") for row in skipped_rows)
    return {
        "accepted_row_count": len(accepted_rows),
        "accepted_unique_lemma_count": len({str(row.get("lemma") or "") for row in accepted_rows}),
        "accepted_counts_by_topic": dict(sorted(accepted_counts.items())),
        "rejected_row_count": len(rejected_rows),
        "rejected_counts_by_topic": dict(sorted(rejected_counts.items())),
        "skipped_row_count": len(skipped_rows),
        "skipped_counts_by_topic": dict(sorted(skipped_counts.items())),
        "missing_decision_count": len(missing_decisions),
        "extra_decision_count": len(extra_decisions),
    }


def _load_json(path: Path) -> Mapping[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _mapping_rows(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, list):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _string_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item)]
    if value is None:
        return []
    return [str(value)]


def _append_unique(values: Sequence[str], *items: str) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for value in [*values, *items]:
        value = str(value)
        if not value or value in seen:
            continue
        seen.add(value)
        out.append(value)
    return out


def _safe_float(value: object, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _escape_md(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def _repo_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


if __name__ == "__main__":
    raise SystemExit(main())
