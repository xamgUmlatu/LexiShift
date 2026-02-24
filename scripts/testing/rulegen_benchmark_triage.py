#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class TriageItem:
    pair: str
    case_id: str
    target: str
    status: str  # FAIL | REVIEW
    reasons: list[str]
    top1_source: str | None
    top3_sources: list[str]
    expected_matches: list[str]
    forbidden_matches: list[str]
    suggested_case_patch: dict[str, object]


@dataclass(frozen=True)
class TriageReport:
    benchmark_json: str
    pairs_processed: int
    failing_or_review_count: int
    items: list[TriageItem]

    def to_dict(self) -> dict[str, object]:
        return {
            "benchmark_json": self.benchmark_json,
            "pairs_processed": self.pairs_processed,
            "failing_or_review_count": self.failing_or_review_count,
            "items": [asdict(item) for item in self.items],
        }


def _read_json(path: Path) -> Mapping[str, object]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, Mapping):
        raise ValueError(f"Expected JSON object at {path}")
    return payload


def _as_list_of_str(value: object) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    result: list[str] = []
    for item in value:
        text = str(item or "").strip()
        if text:
            result.append(text)
    return result


def _classify_case(case: Mapping[str, object]) -> tuple[str | None, list[str]]:
    reasons: list[str] = []
    top1_correct = bool(case.get("top1_correct"))
    top3_hit = bool(case.get("top3_contains_expected"))
    top1_forbidden = bool(case.get("top1_forbidden"))
    forbidden_any = bool(case.get("forbidden_any_present"))
    rule_count = int(case.get("rule_count") or 0)

    if top1_forbidden:
        reasons.append("top1_is_forbidden")
    if forbidden_any:
        reasons.append("forbidden_candidate_present")
    if not top3_hit:
        reasons.append("expected_candidate_missing_from_top3")
    if rule_count == 0:
        reasons.append("no_rules_emitted")

    if reasons:
        return "FAIL", reasons

    if not top1_correct:
        reasons.append("top1_not_in_expected_set")
        return "REVIEW", reasons

    return None, []


def _suggest_patch(case: Mapping[str, object], status: str) -> dict[str, object]:
    top1_source = str(case.get("top1_source") or "").strip()
    top3_sources = _as_list_of_str(case.get("top3_sources"))

    patch: dict[str, object] = {
        "action": "review_labels",
        "priority": "high" if status == "FAIL" else "medium",
        "notes": [],
    }
    notes = patch["notes"]
    if isinstance(notes, list):
        if status == "FAIL":
            notes.append("Review case labels and pair tuning; this case violates hard quality expectations.")
        else:
            notes.append("Review expected_top1_any labels or scoring weights for this case.")
        if top1_source:
            notes.append(f"Observed top1 source: {top1_source}")
        if top3_sources:
            notes.append(f"Observed top3 sources: {', '.join(top3_sources)}")

    if top1_source:
        patch["candidate_forbidden_top1"] = [top1_source]
    if top3_sources:
        patch["candidate_expected_any"] = top3_sources[:3]

    return patch


def _render_markdown(report: TriageReport) -> str:
    lines: list[str] = [
        "# Rulegen Benchmark Triage",
        "",
        f"- benchmark_json: `{report.benchmark_json}`",
        f"- pairs_processed: {report.pairs_processed}",
        f"- failing_or_review_count: {report.failing_or_review_count}",
        "",
    ]

    if not report.items:
        lines.append("No FAIL/REVIEW cases found in best runs.")
        return "\n".join(lines)

    lines.extend(
        [
            "| Pair | Case | Target | Status | Reasons | Top1 | Top3 |",
            "|---|---|---|---|---|---|---|",
        ]
    )

    for item in report.items:
        lines.append(
            "| "
            f"{item.pair} | "
            f"`{item.case_id}` | "
            f"{item.target} | "
            f"{item.status} | "
            f"{', '.join(item.reasons)} | "
            f"{item.top1_source or '-'} | "
            f"{', '.join(item.top3_sources) if item.top3_sources else '-'} |"
        )

    lines.append("")
    lines.append("## Suggested Case Patches")
    lines.append("")
    for item in report.items:
        lines.append(f"### {item.pair} / {item.case_id}")
        lines.append("```json")
        lines.append(json.dumps(item.suggested_case_patch, ensure_ascii=False, indent=2))
        lines.append("```")
        lines.append("")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Extract FAIL/REVIEW benchmark cases from the best run per pair to drive "
            "failure-to-case promotion and iterative tuning."
        )
    )
    parser.add_argument(
        "--benchmark-json",
        type=Path,
        default=PROJECT_ROOT / "docs" / "test_outputs" / "rulegen_benchmark_en_es_latest.json",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        default=PROJECT_ROOT / "docs" / "test_outputs" / "rulegen_benchmark_triage_latest.json",
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=PROJECT_ROOT / "docs" / "test_outputs" / "rulegen_benchmark_triage_latest.md",
    )
    args = parser.parse_args()

    payload = _read_json(args.benchmark_json)
    pairs_payload = payload.get("pairs")
    if not isinstance(pairs_payload, Mapping):
        raise SystemExit("Benchmark payload has no 'pairs' object.")

    triage_items: list[TriageItem] = []

    for pair, pair_payload in sorted(pairs_payload.items()):
        if not isinstance(pair_payload, Mapping):
            continue
        best_run = pair_payload.get("best_run")
        if not isinstance(best_run, Mapping):
            continue
        case_results = best_run.get("case_results")
        if not isinstance(case_results, Sequence):
            continue

        for case in case_results:
            if not isinstance(case, Mapping):
                continue
            status, reasons = _classify_case(case)
            if status is None:
                continue
            case_id = str(case.get("case_id") or "").strip() or "<unknown-case-id>"
            target = str(case.get("target") or "").strip() or "<unknown-target>"
            triage_items.append(
                TriageItem(
                    pair=str(pair),
                    case_id=case_id,
                    target=target,
                    status=status,
                    reasons=reasons,
                    top1_source=str(case.get("top1_source") or "").strip() or None,
                    top3_sources=_as_list_of_str(case.get("top3_sources")),
                    expected_matches=_as_list_of_str(case.get("expected_matches")),
                    forbidden_matches=_as_list_of_str(case.get("forbidden_matches")),
                    suggested_case_patch=_suggest_patch(case, status),
                )
            )

    report = TriageReport(
        benchmark_json=str(args.benchmark_json),
        pairs_processed=len(pairs_payload),
        failing_or_review_count=len(triage_items),
        items=triage_items,
    )

    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.write_text(_render_markdown(report), encoding="utf-8")

    print(f"pairs_processed: {report.pairs_processed}")
    print(f"triage_items: {report.failing_or_review_count}")
    print(f"json_output: {args.json_out}")
    print(f"markdown_output: {args.markdown_out}")


if __name__ == "__main__":
    main()
