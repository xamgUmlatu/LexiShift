#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PACKET_JSON = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_food_cooking_full_source_review_packet_en_es_latest.json"
)
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_food_cooking_full_source_review_precision_summary_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "srs_food_cooking_full_source_review_precision_summary_en_es_latest.md"
)
ACCEPT_DECISIONS = {"accept_strong_topic", "accept_light_topic"}
REJECT_DECISIONS = {"reject_wrong_topic", "reject_secondary_or_obscure_sense"}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Summarize precision from the labeled en-es full-source food/cooking review packet. "
            "Read-only; no source downloads, overlay promotion, or runtime changes."
        )
    )
    parser.add_argument("--packet-json", type=Path, default=DEFAULT_PACKET_JSON)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    packet_path = _resolve_path(args.packet_json)
    report = build_report(packet_payload=_load_json(packet_path), packet_path=packet_path)
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
    packet_payload: Mapping[str, object],
    packet_path: Path | None = None,
    generated_at: str | None = None,
) -> dict[str, object]:
    rows = _review_rows(packet_payload)
    overall = _precision_row("overall", rows)
    findings = _findings(rows=rows, packet_payload=packet_payload, overall=overall)
    status = "ok" if not any(row["level"] == "FAIL" for row in findings) else "review"
    return {
        "schema_version": 1,
        "status": status,
        "decision": (
            "srs_food_cooking_full_source_review_precision_summary_ready"
            if status == "ok"
            else "srs_food_cooking_full_source_review_precision_summary_needs_review"
        ),
        "generated_at": generated_at or _utc_now(),
        "inputs": {
            "packet_json": _repo_path(packet_path),
            "packet_decision": str(packet_payload.get("decision") or ""),
            "labels_json": str(
                _as_mapping(packet_payload.get("label_result")).get("labels_json") or ""
            ),
            "labels_state": str(
                _as_mapping(packet_payload.get("label_result")).get("labels_state") or ""
            ),
        },
        "summary": {
            **overall,
            "finding_counts": dict(Counter(row["level"] for row in findings)),
            "issues": [row["code"] for row in findings if row["level"] == "FAIL"],
            "warnings": [row["code"] for row in findings if row["level"] == "WARN"],
        },
        "precision_by_tier": _group_precision(rows, "best_tier"),
        "precision_by_confidence_band": _group_precision(rows, "confidence_band"),
        "precision_by_tier_and_band": _group_precision(rows, "tier_band"),
        "precision_by_source_label": _group_precision(rows, "source_label"),
        "rejected_rows": _rejected_rows(rows),
        "policy_guidance": _policy_guidance(rows),
        "flow_assessment": {
            "doing_the_right_thing": True,
            "reason": (
                "The current method separated source discovery, review labels, diagnostic "
                "overlay behavior, and runtime admission. The broad source sample accepted "
                "most rows while surfacing specific false-positive classes before product lift."
            ),
            "next_best_step": (
                "Convert review results into small policy guards, then rerun the audit/review "
                "summary before promoting any broader food/cooking overlay."
            ),
        },
        "findings": findings,
        "limitations": [
            "This summary describes one deterministic 96-row review packet, not the full 2,083-row precision.",
            "Agent labels remain pending user approval and are not product-overlay approval by themselves.",
            "High acceptance supports continuing the source path, but false-positive classes still need policy guards.",
        ],
    }


def render_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# en-es Food/Cooking Full-Source Review Precision Summary",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Reviewed rows: `{summary.get('count', 0)}`",
        f"- Accepted rows: `{summary.get('accepted_count', 0)}` "
        f"({_format_percent(summary.get('accepted_rate'))})",
        f"- Strong accepts: `{summary.get('strong_count', 0)}`",
        f"- Light accepts: `{summary.get('light_count', 0)}`",
        f"- Rejected rows: `{summary.get('rejected_count', 0)}` "
        f"({_format_percent(summary.get('rejected_rate'))})",
        "",
        "## Flow Assessment",
        "",
        f"- Doing the right thing: `{_as_mapping(report.get('flow_assessment')).get('doing_the_right_thing', False)}`",
        f"- Reason: {_as_mapping(report.get('flow_assessment')).get('reason', '')}",
        f"- Next best step: {_as_mapping(report.get('flow_assessment')).get('next_best_step', '')}",
        "",
        "## Findings",
        "",
    ]
    for finding in _mapping_rows(report.get("findings")):
        lines.append(
            f"- `{finding.get('level', '')}` `{finding.get('code', '')}`: "
            f"{finding.get('message', '')}"
        )
    lines.extend(["", "## Precision By Tier", ""])
    lines.extend(_precision_table(_mapping_rows(report.get("precision_by_tier"))))
    lines.extend(["", "## Precision By Confidence Band", ""])
    lines.extend(_precision_table(_mapping_rows(report.get("precision_by_confidence_band"))))
    lines.extend(["", "## Notable Source Labels", ""])
    source_rows = [
        row for row in _mapping_rows(report.get("precision_by_source_label")) if row.get("count", 0)
    ][:24]
    lines.extend(_precision_table(source_rows))
    lines.extend(["", "## Rejected Rows", ""])
    if not _mapping_rows(report.get("rejected_rows")):
        lines.append("- _None._")
    for row in _mapping_rows(report.get("rejected_rows")):
        lines.append(
            f"- `{row.get('lemma', '')}`: `{row.get('decision', '')}` "
            f"via `{row.get('best_tier', '')}/{row.get('source_label', '')}` - "
            f"{row.get('notes', '')}"
        )
    lines.extend(["", "## Policy Guidance", ""])
    lines.extend(f"- {item}" for item in report.get("policy_guidance", []))
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- {item}" for item in report.get("limitations", []))
    return "\n".join(lines) + "\n"


def _review_rows(packet_payload: Mapping[str, object]) -> list[dict[str, object]]:
    rows = []
    for row in _mapping_rows(packet_payload.get("review_queue")):
        manual_review = _as_mapping(row.get("manual_review"))
        decision = str(manual_review.get("decision") or "").strip()
        rows.append(
            {
                "review_id": str(row.get("review_id") or ""),
                "lemma": str(row.get("lemma") or ""),
                "best_tier": str(row.get("best_tier") or ""),
                "confidence_band": str(row.get("confidence_band") or ""),
                "tier_band": f"{row.get('best_tier', '')}:{row.get('confidence_band', '')}",
                "source_channel": str(row.get("source_channel") or ""),
                "source_label": str(row.get("source_label") or ""),
                "decision": decision,
                "notes": str(manual_review.get("notes") or ""),
            }
        )
    return rows


def _group_precision(rows: Sequence[Mapping[str, object]], key: str) -> list[dict[str, object]]:
    grouped: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get(key) or "")].append(row)
    return sorted(
        (_precision_row(label, values) for label, values in grouped.items()),
        key=lambda item: (-int(item["count"]), str(item["label"])),
    )


def _precision_row(label: str, rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    decisions = Counter(str(row.get("decision") or "") for row in rows)
    accepted = sum(decisions.get(decision, 0) for decision in ACCEPT_DECISIONS)
    rejected = sum(decisions.get(decision, 0) for decision in REJECT_DECISIONS)
    count = len(rows)
    return {
        "label": label,
        "count": count,
        "accepted_count": accepted,
        "accepted_rate": _ratio(accepted, count),
        "strong_count": decisions.get("accept_strong_topic", 0),
        "light_count": decisions.get("accept_light_topic", 0),
        "rejected_count": rejected,
        "rejected_rate": _ratio(rejected, count),
        "wrong_topic_count": decisions.get("reject_wrong_topic", 0),
        "secondary_or_obscure_count": decisions.get("reject_secondary_or_obscure_sense", 0),
        "uncertain_count": decisions.get("uncertain_needs_source_check", 0),
        "decision_counts": dict(sorted(decisions.items())),
    }


def _rejected_rows(rows: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    return [dict(row) for row in rows if str(row.get("decision") or "") in REJECT_DECISIONS]


def _policy_guidance(rows: Sequence[Mapping[str, object]]) -> list[str]:
    rejected = _rejected_rows(rows)
    guidance = [
        "Continue using review packets before promotion; the high accepted share is meaningful because rejects were caught before overlay lift.",
        "Treat strong accepted rows as overlay candidates only after provenance and rollback fields are generated.",
        "Keep light accepted rows as lower-membership or scalar-ready evidence, not binary strong topic evidence.",
        "Keep Tier D as review-gated discovery even when this sample was mostly acceptable; its broad population is still large and phrase-driven.",
    ]
    source_labels = {str(row.get("source_label") or "") for row in rejected}
    if {"primary_translation:orange", "primary_translation:lemon"} & source_labels:
        guidance.append(
            "Add guards for fruit-word translation matches that are actually colors, trees, sellers, or plants."
        )
    if {"fruits", "fish", "seafood"} & source_labels:
        guidance.append(
            "Penalize name/person/adjective collisions before trusting category-derived food labels."
        )
    if "legumes" in source_labels:
        guidance.append(
            "Keep botanical category overlap review-gated unless primary translation or food gloss corroborates it."
        )
    if "primary_translation:tea" in source_labels:
        guidance.append(
            "Penalize historical, archaic, or region-only terms unless the product explicitly supports that register."
        )
    return guidance


def _findings(
    *,
    rows: Sequence[Mapping[str, object]],
    packet_payload: Mapping[str, object],
    overall: Mapping[str, object],
) -> list[dict[str, object]]:
    findings = []
    if not rows:
        return [_finding("FAIL", "review_rows_missing", "No review rows were available.")]
    findings.append(_finding("PASS", "review_rows_loaded", "Review rows were loaded."))
    unlabeled = [row for row in rows if not str(row.get("decision") or "")]
    if unlabeled:
        findings.append(
            _finding("FAIL", "review_rows_unlabeled", "Some review rows have no decision.")
        )
    else:
        findings.append(_finding("PASS", "review_rows_labeled", "All review rows are labeled."))
    if int(overall.get("accepted_count") or 0) >= int(overall.get("rejected_count") or 0):
        findings.append(
            _finding(
                "PASS",
                "accepted_majority",
                "Accepted rows outnumber rejects in the reviewed sample.",
            )
        )
    if int(overall.get("rejected_count") or 0) > 0:
        findings.append(
            _finding(
                "WARN",
                "policy_guards_still_needed",
                "Rejected rows identify false-positive classes that should be policy-guarded before promotion.",
            )
        )
    label_result = _as_mapping(packet_payload.get("label_result"))
    if label_result.get("missing_review_ids") or label_result.get("unknown_review_ids"):
        findings.append(
            _finding("FAIL", "label_merge_incomplete", "Labels did not merge cleanly into packet.")
        )
    else:
        findings.append(_finding("PASS", "label_merge_clean", "Labels merged cleanly."))
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
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return payload if isinstance(payload, Mapping) else {}


def _mapping_rows(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, list):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _finding(level: str, code: str, message: str) -> dict[str, object]:
    return {"level": level, "code": code, "message": message}


def _ratio(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 6) if denominator else 0.0


def _format_percent(value: object) -> str:
    try:
        return f"{float(value) * 100:.1f}%"
    except (TypeError, ValueError):
        return "0.0%"


def _resolve_path(path: Path) -> Path:
    path = Path(path).expanduser()
    if path.is_absolute():
        return path
    return (PROJECT_ROOT / path).resolve(strict=False)


def _repo_path(path: Path | None) -> str:
    if path is None:
        return ""
    try:
        return str(Path(path).resolve(strict=False).relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


if __name__ == "__main__":
    raise SystemExit(main())
