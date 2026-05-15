from __future__ import annotations

import json
from typing import Mapping, Sequence


def build_source_policy_decision_report(
    *,
    family_reports: Mapping[str, object],
    semantic_report: Mapping[str, object],
) -> dict[str, object]:
    rows: list[dict[str, object]] = []
    for family_name, row in _iter_pack_rows(family_reports, semantic_report):
        policy = _as_mapping(row.get("provenance_policy"))
        for raw_check in _sequence(policy.get("checks")):
            check = _as_mapping(raw_check)
            status = str(check.get("status") or "").strip()
            if not status or status == "ok":
                continue
            review_reason = str(check.get("review_reason") or "").strip()
            check_id = str(check.get("check_id") or "").strip()
            category = _source_policy_category(review_reason, check_id)
            rows.append(
                {
                    "family": family_name,
                    "pack_id": str(row.get("pack_id") or ""),
                    "pack_kind": str(row.get("pack_kind") or family_name),
                    "provenance_path": str(row.get("provenance_path") or ""),
                    "policy_status": str(policy.get("status") or ""),
                    "check_id": check_id,
                    "check_status": status,
                    "review_reason": review_reason,
                    "category": category,
                    "recommended_action": _source_policy_recommended_action(
                        category,
                        review_reason,
                    ),
                    "observed": check.get("observed"),
                }
            )
    return {
        "decision": "source_policy_review_only",
        "runtime_policy_change": "none",
        "decision_count": len(rows),
        "category_counts": _count_by_key(rows, "category"),
        "recommended_action_counts": _count_by_key(rows, "recommended_action"),
        "rows": rows,
    }


def source_policy_summary_fields(source_policy_report: Mapping[str, object]) -> dict[str, object]:
    return {
        "source_policy_decision_count": int(source_policy_report.get("decision_count") or 0),
        "source_policy_category_counts": dict(
            _as_mapping(source_policy_report.get("category_counts"))
        ),
    }


def render_source_policy_decision_markdown(report: Mapping[str, object]) -> list[str]:
    source_policy = _as_mapping(report.get("source_policy_decisions"))
    source_policy_rows = _sequence(source_policy.get("rows"))
    lines = [
        "## Source Policy Decision Queue",
        "",
        f"- Decision items: `{source_policy.get('decision_count') or 0}`",
        "",
    ]
    if source_policy_rows:
        lines.extend(
            [
                "| Family | Pack | Category | Review Reason | Recommended Action | Observed |",
                "| --- | --- | --- | --- | --- | --- |",
            ]
        )
        for raw_row in source_policy_rows:
            row = _as_mapping(raw_row)
            lines.append(
                "| "
                f"{row.get('family')} | "
                f"{row.get('pack_id')} | "
                f"{row.get('category')} | "
                f"{row.get('review_reason')} | "
                f"{row.get('recommended_action')} | "
                f"{_markdown_cell(row.get('observed'))} |"
            )
        lines.append("")
    else:
        lines.extend(["- No source policy decisions are queued.", ""])
    return lines


def _iter_pack_rows(
    family_reports: Mapping[str, object],
    semantic_report: Mapping[str, object],
) -> list[tuple[str, Mapping[str, object]]]:
    rows: list[tuple[str, Mapping[str, object]]] = []
    families = _as_mapping(family_reports)
    for family_name, raw_family in families.items():
        family = _as_mapping(raw_family)
        for row in _sequence(family.get("packs")):
            rows.append((str(family_name), _as_mapping(row)))
    semantic = _as_mapping(semantic_report)
    for row in _sequence(semantic.get("packs")):
        rows.append(("semantic", _as_mapping(row)))
    return rows


def _source_policy_category(review_reason: str, check_id: str) -> str:
    reason = str(review_reason or "").strip()
    check = str(check_id or "").strip()
    if reason.startswith("license_status_"):
        return "license_review"
    if reason in {"missing_provenance", "invalid_provenance"}:
        return "provenance_sidecar"
    if reason == "missing_source_pointer":
        return "source_pointer"
    if reason == "missing_source_identity":
        return "source_identity"
    if reason in {"missing_raw_artifacts", "raw_artifact_checksum_missing"}:
        return "raw_artifact_checksum"
    if reason == "generated_artifact_checksum_missing":
        return "generated_artifact_checksum"
    if reason == "source_bundle_component_pointer_missing":
        return "source_bundle_pointer"
    if reason == "source_bundle_component_checksum_missing":
        return "source_bundle_checksum"
    if reason == "source_bundle_pinning_missing":
        return "source_bundle_pinning"
    if reason == "frequency_metrics_missing":
        return "frequency_metrics"
    if check:
        return check
    return "unknown"


def _source_policy_recommended_action(category: str, review_reason: str) -> str:
    if category == "license_review":
        if review_reason in {"license_status_not_redistributable", "license_status_internal_only"}:
            return "keep_non_promotable_or_internal"
        return "record_source_license_decision"
    actions = {
        "provenance_sidecar": "write_or_fix_provenance_sidecar",
        "source_pointer": "record_source_url_or_local_source_path",
        "source_identity": "choose_source_version_dump_or_bundle_policy",
        "raw_artifact_checksum": "capture_raw_artifact_checksums",
        "generated_artifact_checksum": "record_generated_artifact_checksum",
        "source_bundle_pointer": "record_source_bundle_component_pointers",
        "source_bundle_checksum": "capture_source_bundle_component_checksums",
        "source_bundle_pinning": "record_source_bundle_pinning_decision",
        "frequency_metrics": "write_or_refresh_frequency_metrics",
    }
    return actions.get(category, "review_source_policy_gap")


def _count_by_key(rows: Sequence[Mapping[str, object]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        value = str(row.get(key) or "").strip() or "missing"
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def _markdown_cell(value: object) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, (int, float, str)):
        return str(value).replace("|", "\\|")
    return json.dumps(value, ensure_ascii=False, sort_keys=True).replace("|", "\\|")


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _sequence(value: object) -> list[object]:
    if value is None:
        return []
    if isinstance(value, (str, bytes)):
        return []
    if isinstance(value, Sequence):
        return list(value)
    return []
