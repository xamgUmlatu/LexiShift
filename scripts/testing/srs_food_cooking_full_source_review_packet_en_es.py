#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Mapping, Sequence

from srs_animals_plants_existing_signal_audit_en_es import (
    _candidate_lemmas,
    load_kaikki_rows,
    summarize_family,
)
from srs_food_cooking_existing_signal_audit_en_es import (
    DEFAULT_FREQUENCY_DB,
    DEFAULT_KAIKKI_FORWARD_DB,
    DEFAULT_POLICY,
    FAMILY,
    evidence_from_rows,
    load_food_policy,
)
from srs_food_cooking_signal_review_packet_en_es import (
    build_review_packet as build_frontier_review_packet,
    render_markdown as render_frontier_markdown,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEST_OUTPUTS_ROOT = PROJECT_ROOT / "docs" / "test_outputs"
DEFAULT_JSON_OUT = (
    TEST_OUTPUTS_ROOT / "srs_food_cooking_full_source_review_packet_en_es_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    TEST_OUTPUTS_ROOT / "srs_food_cooking_full_source_review_packet_en_es_latest.md"
)
DEFAULT_LABELS_JSON = (
    PROJECT_ROOT / "docs" / "test_inputs" / "srs_food_cooking_full_source_review_labels_en_es.json"
)
DEFAULT_SAMPLE_PER_CELL = 4
DEFAULT_MAX_ROWS = 96
DEFAULT_TOP_N = 10000


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a deterministic pending-review packet from full local Kaikki "
            "food/cooking candidates outside the already-reviewed current frontier. "
            "Read-only; no downloads, overlays, pack installs, or helper mutation."
        )
    )
    parser.add_argument("--policy-json", type=Path, default=DEFAULT_POLICY)
    parser.add_argument("--frequency-db", type=Path, default=DEFAULT_FREQUENCY_DB)
    parser.add_argument("--kaikki-forward-db", type=Path, default=DEFAULT_KAIKKI_FORWARD_DB)
    parser.add_argument("--top-n", type=int, default=DEFAULT_TOP_N)
    parser.add_argument("--sample-per-cell", type=int, default=DEFAULT_SAMPLE_PER_CELL)
    parser.add_argument("--max-rows", type=int, default=DEFAULT_MAX_ROWS)
    parser.add_argument("--include-current-frontier", action="store_true")
    parser.add_argument("--labels-json", type=Path, default=DEFAULT_LABELS_JSON)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_report(
        policy_path=args.policy_json,
        frequency_db=args.frequency_db,
        kaikki_forward_db=args.kaikki_forward_db,
        top_n=max(1, int(args.top_n)),
        sample_per_cell=max(1, int(args.sample_per_cell)),
        max_rows=max(1, int(args.max_rows)),
        exclude_current_frontier=not bool(args.include_current_frontier),
        labels_path=args.labels_json,
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
    policy_path: Path = DEFAULT_POLICY,
    frequency_db: Path = DEFAULT_FREQUENCY_DB,
    kaikki_forward_db: Path = DEFAULT_KAIKKI_FORWARD_DB,
    top_n: int = DEFAULT_TOP_N,
    sample_per_cell: int = DEFAULT_SAMPLE_PER_CELL,
    max_rows: int = DEFAULT_MAX_ROWS,
    exclude_current_frontier: bool = True,
    labels_path: Path | None = DEFAULT_LABELS_JSON,
    generated_at: str | None = None,
) -> dict[str, object]:
    generated_at = generated_at or _utc_now()
    policy = load_food_policy(policy_path)
    frequency_path = Path(frequency_db).expanduser().resolve(strict=False)
    kaikki_path = Path(kaikki_forward_db).expanduser().resolve(strict=False)
    findings = []
    if not kaikki_path.exists():
        return _missing_source_report(
            generated_at=generated_at,
            policy_path=policy_path,
            frequency_db=frequency_path,
            kaikki_forward_db=kaikki_path,
            finding=_finding("FAIL", "kaikki_db_missing", "Kaikki DB is missing."),
        )

    current_frontier_lemmas: set[str] = set()
    if exclude_current_frontier:
        if frequency_path.exists():
            current_frontier_lemmas = set(_candidate_lemmas(frequency_path, top_n=top_n))
        else:
            findings.append(
                _finding(
                    "WARN",
                    "frequency_db_missing_no_frontier_exclusion",
                    "Frequency DB is missing, so current-frontier candidates were not excluded.",
                )
            )

    candidate_inventory = _candidate_inventory_from_local_source(
        kaikki_forward_db=kaikki_path,
        policy=policy,
    )
    resolved_labels_path = _resolve_path(labels_path) if labels_path else None
    report = build_review_packet_from_candidates(
        candidate_inventory=candidate_inventory,
        current_frontier_lemmas=current_frontier_lemmas,
        exclude_current_frontier=exclude_current_frontier,
        sample_per_cell=sample_per_cell,
        max_rows=max_rows,
        labels_payload=_load_optional_json(resolved_labels_path),
        labels_path=resolved_labels_path,
        generated_at=generated_at,
    )
    base_findings = _mapping_rows(report.get("findings"))
    report["inputs"].update(
        {
            "signal_policy_json": _repo_path(policy_path),
            "signal_policy_id": policy.policy_id,
            "frequency_db": str(frequency_path),
            "kaikki_forward_db": str(kaikki_path),
            "top_n": int(top_n),
        }
    )
    report["findings"] = [*findings, *base_findings, *_source_findings(report)]
    report["summary"]["finding_counts"] = dict(
        Counter(str(row.get("level") or "") for row in report["findings"])
    )
    report["summary"]["issues"] = [
        row.get("code") for row in report["findings"] if row.get("level") == "FAIL"
    ]
    report["summary"]["warnings"] = [
        row.get("code") for row in report["findings"] if row.get("level") == "WARN"
    ]
    report["status"] = (
        "ok" if not any(row.get("level") == "FAIL" for row in report["findings"]) else "review"
    )
    report["decision"] = (
        "srs_food_cooking_full_source_review_packet_ready"
        if report["status"] == "ok"
        else "srs_food_cooking_full_source_review_packet_needs_review"
    )
    return report


def build_review_packet_from_candidates(
    *,
    candidate_inventory: Sequence[Mapping[str, object]],
    current_frontier_lemmas: set[str] | frozenset[str],
    exclude_current_frontier: bool = True,
    sample_per_cell: int = DEFAULT_SAMPLE_PER_CELL,
    max_rows: int = DEFAULT_MAX_ROWS,
    labels_payload: Mapping[str, object] | None = None,
    labels_path: Path | None = None,
    generated_at: str | None = None,
) -> dict[str, object]:
    filtered_candidates = [
        dict(row)
        for row in candidate_inventory
        if not exclude_current_frontier
        or str(row.get("lemma") or "") not in current_frontier_lemmas
    ]
    audit_payload = {
        "decision": "food_cooking_full_source_candidate_inventory_ready",
        "generated_at": generated_at or _utc_now(),
        "family": {
            "family": FAMILY,
            "candidate_inventory": filtered_candidates,
        },
    }
    report = build_frontier_review_packet(
        audit_payload=audit_payload,
        audit_path=None,
        labels_payload=labels_payload,
        labels_path=labels_path,
        sample_per_cell=sample_per_cell,
        max_rows=max_rows,
        generated_at=generated_at,
    )
    report["decision"] = "srs_food_cooking_full_source_review_packet_ready"
    report["inputs"].update(
        {
            "source_scope": (
                "full_local_kaikki_minus_current_frontier"
                if exclude_current_frontier
                else "full_local_kaikki_including_current_frontier"
            ),
            "excluded_current_frontier_lemma_count": len(current_frontier_lemmas)
            if exclude_current_frontier
            else 0,
        }
    )
    report["summary"].update(
        {
            "source_candidate_count": len(candidate_inventory),
            "excluded_current_frontier_candidate_count": len(candidate_inventory)
            - len(filtered_candidates),
            "expansion_candidate_count": len(filtered_candidates),
        }
    )
    report["limitations"] = [
        "This packet samples installed local Kaikki/Wiktionary candidates only; it does not download sources.",
        "Current-frontier candidates are excluded by default because they were already reviewed in the 46-row packet.",
        "The packet calibrates broader food/cooking source policy quality; it is not an installed overlay or runtime admission change.",
        "Rows are selected deterministically by review cell and stable hash, not by model judgment.",
    ]
    return report


def render_markdown(report: Mapping[str, object]) -> str:
    text = render_frontier_markdown(report)
    text = text.replace(
        "# en-es Food/Cooking Signal Review Packet",
        "# en-es Food/Cooking Full-Source Review Packet",
        1,
    )
    summary = _as_mapping(report.get("summary"))
    decision_counts = _as_mapping(summary.get("manual_decision_counts"))
    accepted_count = int(decision_counts.get("accept_strong_topic") or 0) + int(
        decision_counts.get("accept_light_topic") or 0
    )
    rejected_rows = [
        row
        for row in _mapping_rows(report.get("review_queue"))
        if str(_as_mapping(row.get("manual_review")).get("decision") or "").startswith("reject")
    ]
    scope_lines = [
        "",
        "## Source Scope",
        "",
        f"- Scope: `{_as_mapping(report.get('inputs')).get('source_scope', '')}`",
        f"- Source candidates: `{summary.get('source_candidate_count', 0)}`",
        f"- Excluded current-frontier candidates: "
        f"`{summary.get('excluded_current_frontier_candidate_count', 0)}`",
        f"- Expansion candidates sampled from: `{summary.get('expansion_candidate_count', 0)}`",
        "",
        "## Review Interpretation",
        "",
        f"- Accepted rows: `{accepted_count}` / `{summary.get('review_queue_count', 0)}`",
        f"- Strong accepts: `{decision_counts.get('accept_strong_topic', 0)}`",
        f"- Light accepts: `{decision_counts.get('accept_light_topic', 0)}`",
        f"- Rejected rows: `{len(rejected_rows)}`",
    ]
    if rejected_rows:
        scope_lines.extend(["", "Rejected rows:"])
        scope_lines.extend(
            (
                f"- `{row.get('lemma', '')}`: "
                f"`{_as_mapping(row.get('manual_review')).get('decision', '')}` "
                f"({row.get('best_tier', '')}/{row.get('source_label', '')})"
            )
            for row in rejected_rows
        )
    return text.replace(
        "\n## Manual Decisions\n", "\n".join(scope_lines) + "\n\n## Manual Decisions\n", 1
    )


def _candidate_inventory_from_local_source(
    *, kaikki_forward_db: Path, policy: object
) -> list[dict[str, object]]:
    rows_by_lemma = load_kaikki_rows(kaikki_forward_db)
    evidence_by_lemma = {}
    for lemma, source_rows in rows_by_lemma.items():
        evidence = evidence_from_rows(lemma, source_rows, policy)
        if evidence:
            evidence_by_lemma[(FAMILY, lemma)] = evidence
    summary = summarize_family(FAMILY, sorted(rows_by_lemma), evidence_by_lemma)
    return [dict(row) for row in _mapping_rows(summary.get("candidate_inventory"))]


def _source_findings(report: Mapping[str, object]) -> list[dict[str, object]]:
    summary = _as_mapping(report.get("summary"))
    findings = []
    if int(summary.get("source_candidate_count") or 0) > 0:
        findings.append(
            _finding(
                "PASS",
                "full_source_candidates_present",
                "Full local food/cooking candidates loaded.",
            )
        )
    else:
        findings.append(
            _finding(
                "FAIL",
                "full_source_candidates_empty",
                "No full-source food/cooking candidates loaded.",
            )
        )
    if int(summary.get("expansion_candidate_count") or 0) > int(
        summary.get("review_queue_count") or 0
    ):
        findings.append(
            _finding(
                "PASS",
                "expansion_review_packet_sampled",
                "Review packet samples a broader expansion candidate universe.",
            )
        )
    if int(summary.get("excluded_current_frontier_candidate_count") or 0) > 0:
        findings.append(
            _finding(
                "PASS",
                "current_frontier_candidates_excluded",
                "Already reviewed current-frontier candidates were excluded from this packet.",
            )
        )
    return findings


def _missing_source_report(
    *,
    generated_at: str,
    policy_path: Path,
    frequency_db: Path,
    kaikki_forward_db: Path,
    finding: Mapping[str, object],
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "status": "review",
        "decision": "srs_food_cooking_full_source_review_packet_needs_review",
        "generated_at": generated_at,
        "inputs": {
            "signal_policy_json": _repo_path(policy_path),
            "frequency_db": str(frequency_db),
            "kaikki_forward_db": str(kaikki_forward_db),
        },
        "summary": {
            "source_candidate_count": 0,
            "expansion_candidate_count": 0,
            "review_queue_count": 0,
            "finding_counts": {"FAIL": 1},
            "issues": [finding.get("code")],
            "warnings": [],
        },
        "cell_inventory": [],
        "review_queue": [],
        "findings": [dict(finding)],
        "limitations": [
            "This packet cannot be generated without the installed local Kaikki/Wiktionary DB."
        ],
    }


def _mapping_rows(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, list):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def _load_optional_json(path: Path | None) -> Mapping[str, object] | None:
    if not path or not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, Mapping) else None


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _finding(level: str, code: str, message: str) -> dict[str, object]:
    return {"level": level, "code": code, "message": message}


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
