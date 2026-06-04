#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Iterable, Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEST_OUTPUTS_ROOT = PROJECT_ROOT / "docs" / "test_outputs"
DEFAULT_PAIR = "en-es"
DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / "pack_lifecycle_promotion_evidence_latest.json"
DEFAULT_MARKDOWN_OUT = TEST_OUTPUTS_ROOT / "pack_lifecycle_promotion_evidence_latest.md"
PACK_KIND_CHOICES = ("language", "frequency", "embedding", "semantic")
STATUS_ORDER = {"ok": 0, "review": 1, "error": 2}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate the artifact bundle required before promoting a managed pack "
            "candidate. This command reads existing evidence only; it does not mutate "
            "runtime data, docs, packs, or generated artifacts."
        )
    )
    parser.add_argument("--pack-id", required=True)
    parser.add_argument("--pack-kind", choices=PACK_KIND_CHOICES, required=True)
    parser.add_argument("--pair", default=DEFAULT_PAIR)
    parser.add_argument("--pack-lifecycle-json", type=Path, required=True)
    parser.add_argument("--source-readiness-json", type=Path)
    parser.add_argument("--srs-zipf-bridge-json", type=Path)
    parser.add_argument("--denominator-json", type=Path)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument(
        "--fail-on-review",
        action="store_true",
        help="Exit non-zero unless the whole evidence bundle is promotion-ready.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_promotion_evidence_report(
        pack_id=args.pack_id,
        pack_kind=args.pack_kind,
        pair=args.pair,
        pack_lifecycle_json=args.pack_lifecycle_json,
        source_readiness_json=args.source_readiness_json,
        srs_zipf_bridge_json=args.srs_zipf_bridge_json,
        denominator_json=args.denominator_json,
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.markdown_out.write_text(render_promotion_evidence_markdown(report), encoding="utf-8")
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    return promotion_evidence_exit_code(report, fail_on_review=bool(args.fail_on_review))


def build_promotion_evidence_report(
    *,
    pack_id: str,
    pack_kind: str,
    pair: str = DEFAULT_PAIR,
    pack_lifecycle_json: Path,
    source_readiness_json: Path | None = None,
    srs_zipf_bridge_json: Path | None = None,
    denominator_json: Path | None = None,
    generated_at: str | None = None,
) -> dict[str, object]:
    normalized_pack_id = str(pack_id or "").strip()
    normalized_kind = str(pack_kind or "").strip().lower()
    normalized_pair = str(pair or DEFAULT_PAIR).strip().lower() or DEFAULT_PAIR
    evidence = [
        _audit_pack_lifecycle_evidence(
            path=pack_lifecycle_json,
            pack_id=normalized_pack_id,
            pack_kind=normalized_kind,
        ),
        _audit_status_artifact(
            evidence_id="source_readiness_audit",
            path=source_readiness_json,
            required=normalized_kind == "frequency",
            expected_pair=normalized_pair,
            ok_decisions={"srs_corpus_expansion_candidates_audited"},
            missing_issue="source_readiness_json_missing",
            purpose="candidate corpus size, schema, POS, topic/domain, and target readiness",
        ),
        _audit_status_artifact(
            evidence_id="srs_zipf_bridge",
            path=srs_zipf_bridge_json,
            required=normalized_kind == "frequency",
            expected_pair=normalized_pair,
            ok_decisions={"srs_zipf_bridge_established"},
            missing_issue="srs_zipf_bridge_json_missing",
            purpose="expanded SRS target universe and source-target rulegen bridge",
        ),
        _audit_status_artifact(
            evidence_id="denominator_audit",
            path=denominator_json,
            required=normalized_kind == "frequency",
            expected_pair=normalized_pair,
            ok_decisions={"semantic_veto_denominator_audit_current"},
            missing_issue="denominator_json_missing",
            purpose="semantic-veto denominator accounting after candidate evaluation",
        ),
    ]
    required_count = sum(1 for row in evidence if row["required"])
    present_count = sum(1 for row in evidence if row["present"])
    ok_count = sum(1 for row in evidence if row["status"] == "ok")
    review_count = sum(1 for row in evidence if row["status"] == "review")
    error_count = sum(1 for row in evidence if row["status"] == "error")
    status = _worst_status(str(row["status"]) for row in evidence)
    blocking_issues = [
        issue
        for row in evidence
        if row["required"] and row["status"] != "ok"
        for issue in _string_sequence(row.get("issues"))
    ]
    return {
        "schema_version": 1,
        "generated_at": generated_at or _utc_now(),
        "decision": (
            "pack_promotion_evidence_ready"
            if status == "ok"
            else "pack_promotion_evidence_needs_review"
        ),
        "runtime_policy_change": "none",
        "mutation": "none",
        "pair": normalized_pair,
        "pack_id": normalized_pack_id,
        "pack_kind": normalized_kind,
        "status": status,
        "summary": {
            "required_count": required_count,
            "present_count": present_count,
            "ok_count": ok_count,
            "review_count": review_count,
            "error_count": error_count,
            "blocking_issue_count": len(blocking_issues),
        },
        "evidence": evidence,
        "blocking_issues": blocking_issues,
        "boundaries": [
            "This command does not approve source licenses.",
            "This command does not create, install, copy, or promote packs.",
            "This command does not replace the source-readiness, Zipf bridge, denominator, or lifecycle audits.",
        ],
    }


def render_promotion_evidence_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# Pack Promotion Evidence",
        "",
        f"- Generated at: `{report.get('generated_at')}`",
        f"- Pack: `{report.get('pack_kind')}` / `{report.get('pack_id')}`",
        f"- Pair: `{report.get('pair')}`",
        f"- Status: `{report.get('status')}`",
        f"- Decision: `{report.get('decision')}`",
        f"- Required evidence: `{summary.get('required_count')}`",
        f"- Present evidence: `{summary.get('present_count')}`",
        f"- Blocking issues: `{summary.get('blocking_issue_count')}`",
        "",
        "## Evidence",
        "",
        "| Evidence | Required | Present | Status | Path | Issues |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in _mapping_rows(report.get("evidence")):
        issues = ", ".join(_string_sequence(row.get("issues"))) or "none"
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{_escape_md(str(row.get('evidence_id') or ''))}`",
                    f"`{row.get('required')}`",
                    f"`{row.get('present')}`",
                    f"`{row.get('status')}`",
                    f"`{_escape_md(str(row.get('path') or ''))}`",
                    _escape_md(issues),
                ]
            )
            + " |"
        )
    blocking = _string_sequence(report.get("blocking_issues"))
    lines.extend(["", "## Blocking Issues", ""])
    if blocking:
        lines.extend(f"- `{issue}`" for issue in blocking)
    else:
        lines.append("- None.")
    lines.extend(["", "## Boundaries", ""])
    lines.extend(f"- {item}" for item in _string_sequence(report.get("boundaries")))
    return "\n".join(lines) + "\n"


def promotion_evidence_exit_code(
    report: Mapping[str, object],
    *,
    fail_on_review: bool = False,
) -> int:
    if fail_on_review and str(report.get("status") or "") != "ok":
        return 1
    return 0


def _audit_pack_lifecycle_evidence(
    *,
    path: Path,
    pack_id: str,
    pack_kind: str,
) -> dict[str, object]:
    row, payload = _load_artifact(
        evidence_id="pack_lifecycle_audit",
        path=path,
        required=True,
        missing_issue="pack_lifecycle_json_missing",
        purpose="installed manifest, artifact, provenance, and manual-path lifecycle state",
    )
    if payload is None:
        return row
    checks = list(_mapping_rows(row.get("checks")))
    summary = _as_mapping(payload.get("summary"))
    lifecycle_status = _normalize_status(summary.get("status"))
    _append_status_check(
        row,
        checks,
        check_id="summary_status",
        observed=lifecycle_status,
        ok=lifecycle_status == "ok",
        review_issue="pack_lifecycle_summary_not_ok",
    )
    review_count_present = "provenance_review_required_count" in summary
    _append_status_check(
        row,
        checks,
        check_id="provenance_review_required_count_present",
        observed=review_count_present,
        ok=review_count_present,
        review_issue="pack_lifecycle_provenance_review_count_missing",
    )
    review_count = _int_value(summary.get("provenance_review_required_count"))
    _append_status_check(
        row,
        checks,
        check_id="provenance_review_required_count",
        observed=review_count,
        ok=review_count == 0,
        review_issue="pack_lifecycle_provenance_review_required",
    )
    pack_row = _find_pack_row(payload, pack_id=pack_id, pack_kind=pack_kind)
    _append_status_check(
        row,
        checks,
        check_id="pack_found",
        observed=bool(pack_row),
        ok=bool(pack_row),
        review_issue="pack_lifecycle_pack_not_found",
        missing_is_error=True,
    )
    if pack_row:
        provenance_review = _as_mapping(pack_row.get("provenance_review"))
        provenance_policy = _as_mapping(pack_row.get("provenance_policy"))
        _append_status_check(
            row,
            checks,
            check_id="provenance_review_present",
            observed=bool(provenance_review),
            ok=bool(provenance_review),
            review_issue="pack_lifecycle_pack_provenance_review_missing",
        )
        _append_status_check(
            row,
            checks,
            check_id="manifest_exists",
            observed=bool(pack_row.get("manifest_exists")),
            ok=bool(pack_row.get("manifest_exists")),
            review_issue="pack_lifecycle_manifest_missing",
            missing_is_error=True,
        )
        _append_status_check(
            row,
            checks,
            check_id="artifact_exists",
            observed=bool(
                pack_row.get("artifact_exists") or pack_row.get("semantic_inventory_exists")
            ),
            ok=bool(pack_row.get("artifact_exists") or pack_row.get("semantic_inventory_exists")),
            review_issue="pack_lifecycle_artifact_missing",
            missing_is_error=True,
        )
        _append_status_check(
            row,
            checks,
            check_id="provenance_exists",
            observed=bool(pack_row.get("provenance_exists")),
            ok=bool(pack_row.get("provenance_exists")),
            review_issue="pack_lifecycle_provenance_missing",
        )
        _append_status_check(
            row,
            checks,
            check_id="provenance_valid",
            observed=bool(pack_row.get("provenance_valid")),
            ok=bool(pack_row.get("provenance_valid")),
            review_issue="pack_lifecycle_provenance_invalid",
            missing_is_error=True,
        )
        _append_status_check(
            row,
            checks,
            check_id="provenance_review_required",
            observed=bool(provenance_review.get("review_required")),
            ok=not bool(provenance_review.get("review_required")),
            review_issue="pack_lifecycle_pack_provenance_review_required",
        )
        _append_status_check(
            row,
            checks,
            check_id="provenance_policy_present",
            observed=bool(provenance_policy),
            ok=bool(provenance_policy),
            review_issue="pack_lifecycle_pack_provenance_policy_missing",
        )
        if provenance_policy:
            _append_status_check(
                row,
                checks,
                check_id="provenance_policy_status",
                observed=str(provenance_policy.get("status") or ""),
                ok=str(provenance_policy.get("status") or "") == "ok",
                review_issue="pack_lifecycle_pack_provenance_policy_not_ok",
            )
            _append_status_check(
                row,
                checks,
                check_id="provenance_policy_promotion_ready",
                observed=bool(provenance_policy.get("promotion_ready")),
                ok=bool(provenance_policy.get("promotion_ready")),
                review_issue="pack_lifecycle_pack_provenance_policy_not_ready",
            )
    row["checks"] = checks
    row["status"] = _worst_status(
        [str(row.get("status") or "ok"), *(str(check.get("status") or "ok") for check in checks)]
    )
    return row


def _audit_status_artifact(
    *,
    evidence_id: str,
    path: Path | None,
    required: bool,
    expected_pair: str,
    ok_decisions: set[str],
    missing_issue: str,
    purpose: str,
) -> dict[str, object]:
    row, payload = _load_artifact(
        evidence_id=evidence_id,
        path=path,
        required=required,
        missing_issue=missing_issue,
        purpose=purpose,
    )
    if payload is None:
        return row
    checks = list(_mapping_rows(row.get("checks")))
    status = _artifact_status(payload)
    _append_status_check(
        row,
        checks,
        check_id="artifact_status",
        observed=status,
        ok=status == "ok",
        review_issue=f"{evidence_id}_status_not_ok",
    )
    decision = str(payload.get("decision") or "").strip()
    if ok_decisions:
        _append_status_check(
            row,
            checks,
            check_id="decision",
            observed=decision,
            ok=decision in ok_decisions,
            review_issue=f"{evidence_id}_decision_unexpected",
        )
    pair = str(payload.get("pair") or "").strip().lower()
    if pair:
        _append_status_check(
            row,
            checks,
            check_id="pair",
            observed=pair,
            ok=pair == expected_pair,
            review_issue=f"{evidence_id}_pair_mismatch",
        )
    else:
        _append_status_check(
            row,
            checks,
            check_id="pair",
            observed="",
            ok=False,
            review_issue=f"{evidence_id}_pair_missing",
        )
    row["checks"] = checks
    row["status"] = _worst_status(
        [str(row.get("status") or "ok"), *(str(check.get("status") or "ok") for check in checks)]
    )
    return row


def _load_artifact(
    *,
    evidence_id: str,
    path: Path | None,
    required: bool,
    missing_issue: str,
    purpose: str,
) -> tuple[dict[str, object], Mapping[str, object] | None]:
    resolved = Path(path).expanduser().resolve(strict=False) if path else None
    row: dict[str, object] = {
        "evidence_id": evidence_id,
        "required": required,
        "purpose": purpose,
        "path": str(resolved) if resolved else "",
        "present": bool(resolved and resolved.exists()),
        "status": "ok",
        "checks": [],
        "issues": [],
    }
    if not resolved:
        if required:
            row["status"] = "error"
            row["issues"] = [missing_issue]
        else:
            row["status"] = "ok"
            row["issues"] = ["optional_evidence_not_supplied"]
        return row, None
    if not resolved.exists() or not resolved.is_file():
        row["status"] = "error" if required else "review"
        row["issues"] = [missing_issue]
        return row, None
    try:
        payload = json.loads(resolved.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        row["status"] = "error"
        row["issues"] = [f"artifact_unreadable:{exc.__class__.__name__}"]
        return row, None
    if not isinstance(payload, Mapping):
        row["status"] = "error"
        row["issues"] = ["artifact_json_not_object"]
        return row, None
    return row, payload


def _append_status_check(
    row: dict[str, object],
    checks: list[dict[str, object]],
    *,
    check_id: str,
    observed: object,
    ok: bool,
    review_issue: str,
    missing_is_error: bool = False,
) -> None:
    status = "ok" if ok else "error" if missing_is_error else "review"
    checks.append(
        {
            "check_id": check_id,
            "status": status,
            "observed": observed,
        }
    )
    if status != "ok":
        issues = list(_string_sequence(row.get("issues")))
        issues.append(review_issue)
        row["issues"] = issues


def _find_pack_row(
    payload: Mapping[str, object],
    *,
    pack_id: str,
    pack_kind: str,
) -> Mapping[str, object] | None:
    if pack_kind == "semantic":
        for candidate in _mapping_rows(
            _as_mapping(payload.get("semantic_pack_copies")).get("packs")
        ):
            if str(candidate.get("pack_id") or "") == pack_id:
                return candidate
        return None
    family = _as_mapping(_as_mapping(payload.get("installed_pack_families")).get(pack_kind))
    for candidate in _mapping_rows(family.get("packs")):
        if str(candidate.get("pack_id") or "") == pack_id:
            return candidate
    return None


def _artifact_status(payload: Mapping[str, object]) -> str:
    for value in (
        payload.get("status"),
        _as_mapping(payload.get("summary")).get("status"),
        payload.get("overall_status"),
    ):
        status = _normalize_status(value)
        if status:
            return status
    return "review"


def _normalize_status(value: object) -> str:
    text = str(value or "").strip().lower()
    if text in {"ok", "pass", "passed", "success", "succeeded"}:
        return "ok"
    if text in {"review", "warn", "warning", "needs_review"}:
        return "review"
    if text in {"error", "fail", "failed", "failure"}:
        return "error"
    return ""


def _worst_status(values: Iterable[object]) -> str:
    statuses = [status for status in (_normalize_status(value) for value in values) if status]
    if not statuses:
        return "review"
    return max(statuses, key=lambda status: STATUS_ORDER[status])


def _mapping_rows(value: object) -> list[Mapping[str, object]]:
    return [item for item in _sequence(value) if isinstance(item, Mapping)]


def _sequence(value: object) -> list[object]:
    if value is None:
        return []
    if isinstance(value, (str, bytes)):
        return []
    if isinstance(value, Sequence):
        return list(value)
    return []


def _string_sequence(value: object) -> list[str]:
    if isinstance(value, str):
        return [value] if value else []
    return [str(item) for item in _sequence(value) if str(item)]


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _int_value(value: object) -> int:
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 0


def _escape_md(value: str) -> str:
    return value.replace("|", "\\|")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


if __name__ == "__main__":
    raise SystemExit(main())
