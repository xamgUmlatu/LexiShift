#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEST_OUTPUTS_ROOT = PROJECT_ROOT / "docs" / "test_outputs"
DEFAULT_DEPTH_AUDIT = TEST_OUTPUTS_ROOT / "srs_topic_family_depth_audit_en_es_latest.json"
DEFAULT_RELEASE_READINESS = TEST_OUTPUTS_ROOT / "srs_topic_release_readiness_en_es_latest.json"
DEFAULT_LABELS_JSON = (
    PROJECT_ROOT
    / "docs"
    / "test_inputs"
    / "srs_source_topic_precision_review_labels_en_es_spalex_10k.json"
)
DEFAULT_JSON_OUT = (
    TEST_OUTPUTS_ROOT / "srs_source_topic_precision_review_en_es_spalex_10k_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    TEST_OUTPUTS_ROOT / "srs_source_topic_precision_review_en_es_spalex_10k_latest.md"
)
DEFAULT_FRONTIER_LABEL = "spalex_10k_research"
DEFAULT_RELEASE_STATUSES = ("release_candidate", "release_candidate_limited_depth")
DEFAULT_MAX_ROWS_PER_FAMILY = 12
ACCEPT_DECISIONS = {"accept_strong_topic", "accept_light_topic"}
REJECT_DECISIONS = {"reject_wrong_topic", "reject_secondary_or_obscure_sense"}
ALLOWED_DECISIONS = (
    "accept_strong_topic",
    "accept_light_topic",
    "reject_wrong_topic",
    "reject_secondary_or_obscure_sense",
    "uncertain_needs_source_check",
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a deterministic precision-review packet for source-backed en-es "
            "SRS topic release candidates. Read-only; no overlays or runtime changes."
        )
    )
    parser.add_argument("--depth-audit-json", type=Path, default=DEFAULT_DEPTH_AUDIT)
    parser.add_argument("--release-readiness-json", type=Path, default=DEFAULT_RELEASE_READINESS)
    parser.add_argument("--frontier-label", default=DEFAULT_FRONTIER_LABEL)
    parser.add_argument(
        "--release-status",
        action="append",
        default=[],
        help=(
            "Release status to include. May be repeated. Defaults to default and "
            "limited-depth release candidates."
        ),
    )
    parser.add_argument(
        "--labels-json",
        type=Path,
        default=DEFAULT_LABELS_JSON,
        help="Optional review-label JSON. Missing file leaves rows pending.",
    )
    parser.add_argument("--max-rows-per-family", type=int, default=DEFAULT_MAX_ROWS_PER_FAMILY)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    labels_path = _resolve_path(args.labels_json) if args.labels_json else None
    release_statuses = tuple(args.release_status or DEFAULT_RELEASE_STATUSES)
    report = build_report(
        depth_audit_payload=_load_json(args.depth_audit_json),
        release_readiness_payload=_load_json(args.release_readiness_json),
        labels_payload=_load_json_if_exists(labels_path),
        depth_audit_path=args.depth_audit_json,
        release_readiness_path=args.release_readiness_json,
        labels_path=labels_path,
        frontier_label=str(args.frontier_label),
        release_statuses=release_statuses,
        max_rows_per_family=max(1, int(args.max_rows_per_family)),
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
    depth_audit_payload: Mapping[str, object],
    release_readiness_payload: Mapping[str, object],
    labels_payload: Mapping[str, object] | None = None,
    depth_audit_path: Path | None = None,
    release_readiness_path: Path | None = None,
    labels_path: Path | None = None,
    frontier_label: str = DEFAULT_FRONTIER_LABEL,
    release_statuses: Sequence[str] = DEFAULT_RELEASE_STATUSES,
    max_rows_per_family: int = DEFAULT_MAX_ROWS_PER_FAMILY,
    generated_at: str | None = None,
) -> dict[str, object]:
    included_statuses = tuple(str(item) for item in release_statuses if str(item).strip())
    release_topics = _release_topics(
        release_readiness_payload,
        included_statuses=included_statuses,
    )
    frontier = _resolve_frontier(depth_audit_payload, frontier_label=frontier_label)
    family_reports = {
        str(row.get("family") or ""): row for row in _mapping_rows(frontier.get("families"))
    }
    review_queue: list[dict[str, object]] = []
    for family_id in release_topics:
        family_rows = _candidate_rows_from_family(
            family_id=family_id,
            family_report=family_reports.get(family_id, {}),
            max_rows=max_rows_per_family,
        )
        for row in family_rows:
            review_queue.append(row)
    for index, row in enumerate(review_queue, start=1):
        row["review_id"] = f"srs-src-topic-{index:03d}"
        row["manual_review"] = {
            "state": "pending_user_review",
            "decision": "",
            "notes": "",
            "allowed_decisions": list(ALLOWED_DECISIONS),
        }

    label_result = _apply_labels(
        review_queue=review_queue,
        labels_payload=labels_payload,
        labels_path=labels_path,
    )
    findings = _findings(
        review_queue=review_queue,
        frontier=frontier,
        release_topics=release_topics,
        label_result=label_result,
    )
    status = "ok" if not any(row["level"] == "FAIL" for row in findings) else "review"
    return {
        "schema_version": 1,
        "status": status,
        "decision": (
            "srs_source_topic_precision_review_ready"
            if status == "ok"
            else "srs_source_topic_precision_review_needs_review"
        ),
        "generated_at": generated_at or _utc_now(),
        "language_pair": "en-es",
        "inputs": {
            "depth_audit_json": _repo_path(depth_audit_path),
            "release_readiness_json": _repo_path(release_readiness_path),
            "labels_json": _repo_path(labels_path),
            "labels_review_id": str(label_result.get("labels_review_id") or ""),
            "labels_state": str(label_result.get("labels_state") or ""),
            "frontier_label": str(frontier.get("label") or frontier_label),
            "release_statuses": list(included_statuses),
            "max_rows_per_family": int(max_rows_per_family),
        },
        "review_policy": {
            "state": "agent_labeled_pending_user_approval"
            if label_result.get("labels_provided")
            else "pending_user_review",
            "allowed_decisions": list(ALLOWED_DECISIONS),
            "scope": (
                "Sampled release-candidate evidence from the topic-family depth audit; "
                "not a full-universe precision estimate."
            ),
        },
        "summary": _summary(review_queue, findings),
        "precision_by_family": _precision_by(review_queue, "family"),
        "precision_by_source_label": _precision_by(review_queue, "source_label"),
        "rejected_rows": _rejected_rows(review_queue),
        "review_queue": review_queue,
        "label_result": label_result,
        "findings": findings,
        "limitations": [
            "This packet samples compact evidence retained by the depth audit, not every source row.",
            "Agent labels are pending user approval and do not promote runtime topic truth by themselves.",
            "Rejects in this sample should tighten release guidance before default-visible topics are accepted.",
        ],
    }


def render_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# en-es Source Topic Precision Review",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Reviewed rows: `{summary.get('count', 0)}`",
        f"- Accepted rows: `{summary.get('accepted_count', 0)}` "
        f"({_format_percent(summary.get('accepted_rate'))})",
        f"- Rejected rows: `{summary.get('rejected_count', 0)}` "
        f"({_format_percent(summary.get('rejected_rate'))})",
        f"- Pending rows: `{summary.get('pending_count', 0)}`",
        "",
        "## Findings",
        "",
    ]
    for finding in _mapping_rows(report.get("findings")):
        lines.append(
            f"- `{finding.get('level', '')}` `{finding.get('code', '')}`: "
            f"{finding.get('message', '')}"
        )
    lines.extend(["", "## Precision By Family", ""])
    lines.extend(_precision_table(_mapping_rows(report.get("precision_by_family"))))
    lines.extend(["", "## Notable Source Labels", ""])
    source_rows = [
        row for row in _mapping_rows(report.get("precision_by_source_label")) if row.get("count", 0)
    ][:24]
    lines.extend(_precision_table(source_rows))
    lines.extend(["", "## Rejected Rows", ""])
    if not _mapping_rows(report.get("rejected_rows")):
        lines.append("- _None._")
    for row in _mapping_rows(report.get("rejected_rows")):
        manual = _as_mapping(row.get("manual_review"))
        lines.append(
            f"- `{row.get('family', '')}` `{row.get('lemma', '')}`: "
            f"`{manual.get('decision', '')}` - {manual.get('notes', '')}"
        )
    lines.extend(["", "## Review Queue", ""])
    lines.append("| ID | Family | Lemma | Sample | Difficulty | Source Labels | Decision | Notes |")
    lines.append("| --- | --- | --- | --- | ---: | --- | --- | --- |")
    for row in _mapping_rows(report.get("review_queue")):
        manual = _as_mapping(row.get("manual_review"))
        lines.append(
            "| "
            + " | ".join(
                (
                    f"`{row.get('review_id', '')}`",
                    f"`{row.get('family', '')}`",
                    f"`{row.get('lemma', '')}`",
                    f"`{row.get('sample_source', '')}`",
                    str(row.get("difficulty", "")),
                    ", ".join(_string_list(row.get("source_labels"))) or "",
                    str(manual.get("decision") or ""),
                    str(manual.get("notes") or ""),
                )
            )
            + " |"
        )
    lines.extend(["", "## Limitations", ""])
    for item in _string_list(report.get("limitations")):
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def _release_topics(
    release_readiness_payload: Mapping[str, object],
    *,
    included_statuses: Sequence[str],
) -> list[str]:
    included = {str(status) for status in included_statuses}
    topics = []
    for row in _mapping_rows(release_readiness_payload.get("topics")):
        if str(row.get("axis") or "") != "topic":
            continue
        if str(row.get("release_status") or "") not in included:
            continue
        family = str(row.get("family") or "").strip()
        if family:
            topics.append(family)
    return topics


def _resolve_frontier(
    depth_audit_payload: Mapping[str, object],
    *,
    frontier_label: str,
) -> Mapping[str, object]:
    for row in _mapping_rows(depth_audit_payload.get("frontiers")):
        if str(row.get("label") or "") == frontier_label:
            return row
    return {}


def _candidate_rows_from_family(
    *,
    family_id: str,
    family_report: Mapping[str, object],
    max_rows: int,
) -> list[dict[str, object]]:
    candidates: dict[str, dict[str, object]] = {}

    def add_row(row: Mapping[str, object], *, sample_source: str, band: str = "") -> None:
        lemma = str(row.get("lemma") or "").strip()
        if not lemma:
            return
        current = candidates.get(lemma)
        next_row = {
            "family": family_id,
            "lemma": lemma,
            "sample_source": sample_source,
            "difficulty_band": band,
            "difficulty": _round_float(row.get("difficulty")),
            "admission_weight": _round_float(row.get("admission_weight")),
            "seed_rank": row.get("seed_rank"),
            "pos_bucket": str(row.get("pos_bucket") or ""),
            "score": _round_float(row.get("score")),
            "source_labels": _source_labels(row),
        }
        if current is None or _sample_priority(sample_source) < _sample_priority(
            str(current.get("sample_source") or "")
        ):
            candidates[lemma] = next_row

    for row in _mapping_rows(family_report.get("trusted_top_examples"))[:4]:
        add_row(row, sample_source="top_example")
    for row in _mapping_rows(family_report.get("trusted_hardest_examples"))[:4]:
        add_row(row, sample_source="hardest_example")
    for band in _mapping_rows(family_report.get("trusted_bands")):
        band_label = str(band.get("band") or "")
        for row in _mapping_rows(band.get("examples"))[:2]:
            add_row(row, sample_source="band_example", band=band_label)

    rows = sorted(
        candidates.values(),
        key=lambda row: (
            _sample_priority(str(row.get("sample_source") or "")),
            str(row.get("difficulty_band") or ""),
            _float(row.get("difficulty")),
            str(row.get("lemma") or ""),
        ),
    )
    return rows[:max_rows]


def _sample_priority(source: str) -> int:
    return {"top_example": 0, "band_example": 1, "hardest_example": 2}.get(source, 9)


def _source_labels(row: Mapping[str, object]) -> list[str]:
    labels = row.get("source_labels")
    if isinstance(labels, (list, tuple)):
        return [str(label) for label in labels if str(label).strip()]
    label = str(row.get("source_label") or "").strip()
    if not label:
        return []
    return [part.strip() for part in label.split(",") if part.strip()]


def _apply_labels(
    *,
    review_queue: list[dict[str, object]],
    labels_payload: Mapping[str, object] | None,
    labels_path: Path | None,
) -> dict[str, object]:
    if not labels_payload:
        return {
            "labels_provided": False,
            "labels_json": _repo_path(labels_path),
            "labels_review_id": "",
            "labels_state": "",
            "missing_review_ids": [],
            "unknown_review_ids": [],
            "retired_review_ids": [],
            "invalid_decisions": [],
        }
    label_rows = _mapping_rows(labels_payload.get("labels"))
    labels_by_id = {str(row.get("review_id") or ""): row for row in label_rows}
    labels_by_key = {
        key: row
        for row in label_rows
        if (key := _label_key(row)) and str(row.get("decision") or "")
    }
    queue_keys = {_label_key(row) for row in review_queue if _label_key(row)}
    applied_label_ids: set[str] = set()
    missing: list[str] = []
    invalid_decisions = sorted(
        {
            str(row.get("decision") or "")
            for row in label_rows
            if str(row.get("decision") or "")
            and str(row.get("decision") or "") not in ALLOWED_DECISIONS
        }
    )
    for row in review_queue:
        row_key = _label_key(row)
        label = labels_by_key.get(row_key)
        label_match = "family_lemma"
        id_label = labels_by_id.get(str(row.get("review_id") or ""))
        if not label and id_label:
            id_label_key = _label_key(id_label)
            if not id_label_key or id_label_key == row_key:
                label = id_label
                label_match = "review_id"
        if not label:
            missing.append(str(row.get("review_id") or ""))
            continue
        applied_label_ids.add(str(label.get("review_id") or ""))
        manual = _as_mapping(row.get("manual_review"))
        row["manual_review"] = {
            **manual,
            "state": str(labels_payload.get("state") or "agent_labeled_pending_user_approval"),
            "decision": str(label.get("decision") or ""),
            "reviewer": str(labels_payload.get("reviewer") or ""),
            "reviewed_at": str(labels_payload.get("reviewed_at") or ""),
            "label_source": _repo_path(labels_path) or "",
            "label_match": label_match,
            "notes": str(label.get("notes") or ""),
        }
    unknown = sorted(
        str(row.get("review_id") or "")
        for row in label_rows
        if not str(row.get("review_id") or "") and not _label_key(row)
    )
    retired = sorted(
        {
            str(row.get("review_id") or "")
            for row in label_rows
            if str(row.get("review_id") or "")
            and str(row.get("review_id") or "") not in applied_label_ids
            and _label_key(row) not in queue_keys
        }
    )
    return {
        "labels_provided": True,
        "labels_json": _repo_path(labels_path),
        "labels_review_id": str(labels_payload.get("review_id") or ""),
        "labels_state": str(labels_payload.get("state") or ""),
        "missing_review_ids": sorted(missing),
        "unknown_review_ids": unknown,
        "retired_review_ids": retired,
        "invalid_decisions": invalid_decisions,
    }


def _summary(
    review_queue: Sequence[Mapping[str, object]],
    findings: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    overall = _precision_row("overall", review_queue)
    pending = sum(
        1
        for row in review_queue
        if not str(_as_mapping(row.get("manual_review")).get("decision") or "")
    )
    return {
        **overall,
        "pending_count": pending,
        "family_count": len({str(row.get("family") or "") for row in review_queue}),
        "finding_counts": dict(Counter(str(row.get("level") or "") for row in findings)),
        "issues": [row.get("code") for row in findings if row.get("level") == "FAIL"],
        "warnings": [row.get("code") for row in findings if row.get("level") == "WARN"],
    }


def _precision_by(rows: Sequence[Mapping[str, object]], key: str) -> list[dict[str, object]]:
    grouped: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for row in rows:
        if key == "source_label":
            labels = _string_list(row.get("source_labels")) or [""]
            for label in labels:
                grouped[label].append(row)
        else:
            grouped[str(row.get(key) or "")].append(row)
    return sorted(
        (_precision_row(label, values) for label, values in grouped.items()),
        key=lambda item: (-int(item["count"]), str(item["label"])),
    )


def _rejected_rows(rows: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    return [
        dict(row)
        for row in rows
        if str(_as_mapping(row.get("manual_review")).get("decision") or "") in REJECT_DECISIONS
    ]


def _precision_row(label: str, rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    decisions = Counter(
        str(_as_mapping(row.get("manual_review")).get("decision") or "") for row in rows
    )
    accepted = sum(decisions.get(decision, 0) for decision in ACCEPT_DECISIONS)
    rejected = sum(decisions.get(decision, 0) for decision in REJECT_DECISIONS)
    pending = decisions.get("", 0)
    count = len(rows)
    return {
        "label": label,
        "count": count,
        "accepted_count": accepted,
        "accepted_rate": _ratio(accepted, count),
        "pending_count": pending,
        "strong_count": decisions.get("accept_strong_topic", 0),
        "light_count": decisions.get("accept_light_topic", 0),
        "rejected_count": rejected,
        "rejected_rate": _ratio(rejected, count),
        "wrong_topic_count": decisions.get("reject_wrong_topic", 0),
        "secondary_or_obscure_count": decisions.get("reject_secondary_or_obscure_sense", 0),
        "uncertain_count": decisions.get("uncertain_needs_source_check", 0),
        "decision_counts": dict(sorted(decisions.items())),
    }


def _findings(
    *,
    review_queue: Sequence[Mapping[str, object]],
    frontier: Mapping[str, object],
    release_topics: Sequence[str],
    label_result: Mapping[str, object],
) -> list[dict[str, object]]:
    findings = []
    if frontier.get("exists"):
        findings.append(_finding("PASS", "frontier_available", "Depth-audit frontier exists."))
    else:
        findings.append(_finding("FAIL", "frontier_missing", "Depth-audit frontier is missing."))
    if release_topics:
        findings.append(
            _finding("PASS", "release_topics_selected", "Release-candidate topics were selected.")
        )
    else:
        findings.append(
            _finding("FAIL", "release_topics_missing", "No release-candidate topics were selected.")
        )
    if review_queue:
        findings.append(_finding("PASS", "review_rows_present", "Review rows were generated."))
    else:
        findings.append(_finding("FAIL", "review_rows_missing", "No review rows were generated."))
    if label_result.get("labels_provided"):
        unknown = label_result.get("unknown_review_ids") or []
        invalid = label_result.get("invalid_decisions") or []
        if unknown or invalid:
            findings.append(
                _finding("FAIL", "manual_labels_invalid", "Label input has unresolved issues.")
            )
        else:
            findings.append(_finding("PASS", "manual_labels_applied", "Manual labels applied."))
        unlabeled = [
            row
            for row in review_queue
            if not str(_as_mapping(row.get("manual_review")).get("decision") or "")
        ]
        if unlabeled:
            findings.append(
                _finding("FAIL", "review_rows_unlabeled", "Some review rows are unlabeled.")
            )
        else:
            overall = _precision_row("overall", review_queue)
            if int(overall.get("accepted_count") or 0) >= int(overall.get("rejected_count") or 0):
                findings.append(
                    _finding(
                        "PASS",
                        "accepted_majority",
                        "Accepted rows outnumber rejects in the reviewed sample.",
                    )
                )
            else:
                findings.append(
                    _finding(
                        "WARN",
                        "rejected_majority",
                        "Rejects outnumber accepts in the reviewed sample.",
                    )
                )
            if int(overall.get("rejected_count") or 0) > 0:
                findings.append(
                    _finding(
                        "WARN",
                        "source_false_positive_classes_present",
                        "Rejects identify source-label false-positive classes before promotion.",
                    )
                )
            noisy_families = [
                str(row.get("label") or "")
                for row in _precision_by(review_queue, "family")
                if float(row.get("rejected_rate") or 0) >= 0.4
            ]
            if noisy_families:
                findings.append(
                    _finding(
                        "WARN",
                        "family_precision_review_needed",
                        "High sample reject rates need review for: " + ", ".join(noisy_families),
                    )
                )
    else:
        findings.append(
            _finding(
                "WARN",
                "manual_labels_absent",
                "Review rows are pending labels; precision is not available yet.",
            )
        )
    return findings


def _precision_table(rows: Sequence[Mapping[str, object]]) -> list[str]:
    lines = [
        "| Label | Rows | Accepted | Strong | Light | Rejected | Reject Rate |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            f"| `{row.get('label', '')}` | {row.get('count', 0)} | "
            f"{row.get('accepted_count', 0)} | {row.get('strong_count', 0)} | "
            f"{row.get('light_count', 0)} | {row.get('rejected_count', 0)} | "
            f"{_format_percent(row.get('rejected_rate'))} |"
        )
    return lines


def _load_json(path: Path) -> Mapping[str, object]:
    payload = json.loads(_resolve_path(path).read_text(encoding="utf-8"))
    return _as_mapping(payload)


def _load_json_if_exists(path: Path | None) -> Mapping[str, object] | None:
    if path is None or not path.exists():
        return None
    return _load_json(path)


def _resolve_path(path: Path) -> Path:
    candidate = Path(path).expanduser()
    return candidate if candidate.is_absolute() else PROJECT_ROOT / candidate


def _repo_path(path: Path | None) -> str | None:
    if path is None:
        return None
    resolved = _resolve_path(path)
    try:
        return str(resolved.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(resolved)


def _mapping_rows(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, list):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _string_list(value: object) -> list[str]:
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, (list, tuple)):
        return [str(item) for item in value if str(item).strip()]
    return []


def _label_key(row: Mapping[str, object]) -> tuple[str, str]:
    family = str(row.get("family") or "").strip()
    lemma = str(row.get("lemma") or "").strip().lower()
    return (family, lemma) if family and lemma else ("", "")


def _round_float(value: object) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return round(parsed, 6) if parsed == parsed else None


def _float(value: object) -> float:
    parsed = _round_float(value)
    return parsed if parsed is not None else 0.0


def _ratio(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 6) if denominator else 0.0


def _format_percent(value: object) -> str:
    try:
        return f"{float(value) * 100:.1f}%"
    except (TypeError, ValueError):
        return "0.0%"


def _finding(level: str, code: str, message: str) -> dict[str, object]:
    return {"level": level, "code": code, "message": message}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


if __name__ == "__main__":
    raise SystemExit(main())
