#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from typing import Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / "core"
TEST_OUTPUTS_ROOT = PROJECT_ROOT / "docs" / "test_outputs"
if str(CORE_ROOT) not in sys.path:
    sys.path.insert(0, str(CORE_ROOT))
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from lexishift_core.helper.pack_provenance import (  # noqa: E402
    LICENSE_STATUS_VALUES,
    validate_pack_provenance_payload,
)
from pack_lifecycle_manual_resources import manual_path_format_support  # noqa: E402


DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / "pack_lifecycle_external_import_plan_latest.json"
DEFAULT_MARKDOWN_OUT = TEST_OUTPUTS_ROOT / "pack_lifecycle_external_import_plan_latest.md"

FAMILY_FIELD_NAMES = {
    "language": "language_pack_paths",
    "frequency": "frequency_pack_paths",
    "embedding": "embedding_pack_paths",
}
PROMOTION_LICENSE_STATUS = "confirmed"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Preflight a manually acquired external pack path. The command is read-only: "
            "it validates the exact supported artifact shape and reports provenance/import "
            "requirements without copying files, rewriting settings, or promoting a pack."
        )
    )
    parser.add_argument("--family", choices=sorted(FAMILY_FIELD_NAMES), required=True)
    parser.add_argument("--pack-id", required=True)
    parser.add_argument("--path", type=Path, required=True)
    parser.add_argument(
        "--field-name",
        default="",
        help="Manual settings field to model. Defaults from --family.",
    )
    parser.add_argument("--source-name", default="")
    parser.add_argument("--source-url", default="")
    parser.add_argument(
        "--local-source-path",
        default="",
        help="Original local source path for provenance. Defaults to --path.",
    )
    parser.add_argument(
        "--license-status",
        choices=sorted(LICENSE_STATUS_VALUES),
        default="requires_review",
    )
    parser.add_argument("--raw-sha1", default="")
    parser.add_argument("--raw-sha256", default="")
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_external_import_plan(
        family=args.family,
        pack_id=args.pack_id,
        path=args.path,
        field_name=args.field_name,
        source_name=args.source_name,
        source_url=args.source_url,
        local_source_path=args.local_source_path,
        license_status=args.license_status,
        raw_sha1=args.raw_sha1,
        raw_sha256=args.raw_sha256,
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.markdown_out.write_text(render_external_import_plan_markdown(report), encoding="utf-8")
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    return 0


def build_external_import_plan(
    *,
    family: str,
    pack_id: str,
    path: Path,
    field_name: str = "",
    source_name: str = "",
    source_url: str = "",
    local_source_path: str = "",
    license_status: str = "requires_review",
    raw_sha1: str = "",
    raw_sha256: str = "",
    generated_at: str | None = None,
) -> dict[str, object]:
    family_text = str(family or "").strip()
    pack_id_text = str(pack_id or "").strip()
    field_name_text = str(field_name or "").strip() or FAMILY_FIELD_NAMES.get(family_text, "")
    resolved_path = Path(path).expanduser().resolve(strict=False)
    path_exists = resolved_path.exists()
    raw_checksum = _raw_checksum_evidence(
        path=resolved_path,
        raw_sha1=raw_sha1,
        raw_sha256=raw_sha256,
    )
    format_supported, expected_format = manual_path_format_support(
        field_name=field_name_text,
        family=family_text,
        key=pack_id_text,
        path=resolved_path,
    )
    issues = _issues(
        family=family_text,
        pack_id=pack_id_text,
        path_exists=path_exists,
        format_supported=format_supported,
        license_status=license_status,
    )
    manual_link_allowed = path_exists and format_supported and not _fatal_issues(issues)
    provenance_preview = _provenance_preview(
        family=family_text,
        pack_id=pack_id_text,
        path=resolved_path,
        source_name=source_name,
        source_url=source_url,
        local_source_path=local_source_path,
        license_status=license_status,
        raw_sha1=str(raw_checksum.get("sha1") or ""),
        raw_sha256=str(raw_checksum.get("sha256") or ""),
    )
    preview_errors = list(validate_pack_provenance_payload(provenance_preview))
    promotion_blockers = _promotion_blockers(
        manual_link_allowed=manual_link_allowed,
        license_status=license_status,
        raw_sha1=str(raw_checksum.get("sha1") or ""),
        raw_sha256=str(raw_checksum.get("sha256") or ""),
        provenance_preview_errors=preview_errors,
        issues=issues,
    )
    promotion_ready = not promotion_blockers
    decision = _decision(
        manual_link_allowed=manual_link_allowed,
        promotion_ready=promotion_ready,
    )
    status = _status(
        manual_link_allowed=manual_link_allowed,
        promotion_ready=promotion_ready,
        issues=issues,
    )
    return {
        "schema_version": 1,
        "generated_at": generated_at or _utc_now(),
        "mutation": "none",
        "runtime_policy_change": "none",
        "status": status,
        "decision": decision,
        "family": family_text,
        "pack_id": pack_id_text,
        "field_name": field_name_text,
        "path": str(resolved_path),
        "path_exists": path_exists,
        "expected_format": expected_format,
        "format_supported": format_supported,
        "manual_link": {
            "allowed": manual_link_allowed,
            "reason": _manual_link_reason(
                manual_link_allowed=manual_link_allowed,
                path_exists=path_exists,
                format_supported=format_supported,
            ),
        },
        "managed_import": {
            "status": _managed_import_status(
                manual_link_allowed=manual_link_allowed,
                promotion_ready=promotion_ready,
            ),
            "required_action": _managed_import_required_action(
                manual_link_allowed=manual_link_allowed,
                promotion_ready=promotion_ready,
            ),
            "target_pack_root_policy": (
                "future explicit operator flow under data_root/<family>_packs/<pack_id>"
            ),
            "missing_or_review_fields": promotion_blockers,
        },
        "promotion": {
            "ready": promotion_ready,
            "blocked_reasons": promotion_blockers,
        },
        "raw_checksum": raw_checksum,
        "provenance_preview_valid": not preview_errors,
        "provenance_preview_errors": preview_errors,
        "provenance_preview": provenance_preview,
        "issues": issues,
        "boundaries": [
            "does_not_copy_or_convert_external_artifacts",
            "does_not_write_settings_manifest_or_provenance_sidecar",
            "does_not_approve_source_license",
            "does_not_change_runtime_defaults",
        ],
    }


def render_external_import_plan_markdown(report: Mapping[str, object]) -> str:
    manual_link = _as_mapping(report.get("manual_link"))
    managed_import = _as_mapping(report.get("managed_import"))
    promotion = _as_mapping(report.get("promotion"))
    lines = [
        "# Pack Lifecycle External Import Plan",
        "",
        f"- Generated at: `{report.get('generated_at')}`",
        f"- Family: `{report.get('family')}`",
        f"- Pack id: `{report.get('pack_id')}`",
        f"- Path: `{report.get('path')}`",
        f"- Status: `{report.get('status')}`",
        f"- Decision: `{report.get('decision')}`",
        f"- Mutation: `{report.get('mutation')}`",
        f"- Runtime policy change: `{report.get('runtime_policy_change')}`",
        "",
        "## Manual Link",
        "",
        f"- Allowed: `{manual_link.get('allowed')}`",
        f"- Reason: `{manual_link.get('reason')}`",
        f"- Expected format: `{report.get('expected_format')}`",
        f"- Format supported: `{report.get('format_supported')}`",
        "",
        "## Managed Import",
        "",
        f"- Status: `{managed_import.get('status')}`",
        f"- Required action: `{managed_import.get('required_action')}`",
        f"- Target policy: `{managed_import.get('target_pack_root_policy')}`",
        "",
        "## Promotion",
        "",
        f"- Ready: `{promotion.get('ready')}`",
        "- Blocked reasons: " + _inline_list(_sequence(promotion.get("blocked_reasons"))),
        "- Raw checksum source: "
        f"`{_as_mapping(report.get('raw_checksum')).get('source') or 'none'}`",
        "",
        "## Issues",
        "",
        _inline_list(_sequence(report.get("issues"))),
        "",
        "## Boundaries",
        "",
    ]
    lines.extend(f"- `{item}`" for item in _sequence(report.get("boundaries")))
    lines.append("")
    return "\n".join(lines)


def _issues(
    *,
    family: str,
    pack_id: str,
    path_exists: bool,
    format_supported: bool,
    license_status: str,
) -> list[str]:
    issues: list[str] = []
    if family not in FAMILY_FIELD_NAMES:
        issues.append("unknown_pack_family")
    if not pack_id:
        issues.append("missing_pack_id")
    if not path_exists:
        issues.append("external_path_missing")
    elif not format_supported:
        issues.append("unsupported_manual_artifact_format")
    if license_status not in LICENSE_STATUS_VALUES:
        issues.append("invalid_license_status")
    return issues


def _fatal_issues(issues: Sequence[str]) -> bool:
    return any(
        issue in {"unknown_pack_family", "missing_pack_id", "invalid_license_status"}
        for issue in issues
    )


def _provenance_preview(
    *,
    family: str,
    pack_id: str,
    path: Path,
    source_name: str,
    source_url: str,
    local_source_path: str,
    license_status: str,
    raw_sha1: str,
    raw_sha256: str,
) -> dict[str, object]:
    source_pointer = str(local_source_path or "").strip() or str(path)
    raw_artifact: dict[str, object] = {"filename": path.name or pack_id}
    if raw_sha1_text := str(raw_sha1 or "").strip():
        raw_artifact["sha1"] = raw_sha1_text
    if raw_sha256_text := str(raw_sha256 or "").strip():
        raw_artifact["sha256"] = raw_sha256_text
    source: dict[str, object] = {
        "source_name": str(source_name or "").strip(),
        "license_status": str(license_status or "").strip(),
        "raw_artifacts": [raw_artifact],
    }
    if source_url_text := str(source_url or "").strip():
        source["source_url"] = source_url_text
    else:
        source["local_source_path"] = source_pointer
    return {
        "schema_version": 1,
        "pack_id": str(pack_id or "").strip(),
        "pack_kind": str(family or "").strip(),
        "provider": "manual_external",
        "source": source,
        "build": {"build_mode": _build_mode(family=family, path=path)},
        "artifact": {
            "artifact_relpath": path.name or ".",
            "artifact_kind": _artifact_kind(path),
        },
    }


def _raw_checksum_evidence(*, path: Path, raw_sha1: str, raw_sha256: str) -> dict[str, object]:
    provided_sha1 = str(raw_sha1 or "").strip()
    provided_sha256 = str(raw_sha256 or "").strip()
    if provided_sha1 or provided_sha256:
        return {
            "sha1": provided_sha1,
            "sha256": provided_sha256,
            "source": "provided",
        }
    computed = _file_checksums(path)
    if not computed:
        return {
            "sha1": "",
            "sha256": "",
            "source": "unavailable",
        }
    return {
        **computed,
        "source": "computed_from_external_path",
    }


def _file_checksums(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    sha1 = hashlib.sha1()
    sha256 = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            sha1.update(chunk)
            sha256.update(chunk)
    return {
        "sha1": sha1.hexdigest(),
        "sha256": sha256.hexdigest(),
    }


def _promotion_blockers(
    *,
    manual_link_allowed: bool,
    license_status: str,
    raw_sha1: str,
    raw_sha256: str,
    provenance_preview_errors: Sequence[str],
    issues: Sequence[str],
) -> list[str]:
    blockers: list[str] = []
    if not manual_link_allowed:
        blockers.append("manual_link_not_allowed")
    if license_status != PROMOTION_LICENSE_STATUS:
        blockers.append(f"license_status_{license_status or 'missing'}")
    if not str(raw_sha1 or "").strip() and not str(raw_sha256 or "").strip():
        blockers.append("missing_raw_artifact_checksum")
    blockers.extend(f"provenance_preview:{error}" for error in provenance_preview_errors)
    blockers.extend(
        f"issue:{issue}" for issue in issues if issue != "unsupported_manual_artifact_format"
    )
    return _dedupe(blockers)


def _decision(*, manual_link_allowed: bool, promotion_ready: bool) -> str:
    if promotion_ready:
        return "external_import_preflight_ready"
    if manual_link_allowed:
        return "external_manual_link_ready_import_needs_review"
    return "external_manual_link_blocked"


def _status(
    *,
    manual_link_allowed: bool,
    promotion_ready: bool,
    issues: Sequence[str],
) -> str:
    if _fatal_issues(issues):
        return "error"
    if promotion_ready:
        return "ok"
    if manual_link_allowed:
        return "review"
    return "blocked"


def _manual_link_reason(
    *,
    manual_link_allowed: bool,
    path_exists: bool,
    format_supported: bool,
) -> str:
    if manual_link_allowed:
        return "path exists and matches the exact supported manual artifact shape"
    if not path_exists:
        return "external path is missing"
    if not format_supported:
        return "external path exists but does not match the supported manual artifact shape"
    return "manual link blocked by preflight issue"


def _managed_import_status(*, manual_link_allowed: bool, promotion_ready: bool) -> str:
    if promotion_ready:
        return "ready_for_explicit_operator_import"
    if manual_link_allowed:
        return "needs_source_or_license_review"
    return "blocked"


def _managed_import_required_action(*, manual_link_allowed: bool, promotion_ready: bool) -> str:
    if promotion_ready:
        return "copy_or_convert_in_future_explicit_import_flow"
    if manual_link_allowed:
        return "keep_manual_link_or_complete_license_source_and_checksum_review"
    return "choose_existing_artifact_with_supported_exact_format"


def _build_mode(*, family: str, path: Path) -> str:
    if path.is_dir():
        return "manual_external_directory_link"
    if family == "embedding" and path.suffix.lower() in {".vec", ".txt", ".bin"}:
        return "manual_external_vector_link"
    return "manual_external_artifact_link"


def _artifact_kind(path: Path) -> str:
    if path.is_dir():
        return "directory"
    suffix = path.suffix.lower()
    if suffix in {".sqlite", ".sqlite3", ".db"}:
        return "sqlite"
    if suffix in {".vec", ".bin"}:
        return "embedding"
    return "file"


def _inline_list(values: Sequence[object]) -> str:
    items = [f"`{item}`" for item in values if str(item).strip()]
    return ", ".join(items) if items else "`none`"


def _dedupe(values: Sequence[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            deduped.append(value)
    return deduped


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _sequence(value: object) -> Sequence[object]:
    return value if isinstance(value, Sequence) and not isinstance(value, (str, bytes)) else ()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


if __name__ == "__main__":
    raise SystemExit(main())
