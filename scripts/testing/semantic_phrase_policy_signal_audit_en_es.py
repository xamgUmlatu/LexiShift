#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DOCS_ROOT = PROJECT_ROOT / "docs"
TEST_OUTPUTS_ROOT = DOCS_ROOT / "test_outputs"
DEFAULT_CASE_SUITE = (
    DOCS_ROOT
    / "test_inputs"
    / "semantic_routing_cases"
    / "en_es_phrase_policy_signal_non_v10_v1.json"
)
DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / "semantic_phrase_policy_signal_non_v10_latest.json"
DEFAULT_MARKDOWN_OUT = TEST_OUTPUTS_ROOT / "semantic_phrase_policy_signal_non_v10_latest.md"
for candidate in (str(PROJECT_ROOT / "core"),):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from lexishift_core.rulegen.semantic_routing_runtime_scoring import (  # noqa: E402
    extract_runtime_phrase_control_signals,
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Audit phrase-policy signal firing without source evidence or semantic scoring. "
            "This is intended for fresh/non-v10 phrase patterns where source coverage may not exist yet."
        )
    )
    parser.add_argument("--case-suite", type=Path, default=DEFAULT_CASE_SUITE)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def build_phrase_policy_signal_audit_report(
    *,
    case_suite_payload: Mapping[str, object],
    generated_at: str | None = None,
) -> dict[str, object]:
    if generated_at is None:
        generated_at = _utc_now()
    _validate_case_suite(case_suite_payload)
    rows = _audit_rows(case_suite_payload)
    summary = _summary(rows)
    status = "ok" if int(summary["failed_case_count"]) == 0 else "review"
    return {
        "schema_version": 1,
        "status": status,
        "decision": "phrase_signal_pass" if status == "ok" else "phrase_signal_review",
        "generated_at": generated_at,
        "pair": str(case_suite_payload.get("pair") or "").strip() or "en-es",
        "dataset_id": str(case_suite_payload.get("dataset_id") or "").strip(),
        "case_scope": str(case_suite_payload.get("case_scope") or "").strip(),
        "summary": summary,
        "rows": rows,
        "limitations": [
            "signal_only_not_end_to_end_scoring",
            "non_v10_family_senses_are_minimal",
            "does_not_validate_translation_target_quality",
        ],
        "next_steps": [
            "promote useful non-v10 signal rows into end-to-end held-out suites once source evidence exists",
            "add active literal counterexamples before broadening any phrase pattern",
            "rerun the margin sweep when signal rows become end-to-end source cases",
        ],
    }


def render_phrase_policy_signal_audit_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# en-es Phrase Policy Signal Audit",
        "",
        f"- Status: `{report.get('status', 'unknown')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Dataset: `{report.get('dataset_id', '')}`",
        f"- Case scope: `{report.get('case_scope', '')}`",
        "",
        "## Summary",
        "",
        f"- Cases: `{summary.get('case_count', 0)}`",
        f"- Passed: `{summary.get('passed_case_count', 0)}`",
        f"- Failed: `{summary.get('failed_case_count', 0)}`",
        f"- False positives: `{summary.get('false_positive_count', 0)}`",
        f"- False negatives: `{summary.get('false_negative_count', 0)}`",
        "",
        "## Rows",
        "",
        _row_table(report.get("rows", ())),
        "",
        "## Limitations",
        "",
    ]
    lines.extend(f"- `{item}`" for item in report.get("limitations", ()))
    lines.extend(["", "## Next Steps", ""])
    lines.extend(f"- {item}" for item in report.get("next_steps", ()))
    return "\n".join(lines) + "\n"


def _audit_rows(case_suite_payload: Mapping[str, object]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for family in case_suite_payload.get("families", ()):
        if not isinstance(family, Mapping):
            continue
        family_id = str(family.get("family_id") or "").strip()
        family_pos_tags = tuple(
            str(tag or "").strip().lower()
            for tag in family.get("family_pos_tags", ())
            if str(tag or "").strip()
        )
        for case in family.get("cases", ()):
            if not isinstance(case, Mapping):
                continue
            expected_hit = bool(case.get("expected_phrase_preemption"))
            required_signal_codes = tuple(
                str(code or "").strip()
                for code in case.get("required_signal_codes", ())
                if str(code or "").strip()
            )
            signals = extract_runtime_phrase_control_signals(
                str(case.get("sentence") or "").strip(),
                source_phrase=str(case.get("source_phrase") or "").strip(),
                family_pos_tags=family_pos_tags,
            )
            has_required_codes = all(code in signals.signal_codes for code in required_signal_codes)
            passed = bool(signals.phrase_preemption_hit) == expected_hit and has_required_codes
            rows.append(
                {
                    "family_id": family_id,
                    "case_id": str(case.get("case_id") or "").strip(),
                    "sentence": str(case.get("sentence") or "").strip(),
                    "source_phrase": str(case.get("source_phrase") or "").strip(),
                    "expected_phrase_preemption": expected_hit,
                    "required_signal_codes": list(required_signal_codes),
                    "phrase_preemption_hit": bool(signals.phrase_preemption_hit),
                    "matched_phrase_pattern": signals.matched_phrase_pattern,
                    "phrase_reason_code": signals.phrase_reason_code,
                    "signal_codes": list(signals.signal_codes),
                    "family_pos_tags": list(family_pos_tags),
                    "passed": passed,
                }
            )
    return rows


def _summary(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    case_count = len(rows)
    failed_rows = [row for row in rows if not bool(row.get("passed"))]
    false_positives = [
        row
        for row in rows
        if bool(row.get("phrase_preemption_hit"))
        and not bool(row.get("expected_phrase_preemption"))
    ]
    false_negatives = [
        row
        for row in rows
        if not bool(row.get("phrase_preemption_hit"))
        and bool(row.get("expected_phrase_preemption"))
    ]
    reason_counts = Counter(str(row.get("phrase_reason_code") or "") for row in rows)
    signal_counts: Counter[str] = Counter()
    for row in rows:
        signal_counts.update(str(code) for code in row.get("signal_codes", ()) if str(code))
    return {
        "case_count": case_count,
        "passed_case_count": case_count - len(failed_rows),
        "failed_case_count": len(failed_rows),
        "false_positive_count": len(false_positives),
        "false_negative_count": len(false_negatives),
        "failed_case_ids": [str(row.get("case_id") or "") for row in failed_rows],
        "false_positive_case_ids": [str(row.get("case_id") or "") for row in false_positives],
        "false_negative_case_ids": [str(row.get("case_id") or "") for row in false_negatives],
        "reason_code_counts": {key: value for key, value in sorted(reason_counts.items()) if key},
        "signal_code_counts": dict(sorted(signal_counts.items())),
    }


def _row_table(rows: object) -> str:
    materialized = [row for row in rows if isinstance(row, Mapping)]
    if not materialized:
        return "No rows."
    lines = [
        "| Case | Expected | Hit | Reason | Signals | Pass |",
        "| --- | ---: | ---: | --- | --- | ---: |",
    ]
    for row in materialized:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row.get('case_id', '')}`",
                    f"`{str(bool(row.get('expected_phrase_preemption'))).lower()}`",
                    f"`{str(bool(row.get('phrase_preemption_hit'))).lower()}`",
                    f"`{row.get('phrase_reason_code', '') or 'none'}`",
                    f"`{', '.join(row.get('signal_codes', ())) or 'none'}`",
                    f"`{str(bool(row.get('passed'))).lower()}`",
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _validate_case_suite(payload: Mapping[str, object]) -> None:
    if int(payload.get("schema_version") or 0) != 1:
        raise ValueError("Phrase signal case suite must declare schema_version=1.")
    if not str(payload.get("dataset_id") or "").strip():
        raise ValueError("Phrase signal case suite is missing `dataset_id`.")
    families = payload.get("families")
    if not isinstance(families, Sequence) or isinstance(families, (str, bytes)) or not families:
        raise ValueError("Phrase signal case suite must include a non-empty `families` list.")
    for family in families:
        if not isinstance(family, Mapping):
            raise ValueError("Phrase signal family entries must be objects.")
        family_id = str(family.get("family_id") or "").strip()
        family_pos_tags = family.get("family_pos_tags")
        if (
            not family_id
            or not isinstance(family_pos_tags, Sequence)
            or isinstance(family_pos_tags, (str, bytes))
            or not family_pos_tags
        ):
            raise ValueError("Each phrase signal family needs family_id and family_pos_tags.")
        cases = family.get("cases")
        if not isinstance(cases, Sequence) or isinstance(cases, (str, bytes)) or not cases:
            raise ValueError(f"Phrase signal family {family_id!r} has no cases.")
        for case in cases:
            if not isinstance(case, Mapping):
                raise ValueError(f"Phrase signal family {family_id!r} has a non-object case.")
            if (
                not str(case.get("case_id") or "").strip()
                or not str(case.get("sentence") or "").strip()
                or not str(case.get("source_phrase") or "").strip()
                or "expected_phrase_preemption" not in case
            ):
                raise ValueError(
                    f"Phrase signal family {family_id!r} has a case missing required fields."
                )


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def main() -> int:
    args = _parse_args()
    report = build_phrase_policy_signal_audit_report(case_suite_payload=_load_json(args.case_suite))
    _write_json(args.json_out, report)
    _write_text(args.markdown_out, render_phrase_policy_signal_audit_markdown(report))
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    return 1 if args.fail_on_review and report["status"] != "ok" else 0


if __name__ == "__main__":
    raise SystemExit(main())
