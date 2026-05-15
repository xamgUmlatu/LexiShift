from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping, Sequence


PACK_PROVENANCE_POLICY_ID = "pack_provenance_promotion_policy"
PACK_PROVENANCE_POLICY_VERSION = 2
FREQUENCY_METRIC_KEYS = (
    "row_count",
    "distinct_lemma_count",
    "pos_rows",
    "topic_domain_rows",
)
SOURCE_BUNDLE_PROMOTION_LINEAGE_STATUSES = (
    "pinned_snapshot",
    "pinned_component_artifacts",
)


def audit_provenance_policy(
    *,
    provenance_path: Path,
    pack_kind: str,
    provenance_errors: Sequence[str] = (),
) -> dict[str, object]:
    payload, load_errors = _load_json_object(provenance_path)
    source = _as_mapping(payload.get("source"))
    artifact = _as_mapping(payload.get("artifact"))
    raw_artifacts = [_as_mapping(item) for item in _sequence(source.get("raw_artifacts"))]
    source_bundle = _as_mapping(source.get("source_bundle"))
    source_bundle_components = [
        _as_mapping(item) for item in _sequence(source_bundle.get("components"))
    ]
    source_bundle_lineage_status = str(source_bundle.get("lineage_status") or "").strip()
    metrics = _as_mapping(artifact.get("metrics"))

    license_status = str(source.get("license_status") or "").strip()
    source_pointer_kind = _source_pointer_kind(source)
    source_identity_kind = _source_identity_kind(source)
    raw_artifact_checksum_count = sum(1 for item in raw_artifacts if _has_checksum(item))
    artifact_checksum_present = _has_checksum(artifact)
    source_bundle_component_checksum_count = sum(
        1 for item in source_bundle_components if _has_checksum(item)
    )
    source_bundle_component_pointer_count = sum(
        1 for item in source_bundle_components if _component_pointer_kind(item)
    )

    checks: list[dict[str, object]] = []
    _append_check(
        checks,
        check_id="provenance_exists",
        ok=provenance_path.exists(),
        observed=provenance_path.exists(),
        review_reason="missing_provenance",
        error=True,
    )
    _append_check(
        checks,
        check_id="provenance_valid",
        ok=not (load_errors or provenance_errors),
        observed=not (load_errors or provenance_errors),
        review_reason="invalid_provenance",
        error=True,
    )
    if provenance_path.exists() and not (load_errors or provenance_errors):
        _append_check(
            checks,
            check_id="license_confirmed",
            ok=license_status == "confirmed",
            observed=license_status or "missing",
            review_reason=f"license_status_{license_status or 'missing'}",
        )
        _append_check(
            checks,
            check_id="source_pointer_present",
            ok=bool(source_pointer_kind),
            observed=source_pointer_kind or "missing",
            review_reason="missing_source_pointer",
        )
        _append_check(
            checks,
            check_id="source_identity_present",
            ok=bool(source_identity_kind),
            observed=source_identity_kind or "missing",
            review_reason="missing_source_identity",
        )
        _append_check(
            checks,
            check_id="raw_artifacts_present",
            ok=bool(raw_artifacts),
            observed=len(raw_artifacts),
            review_reason="missing_raw_artifacts",
        )
        if raw_artifacts:
            _append_check(
                checks,
                check_id="raw_artifact_checksums_complete",
                ok=raw_artifact_checksum_count == len(raw_artifacts),
                observed=f"{raw_artifact_checksum_count}/{len(raw_artifacts)}",
                review_reason="raw_artifact_checksum_missing",
            )
        _append_check(
            checks,
            check_id="generated_artifact_checksum_present",
            ok=artifact_checksum_present,
            observed=artifact_checksum_present,
            review_reason="generated_artifact_checksum_missing",
        )
        if source_bundle_components:
            _append_check(
                checks,
                check_id="source_bundle_component_pointers_complete",
                ok=source_bundle_component_pointer_count == len(source_bundle_components),
                observed=f"{source_bundle_component_pointer_count}/{len(source_bundle_components)}",
                review_reason="source_bundle_component_pointer_missing",
            )
            _append_check(
                checks,
                check_id="source_bundle_component_checksums_complete",
                ok=source_bundle_component_checksum_count == len(source_bundle_components),
                observed=f"{source_bundle_component_checksum_count}/{len(source_bundle_components)}",
                review_reason="source_bundle_component_checksum_missing",
            )
            _append_check(
                checks,
                check_id="source_bundle_pinning_declared",
                ok=source_bundle_lineage_status in SOURCE_BUNDLE_PROMOTION_LINEAGE_STATUSES,
                observed=source_bundle_lineage_status or "missing",
                review_reason="source_bundle_pinning_missing",
                detail={
                    "accepted_lineage_statuses": list(SOURCE_BUNDLE_PROMOTION_LINEAGE_STATUSES),
                },
            )
        if str(pack_kind or "").strip() == "frequency":
            missing_metric_keys = tuple(key for key in FREQUENCY_METRIC_KEYS if key not in metrics)
            _append_check(
                checks,
                check_id="frequency_metrics_complete",
                ok=not missing_metric_keys,
                observed=sorted(str(key) for key in metrics),
                review_reason="frequency_metrics_missing",
                detail={"missing_metric_keys": list(missing_metric_keys)},
            )

    status = _worst_status(checks)
    review_reasons = [
        str(check.get("review_reason") or "")
        for check in checks
        if str(check.get("review_reason") or "").strip() and str(check.get("status") or "") != "ok"
    ]
    return {
        "policy_id": PACK_PROVENANCE_POLICY_ID,
        "policy_version": PACK_PROVENANCE_POLICY_VERSION,
        "status": status,
        "promotion_ready": status == "ok",
        "review_required": bool(review_reasons),
        "review_reasons": review_reasons,
        "source_name": str(source.get("source_name") or "").strip(),
        "license_status": license_status,
        "source_pointer_kind": source_pointer_kind,
        "source_identity_kind": source_identity_kind,
        "raw_artifact_count": len(raw_artifacts),
        "raw_artifact_checksum_count": raw_artifact_checksum_count,
        "artifact_checksum_present": artifact_checksum_present,
        "artifact_metrics_present": bool(metrics),
        "artifact_metric_keys": sorted(str(key) for key in metrics),
        "source_bundle_component_count": len(source_bundle_components),
        "source_bundle_component_checksum_count": source_bundle_component_checksum_count,
        "source_bundle_component_pointer_count": source_bundle_component_pointer_count,
        "source_bundle_lineage_status": source_bundle_lineage_status,
        "checks": checks,
    }


def _append_check(
    checks: list[dict[str, object]],
    *,
    check_id: str,
    ok: bool,
    observed: object,
    review_reason: str,
    error: bool = False,
    detail: Mapping[str, object] | None = None,
) -> None:
    status = "ok" if ok else "error" if error else "review"
    row: dict[str, object] = {
        "check_id": check_id,
        "status": status,
        "observed": observed,
    }
    if status != "ok":
        row["review_reason"] = review_reason
    if detail:
        row.update(dict(detail))
    checks.append(row)


def _worst_status(checks: Sequence[Mapping[str, object]]) -> str:
    statuses = {str(check.get("status") or "ok") for check in checks}
    if "error" in statuses:
        return "error"
    if "review" in statuses:
        return "review"
    return "ok"


def _source_pointer_kind(source: Mapping[str, object]) -> str:
    if str(source.get("source_url") or "").strip():
        return "source_url"
    if str(source.get("local_source_path") or "").strip():
        return "local_source_path"
    return ""


def _source_identity_kind(source: Mapping[str, object]) -> str:
    if str(source.get("source_version") or "").strip():
        return "source_version"
    if str(source.get("source_dump") or "").strip():
        return "source_dump"
    if _as_mapping(source.get("source_bundle")):
        return "source_bundle"
    return ""


def _component_pointer_kind(component: Mapping[str, object]) -> str:
    if str(component.get("source_url") or "").strip():
        return "source_url"
    if str(component.get("local_source_path") or "").strip():
        return "local_source_path"
    if str(component.get("build_ref") or "").strip():
        return "build_ref"
    return ""


def _has_checksum(payload: Mapping[str, object]) -> bool:
    return bool(str(payload.get("sha1") or "").strip() or str(payload.get("sha256") or "").strip())


def _load_json_object(path: Path) -> tuple[dict[str, object], list[str]]:
    if not path.exists() or not path.is_file():
        return {}, []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {}, [f"invalid_json:{exc}"]
    if not isinstance(payload, Mapping):
        return {}, ["not_json_object"]
    return dict(payload), []


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
