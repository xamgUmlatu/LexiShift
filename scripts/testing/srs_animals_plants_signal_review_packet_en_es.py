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
    TEST_OUTPUTS_ROOT / "srs_animals_plants_existing_signal_audit_en_es_spalex_10k_latest.json"
)
DEFAULT_JSON_OUT = (
    TEST_OUTPUTS_ROOT / "srs_animals_plants_signal_review_packet_en_es_spalex_10k_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    TEST_OUTPUTS_ROOT / "srs_animals_plants_signal_review_packet_en_es_spalex_10k_latest.md"
)
DEFAULT_SAMPLE_PER_CELL = 4
DEFAULT_MAX_ROWS = 96
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
            "Build a deterministic manual review packet for en-es animals/plants "
            "topic-signal candidates. This does not promote any overlay."
        )
    )
    parser.add_argument("--audit-json", type=Path, default=DEFAULT_AUDIT_JSON)
    parser.add_argument("--sample-per-cell", type=int, default=DEFAULT_SAMPLE_PER_CELL)
    parser.add_argument("--max-rows", type=int, default=DEFAULT_MAX_ROWS)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    audit_path = _resolve_path(args.audit_json)
    report = build_review_packet(
        audit_payload=_load_json(audit_path),
        audit_path=audit_path,
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
    sample_per_cell: int = DEFAULT_SAMPLE_PER_CELL,
    max_rows: int = DEFAULT_MAX_ROWS,
    generated_at: str | None = None,
) -> dict[str, object]:
    candidates, full_inventory_used = _candidate_rows(audit_payload)
    cells = _group_by_cell(candidates)
    selected = _select_review_rows(cells, sample_per_cell=sample_per_cell, max_rows=max_rows)
    review_queue = [
        _review_row(index=index, row=row) for index, row in enumerate(selected, start=1)
    ]
    findings = _findings(candidates=candidates, review_queue=review_queue)
    status = "ok" if not any(row["level"] == "FAIL" for row in findings) else "review"
    return {
        "schema_version": 1,
        "status": status,
        "decision": (
            "srs_animals_plants_signal_review_packet_ready"
            if status == "ok"
            else "srs_animals_plants_signal_review_packet_needs_review"
        ),
        "generated_at": generated_at or _utc_now(),
        "inputs": {
            "audit_json": _repo_path(audit_path),
            "audit_decision": str(audit_payload.get("decision") or ""),
            "audit_generated_at": str(audit_payload.get("generated_at") or ""),
            "sample_per_cell": int(sample_per_cell),
            "max_rows": int(max_rows),
        },
        "manual_review_policy": {
            "state": "pending_user_review",
            "allowed_decisions": list(REVIEW_DECISIONS),
            "promotion_rule": (
                "No candidate is product-ready from this packet until its manual_review "
                "state is changed from pending_user_review."
            ),
        },
        "summary": _summary(
            candidates=candidates,
            review_queue=review_queue,
            cells=cells,
            full_inventory_used=full_inventory_used,
        ),
        "cell_inventory": _cell_inventory(cells, review_queue),
        "review_queue": review_queue,
        "findings": findings,
        "limitations": [
            "The packet samples existing audit candidates only; it does not collect new source data.",
            "Rows are selected deterministically by review cell and stable hash, not by model judgment.",
            "Pending labels are a manual QA surface and must not be treated as approved overlay data.",
        ],
    }


def _candidate_rows(
    audit_payload: Mapping[str, object],
) -> tuple[list[dict[str, object]], bool]:
    rows: list[dict[str, object]] = []
    full_inventory_used = True
    for family in _mapping_rows(audit_payload.get("families")):
        family_id = str(family.get("family") or "")
        inventory = _mapping_rows(family.get("candidate_inventory"))
        if not inventory:
            full_inventory_used = False
            inventory = _dedupe_candidate_rows(
                [
                    *_mapping_rows(family.get("top_candidates")),
                    *_mapping_rows(family.get("review_candidates")),
                ]
            )
        for row in inventory:
            evidence = _mapping_rows(row.get("evidence"))
            best_evidence = evidence[0] if evidence else {}
            rows.append(
                {
                    "family": family_id,
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
    rows.sort(key=lambda row: (str(row["family"]), str(row["lemma"])))
    return rows, full_inventory_used


def _group_by_cell(rows: Sequence[Mapping[str, object]]) -> dict[str, list[dict[str, object]]]:
    cells: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        cells[_review_cell(row)].append(dict(row))
    for cell_rows in cells.values():
        cell_rows.sort(key=_stable_candidate_key)
    return dict(cells)


def _select_review_rows(
    cells: Mapping[str, Sequence[dict[str, object]]], *, sample_per_cell: int, max_rows: int
) -> list[dict[str, object]]:
    selected: list[dict[str, object]] = []
    cells_by_family: dict[str, list[str]] = defaultdict(list)
    for cell in sorted(cells, key=_cell_sort_key):
        cells_by_family[cell.split("|", 1)[0]].append(cell)
    families = sorted(cells_by_family)
    for round_index in range(sample_per_cell):
        round_cells_by_family = {
            family: [cell for cell in family_cells if round_index < len(cells[cell])]
            for family, family_cells in cells_by_family.items()
        }
        max_family_cells = max(
            (len(family_cells) for family_cells in round_cells_by_family.values()), default=0
        )
        for cell_index in range(max_family_cells):
            for family in families:
                family_cells = round_cells_by_family.get(family, [])
                if cell_index >= len(family_cells):
                    continue
                if len(selected) >= max_rows:
                    return selected
                cell = family_cells[cell_index]
                selected.append(dict(cells[cell][round_index]))
    return selected


def _review_row(index: int, row: Mapping[str, object]) -> dict[str, object]:
    review_cell = _review_cell(row)
    return {
        "review_id": f"srs-anpl-{index:03d}",
        "review_cell": review_cell,
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
        "# en-es Animals/Plants Signal Review Packet",
        "",
        f"- Status: `{report.get('status', '')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Candidate universe: `{summary.get('candidate_count', 0)}`",
        f"- Review rows: `{summary.get('review_queue_count', 0)}`",
        f"- Review cells covered: `{summary.get('selected_cell_count', 0)}` / "
        f"`{summary.get('cell_count', 0)}`",
        "",
        "## Manual Decisions",
        "",
    ]
    lines.extend(f"- `{decision}`" for decision in REVIEW_DECISIONS)
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
        "| ID | Family | Lemma | Tier | Band | Source | Score | Review? | Evidence | Decision | Notes |"
    )
    lines.append("| --- | --- | --- | --- | --- | --- | ---: | --- | --- | --- | --- |")
    for row in _mapping_rows(report.get("review_queue")):
        lines.append(
            f"| `{row.get('review_id', '')}` | `{row.get('family', '')}` | "
            f"`{row.get('lemma', '')}` | `{row.get('best_tier', '')}` | "
            f"`{row.get('confidence_band', '')}` | "
            f"`{row.get('source_channel', '')}:{row.get('source_label', '')}` | "
            f"{row.get('confidence', 0)} | `{row.get('review_required_by_policy', '')}` | "
            f"{_evidence_cell(row)} |  |  |"
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
) -> dict[str, object]:
    selected_cells = {str(row.get("review_cell") or "") for row in review_queue}
    return {
        "candidate_count": len(candidates),
        "review_queue_count": len(review_queue),
        "cell_count": len(cells),
        "selected_cell_count": len(selected_cells),
        "full_candidate_inventory_used": full_inventory_used,
        "candidate_counts_by_family": _counts(candidates, "family"),
        "candidate_counts_by_tier": _counts(candidates, "best_tier"),
        "candidate_counts_by_band": _counts(candidates, "confidence_band"),
        "review_rows_by_family": _counts(review_queue, "family"),
        "review_rows_by_tier": _counts(review_queue, "best_tier"),
        "review_rows_by_band": _counts(review_queue, "confidence_band"),
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
    *, candidates: Sequence[Mapping[str, object]], review_queue: Sequence[Mapping[str, object]]
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
            _finding("FAIL", "manual_labels_not_pending", "Some labels are not pending.")
        )
    return findings


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


def _evidence_cell(row: Mapping[str, object]) -> str:
    snippet = str(row.get("snippet") or "").replace("|", "\\|").strip()
    if snippet:
        return f"`{_truncate(snippet, 80)}`"
    return str(row.get("evidence_type") or "")


def _mapping_rows(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, list):
        return []
    return [row for row in value if isinstance(row, Mapping)]


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
