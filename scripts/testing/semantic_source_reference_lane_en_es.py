#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Mapping


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DOCS_ROOT = PROJECT_ROOT / "docs"
TEST_OUTPUTS_ROOT = DOCS_ROOT / "test_outputs"
DEFAULT_MANIFEST = (
    DOCS_ROOT / "test_inputs" / "semantic_routing" / "semantic_source_reference_lane_en_es_v1.json"
)
DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / "semantic_source_reference_lane_latest.json"
DEFAULT_MARKDOWN_OUT = TEST_OUTPUTS_ROOT / "semantic_source_reference_lane_latest.md"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate the frozen en-es offline semantic source reference lane against "
            "its source-cycle, held-out, and admitted-evidence artifacts."
        )
    )
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--fail-on-review", action="store_true")
    return parser.parse_args()


def build_source_reference_lane_report(
    *,
    manifest_payload: Mapping[str, object],
    source_cycle_payload: Mapping[str, object],
    heldout_payload: Mapping[str, object],
    evidence_batch_payload: Mapping[str, object],
    phrase_heldout_payload: Mapping[str, object] | None = None,
    generated_at: str | None = None,
) -> dict[str, object]:
    if generated_at is None:
        generated_at = _utc_now()
    checks = [
        *_source_cycle_checks(manifest_payload, source_cycle_payload),
        *_heldout_checks(manifest_payload, heldout_payload),
        *_optional_phrase_heldout_checks(manifest_payload, phrase_heldout_payload),
        *_evidence_batch_checks(manifest_payload, evidence_batch_payload),
    ]
    failed_checks = [check for check in checks if check["status"] != "ok"]
    status = "ok" if not failed_checks else "review"
    return {
        "schema_version": 1,
        "status": status,
        "decision": "reference_lane_frozen" if status == "ok" else "reference_lane_review",
        "generated_at": generated_at,
        "pair": str(manifest_payload.get("pair") or "").strip() or "en-es",
        "lane_id": str(manifest_payload.get("lane_id") or "").strip(),
        "configured_lane": dict(_as_mapping(manifest_payload.get("configured_lane"))),
        "phrase_policy_candidate_lane": dict(
            _as_mapping(manifest_payload.get("phrase_policy_candidate_lane"))
        ),
        "artifacts": dict(_as_mapping(manifest_payload.get("artifacts"))),
        "known_non_runtime_blockers": list(
            manifest_payload.get("known_non_runtime_blockers") or ()
        ),
        "summary": {
            "check_count": len(checks),
            "failed_check_count": len(failed_checks),
            "source_cycle_status": source_cycle_payload.get("status", ""),
            "source_cycle_decision": source_cycle_payload.get("decision", ""),
            "heldout_status": heldout_payload.get("status", ""),
            "heldout_decision": heldout_payload.get("decision", ""),
            "phrase_heldout_status": phrase_heldout_payload.get("status", "")
            if isinstance(phrase_heldout_payload, Mapping)
            else "",
            "phrase_heldout_decision": phrase_heldout_payload.get("decision", "")
            if isinstance(phrase_heldout_payload, Mapping)
            else "",
            "evidence_row_count": int(evidence_batch_payload.get("row_count") or 0),
        },
        "checks": checks,
        "failed_checks": failed_checks,
    }


def render_source_reference_lane_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# en-es Semantic Source Reference Lane",
        "",
        f"- Status: `{report.get('status', 'unknown')}`",
        f"- Decision: `{report.get('decision', '')}`",
        f"- Generated: `{report.get('generated_at', '')}`",
        f"- Lane: `{report.get('lane_id', '')}`",
        f"- Checks: `{summary.get('check_count', 0)}`",
        f"- Failed checks: `{summary.get('failed_check_count', 0)}`",
        "",
        "## Artifacts",
        "",
    ]
    artifacts = _as_mapping(report.get("artifacts"))
    for key, value in artifacts.items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Configured Lane", ""])
    configured = _as_mapping(report.get("configured_lane"))
    for key, value in configured.items():
        lines.append(f"- {key}: `{value}`")
    phrase_candidate = _as_mapping(report.get("phrase_policy_candidate_lane"))
    if phrase_candidate:
        lines.extend(["", "## Phrase Policy Candidate Lane", ""])
        for key, value in phrase_candidate.items():
            lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Checks", "", _check_table(report.get("checks", ()))])
    blockers = report.get("known_non_runtime_blockers") or ()
    if blockers:
        lines.extend(["", "## Non-runtime Blockers", ""])
        lines.extend(f"- `{blocker}`" for blocker in blockers)
    failed = [check for check in report.get("failed_checks", ()) if isinstance(check, Mapping)]
    if failed:
        lines.extend(["", "## Failed Checks", ""])
        for check in failed:
            lines.append(
                f"- `{check.get('check_id', '')}` expected `{check.get('expected', '')}` "
                f"but found `{check.get('actual', '')}`"
            )
    return "\n".join(lines) + "\n"


def _source_cycle_checks(
    manifest: Mapping[str, object],
    payload: Mapping[str, object],
) -> list[dict[str, object]]:
    expected = _as_mapping(_as_mapping(manifest.get("expected")).get("source_cycle"))
    summary = _as_mapping(payload.get("summary"))
    policy = _as_mapping(payload.get("policy"))
    heldout = _as_mapping(summary.get("heldout_validation"))
    best = _as_mapping(summary.get("best_ablation_row"))
    configured = _as_mapping(manifest.get("configured_lane"))
    checks = [
        _check("source_cycle.status", payload.get("status"), expected.get("status")),
        _check("source_cycle.decision", payload.get("decision"), expected.get("decision")),
        _check(
            "source_cycle.offline_promotion_lane",
            policy.get("offline_promotion_lane"),
            expected.get("offline_promotion_lane"),
        ),
        _check(
            "source_cycle.offline_semantic_lane_status",
            policy.get("offline_semantic_lane_status"),
            expected.get("offline_semantic_lane_status"),
        ),
        _check(
            "source_cycle.runtime_publication_status",
            policy.get("runtime_publication_status"),
            expected.get("runtime_publication_status"),
        ),
        _check(
            "source_cycle.runtime_publication_blockers",
            list(_as_sequence(policy.get("runtime_publication_blockers"))),
            list(_as_sequence(expected.get("runtime_publication_blockers"))),
        ),
        _check(
            "source_cycle.heldout_validation_status",
            heldout.get("status"),
            expected.get("heldout_validation_status"),
        ),
        _check(
            "source_cycle.heldout_validation_decision",
            heldout.get("decision"),
            expected.get("heldout_validation_decision"),
        ),
        _check(
            "source_cycle.heldout_validation_passed",
            heldout.get("passed"),
            expected.get("heldout_validation_passed"),
        ),
        _check(
            "source_cycle.leakage_rejected_row_count",
            summary.get("leakage_rejected_row_count"),
            expected.get("leakage_rejected_row_count"),
        ),
        _check(
            "source_cycle.sense_rejected_row_count",
            summary.get("sense_rejected_row_count"),
            expected.get("sense_rejected_row_count"),
        ),
        _check(
            "source_cycle.final_admitted_row_count",
            summary.get("final_admitted_row_count"),
            expected.get("final_admitted_row_count"),
        ),
        _check(
            "source_cycle.families_total",
            summary.get("families_total"),
            expected.get("families_total"),
        ),
        _check(
            "source_cycle.semantic_contract_complete_family_count",
            summary.get("semantic_contract_complete_family_count"),
            expected.get("semantic_contract_complete_family_count"),
        ),
        _check(
            "source_cycle.phrase_contract_complete_family_count",
            summary.get("phrase_contract_complete_family_count"),
            expected.get("phrase_contract_complete_family_count"),
        ),
        _check(
            "source_cycle.best_ablation_cases_total",
            best.get("cases_total"),
            expected.get("best_ablation_cases_total"),
        ),
        _check(
            "source_cycle.best_ablation_harmful_replace_count",
            best.get("harmful_replace_count"),
            expected.get("best_ablation_harmful_replace_count"),
        ),
        _check(
            "source_cycle.best_ablation_false_abstain_count",
            best.get("false_abstain_count"),
            expected.get("best_ablation_false_abstain_count"),
        ),
        _check(
            "source_cycle.best_ablation_replace_recall",
            best.get("replace_recall"),
            expected.get("best_ablation_replace_recall"),
            tolerance=0.0001,
        ),
        _check(
            "source_cycle.best_ablation_decision_accuracy",
            best.get("decision_accuracy"),
            expected.get("best_ablation_decision_accuracy"),
            tolerance=0.0001,
        ),
    ]
    for key in (
        "source_mode",
        "scorer_id",
        "context_view",
        "min_active_score",
        "min_margin",
        "decision_shape",
    ):
        checks.append(
            _check(f"source_cycle.configured_lane.{key}", best.get(key), configured.get(key))
        )
    return checks


def _heldout_checks(
    manifest: Mapping[str, object],
    payload: Mapping[str, object],
    *,
    expected_key: str = "heldout_validation",
    configured_lane_key: str = "configured_lane",
    check_prefix: str = "heldout",
) -> list[dict[str, object]]:
    expected = _as_mapping(_as_mapping(manifest.get("expected")).get(expected_key))
    if not expected:
        return []
    summary = _as_mapping(payload.get("summary"))
    configured = _as_mapping(manifest.get(configured_lane_key))
    if not configured:
        configured = _as_mapping(manifest.get("configured_lane"))
    heldout_config = _as_mapping(payload.get("configured_lane"))
    checks = [
        _check(f"{check_prefix}.status", payload.get("status"), expected.get("status")),
        _check(f"{check_prefix}.decision", payload.get("decision"), expected.get("decision")),
        _check(
            f"{check_prefix}.family_count",
            summary.get("family_count"),
            expected.get("family_count"),
        ),
        _check(f"{check_prefix}.case_count", summary.get("case_count"), expected.get("case_count")),
        _check(
            f"{check_prefix}.harmful_replace_count",
            summary.get("harmful_replace_count"),
            expected.get("harmful_replace_count"),
        ),
        _check(
            f"{check_prefix}.false_abstain_count",
            summary.get("false_abstain_count"),
            expected.get("false_abstain_count"),
        ),
        _check(
            f"{check_prefix}.replace_recall",
            summary.get("replace_recall"),
            expected.get("replace_recall"),
            tolerance=0.0001,
        ),
        _check(
            f"{check_prefix}.decision_accuracy",
            summary.get("decision_accuracy"),
            expected.get("decision_accuracy"),
            tolerance=0.0001,
        ),
    ]
    for key in ("scorer_id", "context_view", "min_active_score", "min_margin", "decision_shape"):
        checks.append(
            _check(
                f"{check_prefix}.configured_lane.{key}",
                heldout_config.get(key),
                configured.get(key),
            )
        )
    return checks


def _optional_phrase_heldout_checks(
    manifest: Mapping[str, object],
    payload: Mapping[str, object] | None,
) -> list[dict[str, object]]:
    expected = _as_mapping(_as_mapping(manifest.get("expected")).get("phrase_heldout_validation"))
    if not expected:
        return []
    if not isinstance(payload, Mapping):
        return [_check("phrase_heldout.artifact_present", False, True)]
    return _heldout_checks(
        manifest,
        payload,
        expected_key="phrase_heldout_validation",
        configured_lane_key="phrase_policy_candidate_lane",
        check_prefix="phrase_heldout",
    )


def _evidence_batch_checks(
    manifest: Mapping[str, object],
    payload: Mapping[str, object],
) -> list[dict[str, object]]:
    expected = _as_mapping(_as_mapping(manifest.get("expected")).get("evidence_batch"))
    relation_counts = _relation_type_counts(payload)
    rows = [row for row in payload.get("rows", ()) if isinstance(row, Mapping)]
    plant_related_active_count = sum(
        1
        for row in rows
        if str(row.get("relation_type") or "") == "anchor_cue"
        and _as_mapping(row.get("metadata")).get("family_id") == "en-es:sentence-veto:plant:planta"
        and _as_mapping(row.get("metadata")).get("wordnet_source_relation") == "direct_hyponym"
    )
    cell_depth_related_active_count = sum(
        1
        for row in rows
        if str(row.get("relation_type") or "") == "anchor_cue"
        and _as_mapping(row.get("metadata")).get("family_id") == "en-es:sentence-veto:cell:celula"
        and len(_as_sequence(_as_mapping(row.get("metadata")).get("wordnet_relation_path"))) >= 3
    )
    checks = [
        _check("evidence.source_id", payload.get("source_id"), expected.get("source_id")),
        _check("evidence.batch_id", payload.get("batch_id"), expected.get("batch_id")),
        _check("evidence.row_count", payload.get("row_count"), expected.get("row_count")),
    ]
    for relation_type, count in _as_mapping(expected.get("relation_type_counts")).items():
        checks.append(
            _check(
                f"evidence.relation_type.{relation_type}",
                relation_counts.get(relation_type, 0),
                count,
            )
        )
    checks.append(
        _check_minimum(
            "evidence.plant_active_related_wordnet_min_count",
            plant_related_active_count,
            expected.get("plant_active_related_wordnet_min_count"),
        )
    )
    if expected.get("cell_active_related_wordnet_depth2_plus_min_count") is not None:
        checks.append(
            _check_minimum(
                "evidence.cell_active_related_wordnet_depth2_plus_min_count",
                cell_depth_related_active_count,
                expected.get("cell_active_related_wordnet_depth2_plus_min_count"),
            )
        )
    return checks


def _check(
    check_id: str,
    actual: object,
    expected: object,
    *,
    tolerance: float = 0.0,
) -> dict[str, object]:
    if tolerance:
        passed = abs(_float(actual) - _float(expected)) <= tolerance
    else:
        passed = actual == expected
    return {
        "check_id": check_id,
        "status": "ok" if passed else "review",
        "actual": actual,
        "expected": expected,
    }


def _check_minimum(check_id: str, actual: object, minimum: object) -> dict[str, object]:
    passed = _float(actual) >= _float(minimum)
    return {
        "check_id": check_id,
        "status": "ok" if passed else "review",
        "actual": actual,
        "expected": f">= {minimum}",
    }


def _relation_type_counts(payload: Mapping[str, object]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in payload.get("rows", ()):
        if not isinstance(row, Mapping):
            continue
        relation_type = str(row.get("relation_type") or "").strip()
        if relation_type:
            counts[relation_type] = counts.get(relation_type, 0) + 1
    return counts


def _check_table(checks: object) -> str:
    materialized = [check for check in checks if isinstance(check, Mapping)]
    if not materialized:
        return "No checks."
    lines = [
        "| Check | Status | Expected | Actual |",
        "| --- | --- | --- | --- |",
    ]
    for check in materialized:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{check.get('check_id', '')}`",
                    f"`{check.get('status', '')}`",
                    f"`{check.get('expected', '')}`",
                    f"`{check.get('actual', '')}`",
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _as_sequence(value: object) -> tuple[object, ...]:
    if isinstance(value, (str, bytes)):
        return ()
    if isinstance(value, (list, tuple)):
        return tuple(value)
    return ()


def _float(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _load_json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object in {path}.")
    return payload


def _resolve_repo_path(value: object) -> Path:
    path = Path(str(value or "").strip())
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def _write_json(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def main() -> int:
    args = _parse_args()
    manifest = _load_json(args.manifest)
    artifacts = _as_mapping(manifest.get("artifacts"))
    phrase_heldout_path = artifacts.get("phrase_heldout_validation_json")
    phrase_heldout_payload = (
        _load_json(_resolve_repo_path(phrase_heldout_path)) if phrase_heldout_path else None
    )
    report = build_source_reference_lane_report(
        manifest_payload=manifest,
        source_cycle_payload=_load_json(_resolve_repo_path(artifacts.get("source_cycle_json"))),
        heldout_payload=_load_json(_resolve_repo_path(artifacts.get("heldout_validation_json"))),
        evidence_batch_payload=_load_json(
            _resolve_repo_path(artifacts.get("admitted_evidence_batch_json"))
        ),
        phrase_heldout_payload=phrase_heldout_payload,
    )
    _write_json(args.json_out, report)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.write_text(render_source_reference_lane_markdown(report), encoding="utf-8")
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    if args.fail_on_review and report.get("status") != "ok":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
