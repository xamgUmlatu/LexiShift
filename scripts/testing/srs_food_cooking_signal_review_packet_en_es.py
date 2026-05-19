#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEST_OUTPUTS_ROOT = PROJECT_ROOT / "docs" / "test_outputs"
DEFAULT_AUDIT_JSON = (
    TEST_OUTPUTS_ROOT / "srs_food_cooking_existing_signal_audit_en_es_current_latest.json"
)
DEFAULT_JSON_OUT = (
    TEST_OUTPUTS_ROOT / "srs_food_cooking_signal_review_packet_en_es_current_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    TEST_OUTPUTS_ROOT / "srs_food_cooking_signal_review_packet_en_es_current_latest.md"
)
DEFAULT_LABELS_JSON = (
    PROJECT_ROOT
    / "docs"
    / "test_inputs"
    / "srs_food_cooking_signal_review_labels_en_es_current.json"
)
DEFAULT_SAMPLE_PER_CELL = 8
DEFAULT_MAX_ROWS = 64
REVIEW_DECISIONS = (
    "accept_strong_topic",
    "accept_light_topic",
    "reject_wrong_topic",
    "reject_secondary_or_obscure_sense",
    "uncertain_needs_source_check",
)
BAND_PRIORITY = {"review": 0, "inventory": 1, "medium": 2, "high": 3}
TIER_PRIORITY = {"D": 0, "C": 1, "B": 2, "A": 3}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a deterministic manual review packet for en-es food/cooking "
            "topic-signal candidates. This does not promote any overlay."
        )
    )
    parser.add_argument("--audit-json", type=Path, default=DEFAULT_AUDIT_JSON)
    parser.add_argument("--sample-per-cell", type=int, default=DEFAULT_SAMPLE_PER_CELL)
    parser.add_argument("--max-rows", type=int, default=DEFAULT_MAX_ROWS)
    parser.add_argument("--labels-json", type=Path, default=DEFAULT_LABELS_JSON)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    audit_path = _resolve_path(args.audit_json)
    labels_path = _resolve_path(args.labels_json)
    report = build_review_packet(
        audit_payload=_load_json(audit_path),
        audit_path=audit_path,
        labels_payload=_load_optional_json(labels_path),
        labels_path=labels_path,
        sample_per_cell=max(1, int(args.sample_per_cell)),
        max_rows=max(1, int(args.max_rows)),
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


def build_review_packet(
    *,
    audit_payload: Mapping[str, object],
    audit_path: Path | None = None,
    labels_payload: Mapping[str, object] | None = None,
    labels_path: Path | None = None,
    sample_per_cell: int = DEFAULT_SAMPLE_PER_CELL,
    max_rows: int = DEFAULT_MAX_ROWS,
    generated_at: str | None = None,
) -> dict[str, object]:
    candidates, full_inventory_used = _candidate_rows(audit_payload)
    cells = _group_by_cell(candidates)
    selected = _select_review_rows(
        candidates, cells, sample_per_cell=sample_per_cell, max_rows=max_rows
    )
    review_queue = [
        _review_row(index=index, row=row) for index, row in enumerate(selected, start=1)
    ]
    label_result = _apply_labels(
        review_queue=review_queue,
        labels_payload=labels_payload,
        labels_path=labels_path,
    )
    findings = _findings(
        candidates=candidates,
        review_queue=review_queue,
        label_result=label_result,
    )
    status = "ok" if not any(row["level"] == "FAIL" for row in findings) else "review"
    return {
        "schema_version": 1,
        "status": status,
        "decision": (
            "srs_food_cooking_signal_review_packet_ready"
            if status == "ok"
            else "srs_food_cooking_signal_review_packet_needs_review"
        ),
        "generated_at": generated_at or _utc_now(),
        "inputs": {
            "audit_json": _repo_path(audit_path),
            "audit_decision": str(audit_payload.get("decision") or ""),
            "audit_generated_at": str(audit_payload.get("generated_at") or ""),
            "labels_json": _repo_path(labels_path),
            "labels_review_id": str(label_result.get("labels_review_id") or ""),
            "labels_state": str(label_result.get("labels_state") or ""),
            "sample_per_cell": int(sample_per_cell),
            "max_rows": int(max_rows),
        },
        "manual_review_policy": {
            "state": "agent_labeled_pending_user_approval"
            if label_result.get("labels_provided")
            else "pending_user_review",
            "allowed_decisions": list(REVIEW_DECISIONS),
            "promotion_rule": (
                "Labels calibrate source-signal quality only. No food/cooking candidate "
                "is product-ready until it is promoted through a reviewed overlay/policy artifact."
            ),
        },
        "summary": _summary(
            candidates=candidates,
            review_queue=review_queue,
            cells=cells,
            full_inventory_used=full_inventory_used,
            label_result=label_result,
        ),
        "cell_inventory": _cell_inventory(cells, review_queue),
        "review_queue": review_queue,
        "label_result": label_result,
        "findings": findings,
        "limitations": [
            "The packet reviews existing audit candidates only; it does not collect new food data.",
            "The current food/cooking audit is intentionally conservative and not a final recall target.",
            "Rows are selected deterministically by review cell and stable hash, not by model judgment.",
            "Pending or agent labels are QA surfaces and must not be treated as approved overlay data.",
        ],
    }


def _candidate_rows(audit_payload: Mapping[str, object]) -> tuple[list[dict[str, object]], bool]:
    family = _as_mapping(audit_payload.get("family"))
    inventory = _mapping_rows(family.get("candidate_inventory"))
    full_inventory_used = bool(inventory)
    if not inventory:
        inventory = _dedupe_candidate_rows(
            [
                *_mapping_rows(family.get("top_candidates")),
                *_mapping_rows(family.get("review_candidates")),
            ]
        )
    rows = []
    for row in inventory:
        evidence = _mapping_rows(row.get("evidence"))
        best_evidence = evidence[0] if evidence else {}
        rows.append(
            {
                "family": str(row.get("family") or family.get("family") or "food_cooking"),
                "lemma": str(row.get("lemma") or ""),
                "confidence": _safe_float(row.get("confidence")),
                "confidence_band": str(row.get("confidence_band") or ""),
                "best_tier": str(row.get("best_tier") or ""),
                "review_required": bool(row.get("review_required")),
                "source_channel": str(best_evidence.get("source_channel") or ""),
                "source_label": str(best_evidence.get("source_label") or ""),
                "evidence_type": str(best_evidence.get("evidence_type") or ""),
                "snippet": str(best_evidence.get("snippet") or ""),
                "evidence": evidence,
            }
        )
    rows.sort(key=lambda item: (str(item["family"]), str(item["lemma"])))
    return rows, full_inventory_used


def _group_by_cell(rows: Sequence[Mapping[str, object]]) -> dict[str, list[dict[str, object]]]:
    cells: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        cells[_review_cell(row)].append(dict(row))
    for cell_rows in cells.values():
        cell_rows.sort(key=_stable_candidate_key)
    return dict(cells)


def _select_review_rows(
    candidates: Sequence[dict[str, object]],
    cells: Mapping[str, Sequence[dict[str, object]]],
    *,
    sample_per_cell: int,
    max_rows: int,
) -> list[dict[str, object]]:
    if len(candidates) <= max_rows:
        return sorted((dict(row) for row in candidates), key=_review_sort_key)
    selected: list[dict[str, object]] = []
    for round_index in range(sample_per_cell):
        for cell in sorted(cells, key=_cell_sort_key):
            if round_index >= len(cells[cell]):
                continue
            if len(selected) >= max_rows:
                return selected
            selected.append(dict(cells[cell][round_index]))
    return selected


def _review_row(index: int, row: Mapping[str, object]) -> dict[str, object]:
    return {
        "review_id": f"srs-food-{index:03d}",
        "review_cell": _review_cell(row),
        "family": row.get("family"),
        "lemma": row.get("lemma"),
        "confidence": row.get("confidence"),
        "confidence_band": row.get("confidence_band"),
        "best_tier": row.get("best_tier"),
        "review_required_by_policy": row.get("review_required"),
        "source_channel": row.get("source_channel"),
        "source_label": row.get("source_label"),
        "evidence_type": row.get("evidence_type"),
        "snippet": row.get("snippet"),
        "evidence": row.get("evidence"),
        "manual_review": {
            "state": "pending_user_review",
            "decision": "",
            "notes": "",
            "allowed_decisions": list(REVIEW_DECISIONS),
        },
    }


def render_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# en-es Food/Cooking Signal Review Packet",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Candidate universe: `{summary.get('candidate_count', 0)}`",
        f"- Review rows: `{summary.get('review_queue_count', 0)}`",
        f"- Review cells covered: `{summary.get('selected_cell_count', 0)}` / "
        f"`{summary.get('cell_count', 0)}`",
        f"- Labeled rows: `{summary.get('labeled_row_count', 0)}`",
        "",
        "## Manual Decisions",
        "",
    ]
    decision_counts = _as_mapping(summary.get("manual_decision_counts"))
    lines.extend(
        f"- `{decision}`: `{decision_counts.get(decision, 0)}`" for decision in REVIEW_DECISIONS
    )
    lines.extend(["", "## Cell Coverage", ""])
    lines.append("| Cell | Candidates | Selected |")
    lines.append("| --- | ---: | ---: |")
    for cell in _mapping_rows(report.get("cell_inventory")):
        lines.append(
            f"| `{cell.get('cell', '')}` | {cell.get('candidate_count', 0)} | "
            f"{cell.get('selected_count', 0)} |"
        )
    lines.extend(["", "## Manual Review Queue", ""])
    lines.append(
        "| ID | Lemma | Tier | Band | Source | Score | Review? | Evidence | Decision | Notes |"
    )
    lines.append("| --- | --- | --- | --- | --- | ---: | --- | --- | --- | --- |")
    for row in _mapping_rows(report.get("review_queue")):
        manual_review = _as_mapping(row.get("manual_review"))
        lines.append(
            f"| `{row.get('review_id', '')}` | `{row.get('lemma', '')}` | "
            f"`{row.get('best_tier', '')}` | `{row.get('confidence_band', '')}` | "
            f"`{row.get('source_channel', '')}:{row.get('source_label', '')}` | "
            f"{row.get('confidence', 0)} | `{row.get('review_required_by_policy', '')}` | "
            f"{_evidence_cell(row)} | "
            f"{_markdown_cell(str(manual_review.get('decision') or ''))} | "
            f"{_markdown_cell(str(manual_review.get('notes') or ''))} |"
        )
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- {item}" for item in report.get("limitations", []))
    return "\n".join(lines) + "\n"


def _summary(
    *,
    candidates: Sequence[Mapping[str, object]],
    review_queue: Sequence[Mapping[str, object]],
    cells: Mapping[str, Sequence[Mapping[str, object]]],
    full_inventory_used: bool,
    label_result: Mapping[str, object],
) -> dict[str, object]:
    selected_cells = {str(row.get("review_cell") or "") for row in review_queue}
    return {
        "candidate_count": len(candidates),
        "review_queue_count": len(review_queue),
        "cell_count": len(cells),
        "selected_cell_count": len(selected_cells),
        "full_candidate_inventory_used": full_inventory_used,
        "candidate_counts_by_tier": _counts(candidates, "best_tier"),
        "candidate_counts_by_band": _counts(candidates, "confidence_band"),
        "review_rows_by_tier": _counts(review_queue, "best_tier"),
        "review_rows_by_band": _counts(review_queue, "confidence_band"),
        "manual_decision_counts": _manual_review_counts(review_queue, "decision"),
        "manual_state_counts": _manual_review_counts(review_queue, "state"),
        "labeled_row_count": sum(
            1
            for row in review_queue
            if str(_as_mapping(row.get("manual_review")).get("decision") or "")
        ),
        "label_missing_count": len(_string_list(label_result.get("missing_review_ids"))),
    }


def _cell_inventory(
    cells: Mapping[str, Sequence[Mapping[str, object]]],
    review_queue: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    selected_counts = Counter(str(row.get("review_cell") or "") for row in review_queue)
    return [
        {
            "cell": cell,
            "candidate_count": len(rows),
            "selected_count": selected_counts.get(cell, 0),
        }
        for cell, rows in sorted(cells.items(), key=lambda item: _cell_sort_key(item[0]))
    ]


def _findings(
    *,
    candidates: Sequence[Mapping[str, object]],
    review_queue: Sequence[Mapping[str, object]],
    label_result: Mapping[str, object],
) -> list[dict[str, object]]:
    findings = []
    if candidates:
        findings.append(_finding("PASS", "candidate_universe_present", "Audit candidates loaded."))
    else:
        findings.append(_finding("FAIL", "candidate_universe_empty", "No audit candidates loaded."))
    if review_queue:
        findings.append(_finding("PASS", "review_queue_present", "Manual review queue generated."))
    else:
        findings.append(_finding("FAIL", "review_queue_empty", "Manual review queue is empty."))
    if len(review_queue) == len(candidates):
        findings.append(
            _finding(
                "PASS",
                "full_candidate_universe_selected",
                "Every current food/cooking candidate is included for review.",
            )
        )

    labels_provided = bool(label_result.get("labels_provided"))
    if not labels_provided:
        if all(
            _as_mapping(row.get("manual_review")).get("state") == "pending_user_review"
            for row in review_queue
        ):
            findings.append(
                _finding(
                    "PASS",
                    "manual_labels_pending",
                    "All selected rows remain pending user review.",
                )
            )
        else:
            findings.append(
                _finding(
                    "FAIL",
                    "manual_labels_not_pending",
                    "Selected rows are labeled but no label input was provided.",
                )
            )
        return findings

    invalid_keys = (
        "missing_review_ids",
        "unknown_review_ids",
        "duplicate_review_ids",
        "invalid_decision_review_ids",
        "mismatched_review_ids",
    )
    invalid_values = {
        key: _string_list(label_result.get(key))
        for key in invalid_keys
        if _string_list(label_result.get(key))
    }
    if invalid_values:
        findings.append(
            _finding(
                "FAIL",
                "manual_labels_invalid",
                f"Label input has unresolved issues: {invalid_values}",
            )
        )
    else:
        findings.append(
            _finding("PASS", "manual_labels_applied", "Labels were applied to review rows.")
        )
    return findings


def _apply_labels(
    *,
    review_queue: Sequence[dict[str, object]],
    labels_payload: Mapping[str, object] | None,
    labels_path: Path | None,
) -> dict[str, object]:
    labels = _mapping_rows(labels_payload.get("labels") if labels_payload else None)
    result: dict[str, object] = {
        "labels_provided": bool(labels),
        "labels_json": _repo_path(labels_path),
        "labels_review_id": str(labels_payload.get("review_id") or "") if labels_payload else "",
        "labels_state": str(labels_payload.get("state") or "") if labels_payload else "",
        "provided_label_count": len(labels),
        "applied_label_count": 0,
        "missing_review_ids": [],
        "unknown_review_ids": [],
        "duplicate_review_ids": [],
        "invalid_decision_review_ids": [],
        "mismatched_review_ids": [],
    }
    if not labels:
        return result

    review_by_id = {str(row.get("review_id") or ""): row for row in review_queue}
    labels_by_id: dict[str, Mapping[str, object]] = {}
    invalid_decision_ids: list[str] = []
    duplicate_ids: list[str] = []
    mismatched_ids: list[str] = []
    for label in labels:
        review_id = str(label.get("review_id") or "")
        if not review_id:
            invalid_decision_ids.append("(missing review_id)")
            continue
        if review_id in labels_by_id:
            duplicate_ids.append(review_id)
            continue
        labels_by_id[review_id] = label
        if str(label.get("decision") or "") not in REVIEW_DECISIONS:
            invalid_decision_ids.append(review_id)

    reviewer = str(labels_payload.get("reviewer") or "") if labels_payload else ""
    reviewed_at = str(labels_payload.get("reviewed_at") or "") if labels_payload else ""
    default_state = (
        str(labels_payload.get("state") or "agent_labeled_pending_user_approval")
        if labels_payload
        else "agent_labeled_pending_user_approval"
    )
    applied_count = 0
    for review_id, row in review_by_id.items():
        label = labels_by_id.get(review_id)
        if label is None or review_id in invalid_decision_ids:
            continue
        mismatches = [
            key
            for key in ("family", "lemma")
            if label.get(key) is not None and str(label.get(key)) != str(row.get(key) or "")
        ]
        if mismatches:
            mismatched_ids.append(f"{review_id}:{','.join(mismatches)}")
            continue
        manual_review = dict(_as_mapping(row.get("manual_review")))
        manual_review.update(
            {
                "state": str(label.get("state") or default_state),
                "decision": str(label.get("decision") or ""),
                "notes": str(label.get("notes") or ""),
                "reviewer": reviewer,
                "reviewed_at": reviewed_at,
                "label_source": _repo_path(labels_path),
            }
        )
        row["manual_review"] = manual_review
        applied_count += 1

    result.update(
        {
            "applied_label_count": applied_count,
            "missing_review_ids": sorted(set(review_by_id) - set(labels_by_id)),
            "unknown_review_ids": sorted(set(labels_by_id) - set(review_by_id)),
            "duplicate_review_ids": sorted(set(duplicate_ids)),
            "invalid_decision_review_ids": sorted(set(invalid_decision_ids)),
            "mismatched_review_ids": sorted(set(mismatched_ids)),
        }
    )
    return result


def _review_cell(row: Mapping[str, object]) -> str:
    return "|".join(
        [
            str(row.get("family") or ""),
            f"tier={row.get('best_tier') or ''}",
            f"band={row.get('confidence_band') or ''}",
            f"review={bool(row.get('review_required'))}",
            f"source={row.get('source_label') or ''}",
        ]
    )


def _cell_sort_key(cell: str) -> tuple[object, ...]:
    parts = dict(part.split("=", 1) for part in cell.split("|")[1:] if "=" in part)
    family = cell.split("|", 1)[0]
    band = parts.get("band", "")
    tier = parts.get("tier", "")
    review = parts.get("review", "")
    source = parts.get("source", "")
    return (
        family,
        0 if review == "True" else 1,
        BAND_PRIORITY.get(band, 99),
        TIER_PRIORITY.get(tier, 99),
        source,
        cell,
    )


def _review_sort_key(row: Mapping[str, object]) -> tuple[object, ...]:
    return (*_cell_sort_key(_review_cell(row)), _stable_candidate_key(row))


def _stable_candidate_key(row: Mapping[str, object]) -> str:
    seed = "|".join(
        [
            str(row.get("family") or ""),
            str(row.get("lemma") or ""),
            str(row.get("best_tier") or ""),
            str(row.get("confidence_band") or ""),
            str(row.get("source_label") or ""),
        ]
    )
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()


def _dedupe_candidate_rows(rows: Sequence[Mapping[str, object]]) -> list[Mapping[str, object]]:
    seen: set[tuple[str, str]] = set()
    result: list[Mapping[str, object]] = []
    for row in rows:
        key = (str(row.get("lemma") or ""), str(row.get("best_tier") or ""))
        if key in seen:
            continue
        seen.add(key)
        result.append(row)
    return result


def _counts(rows: Sequence[Mapping[str, object]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key) or "") for row in rows).items()))


def _manual_review_counts(rows: Sequence[Mapping[str, object]], key: str) -> dict[str, int]:
    return dict(
        sorted(
            Counter(
                str(_as_mapping(row.get("manual_review")).get(key) or "") for row in rows
            ).items()
        )
    )


def _evidence_cell(row: Mapping[str, object]) -> str:
    snippet = str(row.get("snippet") or "").replace("|", "\\|").strip()
    if snippet:
        return f"`{_truncate(snippet, 80)}`"
    return str(row.get("evidence_type") or "")


def _markdown_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ").strip()


def _mapping_rows(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, list):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _safe_float(value: object) -> float:
    try:
        return round(float(value), 6)
    except (TypeError, ValueError):
        return 0.0


def _truncate(value: str, limit: int) -> str:
    text = " ".join(value.split())
    return text if len(text) <= limit else text[: max(0, limit - 3)].rstrip() + "..."


def _finding(level: str, code: str, message: str) -> dict[str, object]:
    return {"level": level, "code": code, "message": message}


def _load_json(path: Path) -> Mapping[str, object]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return payload if isinstance(payload, Mapping) else {}


def _load_optional_json(path: Path) -> Mapping[str, object] | None:
    if not Path(path).exists():
        return None
    return _load_json(path)


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
