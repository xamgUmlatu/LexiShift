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
DEFAULT_AUDIT_JSON = TEST_OUTPUTS_ROOT / "srs_jmdict_topic_source_readiness_en_ja_latest.json"
DEFAULT_LABELS_JSON = (
    PROJECT_ROOT / "docs" / "test_inputs" / "srs_jmdict_topic_review_labels_en_ja.json"
)
DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / "srs_jmdict_topic_review_packet_en_ja_latest.json"
DEFAULT_MARKDOWN_OUT = TEST_OUTPUTS_ROOT / "srs_jmdict_topic_review_packet_en_ja_latest.md"
DEFAULT_SAMPLE_PER_CELL = 3
DEFAULT_MAX_ROWS = 144
REVIEW_DECISIONS = (
    "accept_strong_topic",
    "accept_light_topic",
    "reject_wrong_topic",
    "reject_secondary_or_obscure_sense",
    "uncertain_needs_source_check",
)
MATCH_STRENGTH_PRIORITY = {"strong": 0, "reading_only": 1}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a deterministic manual review packet from the en-ja "
            "JMDict/BCCWJ topic-source readiness audit. This does not promote "
            "admission overlays."
        )
    )
    parser.add_argument("--audit-json", type=Path, default=DEFAULT_AUDIT_JSON)
    parser.add_argument("--labels-json", type=Path, default=DEFAULT_LABELS_JSON)
    parser.add_argument("--family", action="append", default=[])
    parser.add_argument("--sample-per-cell", type=int, default=DEFAULT_SAMPLE_PER_CELL)
    parser.add_argument("--max-rows", type=int, default=DEFAULT_MAX_ROWS)
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
        families=tuple(str(family).strip() for family in args.family if str(family).strip()),
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
    families: Sequence[str] = (),
    sample_per_cell: int = DEFAULT_SAMPLE_PER_CELL,
    max_rows: int = DEFAULT_MAX_ROWS,
    generated_at: str | None = None,
) -> dict[str, object]:
    candidates = _candidate_rows(audit_payload, selected_families=set(families))
    cells = _group_by_cell(candidates)
    selected = _select_review_rows(cells, sample_per_cell=sample_per_cell, max_rows=max_rows)
    review_queue = [
        _review_row(index=index, row=row) for index, row in enumerate(selected, start=1)
    ]
    label_result = _apply_labels(
        review_queue=review_queue,
        labels_payload=labels_payload,
        labels_path=labels_path,
    )
    findings = _findings(
        candidates=candidates, review_queue=review_queue, label_result=label_result
    )
    status = "ok" if not any(row["level"] == "FAIL" for row in findings) else "review"
    return {
        "schema_version": 1,
        "status": status,
        "decision": (
            "srs_jmdict_topic_review_packet_ready"
            if status == "ok"
            else "srs_jmdict_topic_review_packet_needs_review"
        ),
        "generated_at": generated_at or _utc_now(),
        "language_pair": "en-ja",
        "inputs": {
            "audit_json": _repo_path(audit_path),
            "audit_decision": str(audit_payload.get("decision") or ""),
            "audit_generated_at": str(audit_payload.get("generated_at") or ""),
            "labels_json": _repo_path(labels_path),
            "families": sorted(set(families)),
            "sample_per_cell": int(sample_per_cell),
            "max_rows": int(max_rows),
        },
        "manual_review_policy": {
            "state": "agent_labeled_pending_user_approval"
            if label_result.get("labels_provided")
            else "pending_user_review",
            "allowed_decisions": list(REVIEW_DECISIONS),
            "promotion_rule": (
                "Selected rows are precision-review samples only. No topic label "
                "is promoted into profile_topics or admission overlays until a "
                "reviewed overlay/policy artifact explicitly accepts it."
            ),
        },
        "summary": _summary(
            candidates=candidates,
            review_queue=review_queue,
            cells=cells,
            label_result=label_result,
        ),
        "cell_inventory": _cell_inventory(cells=cells, review_queue=review_queue),
        "review_queue": review_queue,
        "label_result": label_result,
        "findings": findings,
        "limitations": [
            "The packet samples the existing source-readiness inventory only; it does not mine new sources.",
            "Rows are selected deterministically by family, match strength, source label, rank, and stable hash.",
            "JMDict field labels are source evidence, not product-approved topic tags.",
            "Agent labels, if supplied, are calibration evidence and still need user approval before promotion.",
        ],
    }


def _candidate_rows(
    audit_payload: Mapping[str, object],
    *,
    selected_families: set[str],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for raw in _mapping_rows(audit_payload.get("topic_candidate_inventory")):
        family_id = str(raw.get("family_id") or "").strip()
        if not family_id or (selected_families and family_id not in selected_families):
            continue
        source_labels = _string_list(raw.get("source_labels"))
        if not source_labels:
            continue
        rows.append(
            {
                "family_id": family_id,
                "lemma": str(raw.get("lemma") or ""),
                "lform": str(raw.get("lform") or ""),
                "rank": _safe_float(raw.get("rank")),
                "pos": str(raw.get("pos") or ""),
                "pos_bucket": str(raw.get("pos_bucket") or ""),
                "match_strength": str(raw.get("match_strength") or ""),
                "jmdict_match_modes": _string_list(raw.get("jmdict_match_modes")),
                "jmdict_matched_terms": _string_list(raw.get("jmdict_matched_terms")),
                "source_labels": source_labels,
                "primary_source_label": source_labels[0],
                "jmdict_glosses": _string_list(raw.get("jmdict_glosses")),
                "ambiguity_flags": _ambiguity_flags(raw),
            }
        )
    rows.sort(key=_candidate_sort_key)
    return rows


def _ambiguity_flags(row: Mapping[str, object]) -> list[str]:
    flags: list[str] = []
    if str(row.get("match_strength") or "") == "reading_only":
        flags.append("reading_only")
    if len(_string_list(row.get("source_labels"))) > 1:
        flags.append("multi_source_label")
    if len(_string_list(row.get("jmdict_match_modes"))) > 1:
        flags.append("multi_match_mode")
    if len(_string_list(row.get("jmdict_glosses"))) > 4:
        flags.append("many_glosses")
    return flags


def _group_by_cell(rows: Sequence[Mapping[str, object]]) -> dict[str, list[dict[str, object]]]:
    cells: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        cells[_review_cell(row)].append(dict(row))
    for cell_rows in cells.values():
        cell_rows.sort(key=_candidate_sort_key)
    return dict(cells)


def _select_review_rows(
    cells: Mapping[str, Sequence[dict[str, object]]],
    *,
    sample_per_cell: int,
    max_rows: int,
) -> list[dict[str, object]]:
    selected: list[dict[str, object]] = []
    cells_by_family: dict[str, list[str]] = defaultdict(list)
    for cell in sorted(cells, key=_cell_sort_key):
        cells_by_family[cell.split("|", 1)[0]].append(cell)
    families = sorted(cells_by_family)
    for round_index in range(sample_per_cell):
        for family in families:
            for cell in cells_by_family[family]:
                if round_index >= len(cells[cell]):
                    continue
                if len(selected) >= max_rows:
                    return selected
                selected.append(dict(cells[cell][round_index]))
    return selected


def _review_row(index: int, row: Mapping[str, object]) -> dict[str, object]:
    review_cell = _review_cell(row)
    return {
        "review_id": f"srs-enja-topic-{index:03d}",
        "review_cell": review_cell,
        "family_id": row.get("family_id"),
        "lemma": row.get("lemma"),
        "lform": row.get("lform"),
        "rank": row.get("rank"),
        "pos": row.get("pos"),
        "pos_bucket": row.get("pos_bucket"),
        "match_strength": row.get("match_strength"),
        "source_labels": row.get("source_labels"),
        "primary_source_label": row.get("primary_source_label"),
        "jmdict_match_modes": row.get("jmdict_match_modes"),
        "jmdict_matched_terms": row.get("jmdict_matched_terms"),
        "jmdict_glosses": row.get("jmdict_glosses"),
        "ambiguity_flags": row.get("ambiguity_flags"),
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
        "# en-ja JMDict Topic Review Packet",
        "",
        f"- status: `{report.get('status')}`",
        f"- decision: `{report.get('decision')}`",
        f"- generated_at: `{report.get('generated_at')}`",
        f"- candidate universe: `{summary.get('candidate_count', 0)}`",
        f"- review rows: `{summary.get('review_queue_count', 0)}`",
        f"- review cells covered: `{summary.get('selected_cell_count', 0)}` / "
        f"`{summary.get('cell_count', 0)}`",
        f"- labeled rows: `{summary.get('labeled_row_count', 0)}`",
        "",
        "## Counts",
        "",
        "### Review Rows By Family",
        "",
    ]
    for family, count in _as_mapping(summary.get("review_rows_by_family")).items():
        lines.append(f"- `{family}`: `{count}`")
    lines.extend(["", "### Manual Decisions", ""])
    decision_counts = _as_mapping(summary.get("manual_decision_counts"))
    for decision in REVIEW_DECISIONS:
        lines.append(f"- `{decision}`: `{decision_counts.get(decision, 0)}`")
    lines.extend(
        [
            "",
            "## Cell Coverage",
            "",
            "| Cell | Candidates | Selected |",
            "| --- | ---: | ---: |",
        ]
    )
    for cell in _mapping_rows(report.get("cell_inventory")):
        lines.append(
            f"| `{cell.get('cell', '')}` | `{cell.get('candidate_count', 0)}` | "
            f"`{cell.get('selected_count', 0)}` |"
        )
    lines.extend(
        [
            "",
            "## Manual Review Queue",
            "",
            "| ID | Family | Lemma | Reading | Rank | Match | Source labels | Flags | Matched terms | Gloss hints | Decision | Notes |",
            "| --- | --- | --- | --- | ---: | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in _mapping_rows(report.get("review_queue")):
        manual_review = _as_mapping(row.get("manual_review"))
        lines.append(
            f"| `{row.get('review_id', '')}` | `{row.get('family_id', '')}` | "
            f"`{row.get('lemma', '')}` | `{row.get('lform', '')}` | "
            f"`{row.get('rank', '')}` | `{row.get('match_strength', '')}` | "
            f"{_markdown_list(row.get('source_labels'))} | "
            f"{_markdown_list(row.get('ambiguity_flags'))} | "
            f"{_markdown_list(row.get('jmdict_matched_terms'))} | "
            f"{_markdown_glosses(row.get('jmdict_glosses'))} | "
            f"{_markdown_cell(str(manual_review.get('decision') or ''))} | "
            f"{_markdown_cell(str(manual_review.get('notes') or ''))} |"
        )
    lines.extend(["", "## Findings", ""])
    for finding in _mapping_rows(report.get("findings")):
        lines.append(
            f"- `{finding.get('level')}` `{finding.get('code')}`: {finding.get('message')}"
        )
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- {item}" for item in report.get("limitations", []))
    return "\n".join(lines) + "\n"


def _summary(
    *,
    candidates: Sequence[Mapping[str, object]],
    review_queue: Sequence[Mapping[str, object]],
    cells: Mapping[str, Sequence[Mapping[str, object]]],
    label_result: Mapping[str, object],
) -> dict[str, object]:
    selected_cells = {str(row.get("review_cell") or "") for row in review_queue}
    return {
        "candidate_count": len(candidates),
        "review_queue_count": len(review_queue),
        "cell_count": len(cells),
        "selected_cell_count": len(selected_cells),
        "candidate_counts_by_family": _counts(candidates, "family_id"),
        "candidate_counts_by_match_strength": _counts(candidates, "match_strength"),
        "review_rows_by_family": _counts(review_queue, "family_id"),
        "review_rows_by_match_strength": _counts(review_queue, "match_strength"),
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
    *,
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
    findings: list[dict[str, object]] = []
    findings.append(
        _finding(
            "PASS" if candidates else "FAIL",
            "candidate_universe_present" if candidates else "candidate_universe_empty",
            f"Candidate rows loaded: {len(candidates)}",
        )
    )
    findings.append(
        _finding(
            "PASS" if review_queue else "FAIL",
            "review_queue_present" if review_queue else "review_queue_empty",
            f"Review rows generated: {len(review_queue)}",
        )
    )
    if not label_result.get("labels_provided"):
        findings.append(
            _finding(
                "PASS",
                "manual_labels_pending",
                "No label file was supplied; selected rows remain pending review.",
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
    findings.append(
        _finding(
            "FAIL" if invalid_values else "PASS",
            "manual_labels_invalid" if invalid_values else "manual_labels_applied",
            f"Label validation issues: {invalid_values}"
            if invalid_values
            else "All labels applied.",
        )
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
    duplicate_review_ids: list[str] = []
    invalid_decision_review_ids: list[str] = []
    mismatched_review_ids: list[str] = []
    for label in labels:
        review_id = str(label.get("review_id") or "")
        if not review_id:
            invalid_decision_review_ids.append("(missing review_id)")
            continue
        if review_id in labels_by_id:
            duplicate_review_ids.append(review_id)
            continue
        labels_by_id[review_id] = label
        if str(label.get("decision") or "") not in REVIEW_DECISIONS:
            invalid_decision_review_ids.append(review_id)
    unknown_review_ids = sorted(set(labels_by_id) - set(review_by_id))
    missing_review_ids = sorted(set(review_by_id) - set(labels_by_id))
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
        if label is None or review_id in invalid_decision_review_ids:
            continue
        mismatches = [
            key
            for key in ("family_id", "lemma")
            if label.get(key) is not None and str(label.get(key)) != str(row.get(key) or "")
        ]
        if mismatches:
            mismatched_review_ids.append(f"{review_id}:{','.join(mismatches)}")
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
            "missing_review_ids": missing_review_ids,
            "unknown_review_ids": unknown_review_ids,
            "duplicate_review_ids": sorted(set(duplicate_review_ids)),
            "invalid_decision_review_ids": sorted(set(invalid_decision_review_ids)),
            "mismatched_review_ids": sorted(set(mismatched_review_ids)),
        }
    )
    return result


def _review_cell(row: Mapping[str, object]) -> str:
    return "|".join(
        (
            str(row.get("family_id") or ""),
            str(row.get("match_strength") or ""),
            str(row.get("primary_source_label") or ""),
        )
    )


def _cell_sort_key(cell: str) -> tuple[str, int, str]:
    family, match_strength, source_label = (cell.split("|") + ["", ""])[:3]
    return (family, MATCH_STRENGTH_PRIORITY.get(match_strength, 9), source_label)


def _candidate_sort_key(row: Mapping[str, object]) -> tuple[str, int, str, float, str, str]:
    return (
        str(row.get("family_id") or ""),
        MATCH_STRENGTH_PRIORITY.get(str(row.get("match_strength") or ""), 9),
        str(row.get("primary_source_label") or ""),
        float(row.get("rank") or 9999999),
        str(row.get("lemma") or ""),
        _stable_hash(row),
    )


def _stable_hash(row: Mapping[str, object]) -> str:
    payload = "|".join(
        str(row.get(key) or "")
        for key in ("family_id", "lemma", "lform", "primary_source_label", "rank")
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _counts(rows: Sequence[Mapping[str, object]], key: str) -> dict[str, int]:
    counts = Counter(str(row.get(key) or "") for row in rows)
    return {name: counts[name] for name in sorted(counts)}


def _manual_review_counts(rows: Sequence[Mapping[str, object]], key: str) -> dict[str, int]:
    counts = Counter(str(_as_mapping(row.get("manual_review")).get(key) or "") for row in rows)
    return {name: counts[name] for name in sorted(counts)}


def _finding(level: str, code: str, message: str) -> dict[str, object]:
    return {"level": level, "code": code, "message": message}


def _load_json(path: Path) -> dict[str, object]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, Mapping):
        raise ValueError(f"Expected JSON object in {path}")
    return dict(payload)


def _load_optional_json(path: Path) -> dict[str, object] | None:
    if not path.exists():
        return None
    return _load_json(path)


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


def _repo_path(path: Path | None) -> str:
    if path is None:
        return ""
    resolved = path.resolve()
    try:
        return resolved.relative_to(PROJECT_ROOT.resolve()).as_posix()
    except ValueError:
        return str(resolved)


def _mapping_rows(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, Sequence) or isinstance(value, str):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _string_list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if isinstance(value, Sequence):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    return [text] if text else []


def _safe_float(value: object) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _markdown_list(value: object, *, limit: int = 4) -> str:
    values = _string_list(value)[:limit]
    return ", ".join(f"`{_markdown_cell(item)}`" for item in values) if values else "-"


def _markdown_glosses(value: object, *, limit: int = 2) -> str:
    values = _string_list(value)[:limit]
    return "<br>".join(_markdown_cell(item) for item in values) if values else "-"


def _markdown_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ").replace("\r", " ")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


if __name__ == "__main__":
    raise SystemExit(main())
