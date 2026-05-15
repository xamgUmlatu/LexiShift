#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sqlite3
import sys
from typing import Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / "core"
GUI_SRC = PROJECT_ROOT / "apps" / "gui" / "src"
TEST_OUTPUTS_ROOT = PROJECT_ROOT / "docs" / "test_outputs"
for candidate in (CORE_ROOT, GUI_SRC):
    candidate_text = str(candidate)
    if candidate_text not in sys.path:
        sys.path.insert(0, candidate_text)

from language_packs_catalog import build_pack_catalogs  # noqa: E402
from lexishift_core.helper.installed_packs import MANIFEST_FILENAME  # noqa: E402
from lexishift_core.helper.pack_provenance import (  # noqa: E402
    PACK_PROVENANCE_FILENAME,
    validate_pack_provenance_file,
)
from pack_lifecycle_manual_resources import audit_manual_resource_settings  # noqa: E402


DEFAULT_JSON_OUT = TEST_OUTPUTS_ROOT / "pack_lifecycle_audit_latest.json"
DEFAULT_MARKDOWN_OUT = TEST_OUTPUTS_ROOT / "pack_lifecycle_audit_latest.md"
DEFAULT_PAIR = "en-es"
DEFAULT_PROFILE_ID = "default"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Audit local pack lifecycle state without changing runtime data: installed "
            "manifests, optional provenance sidecars, semantic pack copies, publication "
            "manifests, and optional candidate SQLite metadata."
        )
    )
    parser.add_argument(
        "--data-root",
        type=Path,
        default=Path("~/.local/share/LexiShift/LexiShift"),
        help="LexiShift data root to inspect.",
    )
    parser.add_argument("--pair", default=DEFAULT_PAIR)
    parser.add_argument("--profile-id", default=DEFAULT_PROFILE_ID)
    parser.add_argument(
        "--candidate-db",
        type=Path,
        action="append",
        default=None,
        help="Optional generated SQLite pack candidate to inspect. May be repeated.",
    )
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    parser.add_argument("--fail-on-error", action="store_true")
    parser.add_argument(
        "--fail-on-review",
        action="store_true",
        help=(
            "Exit non-zero unless the summary status is ok. Use for release/promotion "
            "gates; omit for ordinary local audits that may intentionally surface review items."
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_pack_lifecycle_audit_report(
        data_root=args.data_root,
        pair=args.pair,
        profile_id=args.profile_id,
        candidate_dbs=args.candidate_db or (),
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.markdown_out.write_text(render_pack_lifecycle_markdown(report), encoding="utf-8")
    print(f"Wrote JSON artifact to {args.json_out}")
    print(f"Wrote Markdown artifact to {args.markdown_out}")
    return pack_lifecycle_audit_exit_code(
        report,
        fail_on_error=bool(args.fail_on_error),
        fail_on_review=bool(args.fail_on_review),
    )


def build_pack_lifecycle_audit_report(
    *,
    data_root: Path,
    pair: str = DEFAULT_PAIR,
    profile_id: str = DEFAULT_PROFILE_ID,
    candidate_dbs: Sequence[Path] = (),
    generated_at: str | None = None,
) -> dict[str, object]:
    resolved_root = Path(data_root).expanduser().resolve(strict=False)
    normalized_pair = str(pair or DEFAULT_PAIR).strip().lower() or DEFAULT_PAIR
    normalized_profile = _sanitize_profile_id(profile_id)
    family_reports = {
        "language": audit_installed_pack_family(
            resolved_root / "language_packs",
            expected_pack_kind="language",
        ),
        "frequency": audit_installed_pack_family(
            resolved_root / "frequency_packs",
            expected_pack_kind="frequency",
        ),
        "embedding": audit_installed_pack_family(
            resolved_root / "embedding_packs",
            expected_pack_kind="embedding",
        ),
    }
    semantic_report = audit_semantic_pack_copies(
        resolved_root / "language_packs" / normalized_pair / "semantic_packs"
    )
    publication_report = audit_publication_manifests(
        resolved_root / "srs" / "profiles" / normalized_profile,
        pair=normalized_pair,
    )
    manual_resource_report = audit_manual_resource_settings(resolved_root / "settings.json")
    candidate_reports = [audit_candidate_sqlite(path) for path in candidate_dbs]
    summary = _build_summary(
        family_reports=family_reports,
        semantic_report=semantic_report,
        publication_report=publication_report,
        manual_resource_report=manual_resource_report,
        candidate_reports=candidate_reports,
    )
    return {
        "schema_version": 1,
        "generated_at": generated_at or _utc_now(),
        "decision": "pack_lifecycle_state_audited",
        "runtime_policy_change": "none",
        "data_root": str(resolved_root),
        "pair": normalized_pair,
        "profile_id": normalized_profile,
        "catalog_summary": build_catalog_summary(),
        "summary": summary,
        "installed_pack_families": family_reports,
        "semantic_pack_copies": semantic_report,
        "publication_manifests": publication_report,
        "manual_resource_settings": manual_resource_report,
        "candidate_sqlite": candidate_reports,
    }


def audit_installed_pack_family(base_dir: Path, *, expected_pack_kind: str) -> dict[str, object]:
    root = Path(base_dir).expanduser().resolve(strict=False)
    rows = []
    if root.exists() and root.is_dir():
        for pack_root in sorted(path for path in root.iterdir() if path.is_dir()):
            rows.append(_audit_installed_pack_root(pack_root, expected_pack_kind))
    return {
        "base_dir": str(root),
        "base_dir_exists": root.exists(),
        "expected_pack_kind": expected_pack_kind,
        "pack_count": len(rows),
        "missing_manifest_count": sum(1 for row in rows if not row["manifest_exists"]),
        "missing_artifact_count": sum(1 for row in rows if "missing_artifact" in row["issues"]),
        "missing_provenance_count": sum(1 for row in rows if not row["provenance_exists"]),
        "invalid_provenance_count": sum(
            1 for row in rows if row["provenance_exists"] and not row["provenance_valid"]
        ),
        "provenance_review_required_count": sum(
            1 for row in rows if _as_mapping(row.get("provenance_review")).get("review_required")
        ),
        "license_status_counts": _license_status_counts(rows),
        "packs": rows,
    }


def audit_semantic_pack_copies(base_dir: Path) -> dict[str, object]:
    root = Path(base_dir).expanduser().resolve(strict=False)
    rows = []
    if root.exists() and root.is_dir():
        for pack_root in sorted(path for path in root.iterdir() if path.is_dir()):
            rows.append(_audit_semantic_pack_root(pack_root))
    return {
        "base_dir": str(root),
        "base_dir_exists": root.exists(),
        "pack_count": len(rows),
        "missing_manifest_count": sum(1 for row in rows if not row["manifest_exists"]),
        "missing_inventory_count": sum(
            1 for row in rows if "missing_semantic_inventory" in row["issues"]
        ),
        "missing_provenance_count": sum(1 for row in rows if not row["provenance_exists"]),
        "invalid_provenance_count": sum(
            1 for row in rows if row["provenance_exists"] and not row["provenance_valid"]
        ),
        "provenance_review_required_count": sum(
            1 for row in rows if _as_mapping(row.get("provenance_review")).get("review_required")
        ),
        "license_status_counts": _license_status_counts(rows),
        "packs": rows,
    }


def audit_publication_manifests(profile_dir: Path, *, pair: str) -> dict[str, object]:
    root = Path(profile_dir).expanduser().resolve(strict=False)
    pattern = f"srs_publication_manifest_{pair}.json" if pair else "srs_publication_manifest_*.json"
    rows = []
    if root.exists() and root.is_dir():
        for manifest_path in sorted(root.glob(pattern)):
            rows.append(_audit_publication_manifest(manifest_path))
    return {
        "profile_dir": str(root),
        "profile_dir_exists": root.exists(),
        "manifest_count": len(rows),
        "invalid_count": sum(1 for row in rows if row["issues"]),
        "source_lineage_count": sum(1 for row in rows if row["source_lineage_exists"]),
        "manifests": rows,
    }


def audit_candidate_sqlite(path: Path) -> dict[str, object]:
    resolved = Path(path).expanduser().resolve(strict=False)
    row: dict[str, object] = {
        "path": str(resolved),
        "exists": resolved.exists(),
        "status": "ok",
        "issues": [],
        "tables": [],
        "primary_table": None,
        "row_count": None,
        "columns": [],
        "meta": {},
    }
    if not resolved.exists() or not resolved.is_file():
        row["status"] = "error"
        row["issues"] = ["candidate_sqlite_missing"]
        return row
    try:
        with sqlite3.connect(resolved) as conn:
            tables = _sqlite_tables(conn)
            row["tables"] = tables
            primary_table = _first_data_table(tables)
            row["primary_table"] = primary_table
            if primary_table:
                row["columns"] = _sqlite_columns(conn, primary_table)
                row["row_count"] = _sqlite_row_count(conn, primary_table)
            if "meta" in tables:
                row["meta"] = _sqlite_meta(conn)
    except sqlite3.Error as exc:
        row["status"] = "error"
        row["issues"] = [f"sqlite_error:{exc}"]
    return row


def build_catalog_summary() -> dict[str, object]:
    catalogs = build_pack_catalogs()
    return {
        "language_pack_count": len(catalogs.language_packs),
        "frequency_pack_count": len(catalogs.frequency_packs),
        "embedding_pack_count": len(catalogs.embedding_packs),
        "cross_embedding_pack_count": len(catalogs.cross_embedding_packs),
        "language_pack_ids": [pack.pack_id for pack in catalogs.language_packs],
        "frequency_pack_ids": [pack.pack_id for pack in catalogs.frequency_packs],
        "embedding_pack_ids": [pack.pack_id for pack in catalogs.embedding_packs],
        "cross_embedding_pack_ids": [pack.pack_id for pack in catalogs.cross_embedding_packs],
    }


def render_pack_lifecycle_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# Pack Lifecycle Audit",
        "",
        f"- Generated at: `{report.get('generated_at')}`",
        f"- Data root: `{report.get('data_root')}`",
        f"- Pair/profile: `{report.get('pair')}` / `{report.get('profile_id')}`",
        f"- Status: `{summary.get('status')}`",
        f"- Installed pack count: `{summary.get('installed_pack_count')}`",
        f"- Missing provenance sidecars: `{summary.get('missing_provenance_count')}`",
        f"- Invalid provenance sidecars: `{summary.get('invalid_provenance_count')}`",
        f"- Provenance review required: `{summary.get('provenance_review_required_count')}`",
        f"- Missing installed artifacts: `{summary.get('missing_artifact_count')}`",
        "",
        "## Installed Pack Families",
        "",
        "| Family | Packs | Missing Manifest | Missing Artifact | Missing Provenance | Invalid Provenance | Provenance Review |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    families = _as_mapping(report.get("installed_pack_families"))
    for family_name, raw_family in families.items():
        family = _as_mapping(raw_family)
        lines.append(
            "| "
            f"{family_name} | {family.get('pack_count')} | "
            f"{family.get('missing_manifest_count')} | "
            f"{family.get('missing_artifact_count')} | "
            f"{family.get('missing_provenance_count')} | "
            f"{family.get('invalid_provenance_count')} | "
            f"{family.get('provenance_review_required_count')} |"
        )
    semantic = _as_mapping(report.get("semantic_pack_copies"))
    lines.extend(
        [
            "",
            "## Semantic Pack Copies",
            "",
            f"- Pack count: `{semantic.get('pack_count')}`",
            f"- Missing inventory count: `{semantic.get('missing_inventory_count')}`",
            f"- Missing provenance count: `{semantic.get('missing_provenance_count')}`",
            f"- Provenance review required: `{semantic.get('provenance_review_required_count')}`",
            "",
            "## Provenance Review",
            "",
        ]
    )
    review_rows = _provenance_review_rows(report)
    if review_rows:
        lines.extend(
            [
                "| Family | Pack | License | Source Pointer | Raw Checksums | Artifact Checksum | Review Reasons |",
                "| --- | --- | --- | --- | ---: | --- | --- |",
            ]
        )
        for family_name, row, review in review_rows:
            reasons = ", ".join(str(value) for value in _sequence(review.get("review_reasons")))
            lines.append(
                "| "
                f"{family_name} | "
                f"{row.get('pack_id')} | "
                f"{review.get('license_status')} | "
                f"{review.get('source_pointer_kind')} | "
                f"{review.get('raw_artifact_checksum_count')}/"
                f"{review.get('raw_artifact_count')} | "
                f"{review.get('artifact_checksum_present')} | "
                f"{reasons or 'none'} |"
            )
        lines.append("")
    else:
        lines.extend(["- No provenance review items.", ""])
    lines.extend(
        [
            "## Publication Manifests",
            "",
        ]
    )
    publication = _as_mapping(report.get("publication_manifests"))
    lines.extend(
        [
            f"- Manifest count: `{publication.get('manifest_count')}`",
            f"- Invalid count: `{publication.get('invalid_count')}`",
            f"- Source lineage count: `{publication.get('source_lineage_count')}`",
            "",
            "## Manual Resource Settings",
            "",
        ]
    )
    manual_settings = _as_mapping(report.get("manual_resource_settings"))
    lines.extend(
        [
            f"- Settings path: `{manual_settings.get('settings_path')}`",
            f"- Status: `{manual_settings.get('status')}`",
            f"- Manual path count: `{manual_settings.get('manual_path_count')}`",
            f"- Manual path review count: `{manual_settings.get('manual_path_review_count')}`",
            f"- Managed artifact manual paths: "
            f"`{manual_settings.get('managed_artifact_manual_path_count')}`",
            "",
        ]
    )
    manual_paths = _sequence(manual_settings.get("manual_paths"))
    if manual_paths:
        lines.extend(
            [
                "| Field | Key | Disposition | Exists | Expected Format | Issues |",
                "| --- | --- | --- | --- | --- | --- |",
            ]
        )
        for raw_row in manual_paths:
            row = _as_mapping(raw_row)
            issues = ", ".join(str(value) for value in _sequence(row.get("issues"))) or "none"
            lines.append(
                "| "
                f"{row.get('field_name')} | "
                f"{row.get('key')} | "
                f"{row.get('disposition')} | "
                f"{row.get('path_exists')} | "
                f"{row.get('expected_format')} | "
                f"{issues} |"
            )
        lines.append("")
    lines.extend(
        [
            "## Candidate SQLite",
            "",
        ]
    )
    candidates = _sequence(report.get("candidate_sqlite"))
    if not candidates:
        lines.append("- No candidate SQLite files were provided.")
    for raw_candidate in candidates:
        candidate = _as_mapping(raw_candidate)
        lines.append(
            "- "
            f"`{candidate.get('path')}`: status=`{candidate.get('status')}`, "
            f"primary_table=`{candidate.get('primary_table')}`, "
            f"row_count=`{candidate.get('row_count')}`"
        )
    lines.append("")
    return "\n".join(lines)


def pack_lifecycle_audit_exit_code(
    report: Mapping[str, object],
    *,
    fail_on_error: bool = False,
    fail_on_review: bool = False,
) -> int:
    status = str(_as_mapping(report.get("summary")).get("status") or "").strip()
    if fail_on_review and status != "ok":
        return 1
    if fail_on_error and status == "error":
        return 1
    return 0


def _audit_installed_pack_root(pack_root: Path, expected_pack_kind: str) -> dict[str, object]:
    manifest_path = pack_root / MANIFEST_FILENAME
    manifest_payload, manifest_errors = _load_json_object(manifest_path)
    artifact_relpath = str(manifest_payload.get("artifact_relpath") or "").strip()
    artifact_path = _resolve_artifact_path(pack_root, artifact_relpath)
    provenance_path = pack_root / PACK_PROVENANCE_FILENAME
    provenance_errors = (
        list(validate_pack_provenance_file(provenance_path)) if provenance_path.exists() else []
    )
    provenance_review = _audit_provenance_review(provenance_path, provenance_errors)
    issues: list[str] = []
    if not manifest_path.exists():
        issues.append("missing_manifest")
    if manifest_errors:
        issues.extend(f"manifest:{error}" for error in manifest_errors)
    if artifact_relpath and not artifact_path.exists():
        issues.append("missing_artifact")
    if not provenance_path.exists():
        issues.append("missing_provenance")
    if provenance_errors:
        issues.extend(f"provenance:{error}" for error in provenance_errors)
    pack_kind = str(manifest_payload.get("pack_kind") or expected_pack_kind).strip()
    if manifest_payload and pack_kind != expected_pack_kind:
        issues.append(f"unexpected_pack_kind:{pack_kind}")
    return {
        "pack_id": str(manifest_payload.get("pack_id") or pack_root.name),
        "pack_kind": pack_kind,
        "pack_root": str(pack_root),
        "manifest_path": str(manifest_path),
        "manifest_exists": manifest_path.exists(),
        "manifest_errors": manifest_errors,
        "artifact_relpath": artifact_relpath,
        "artifact_path": str(artifact_path) if artifact_relpath else "",
        "artifact_exists": bool(artifact_relpath and artifact_path.exists()),
        "provenance_path": str(provenance_path),
        "provenance_exists": provenance_path.exists(),
        "provenance_valid": provenance_path.exists() and not provenance_errors,
        "provenance_errors": provenance_errors,
        "provenance_review": provenance_review,
        "issues": issues,
    }


def _audit_semantic_pack_root(pack_root: Path) -> dict[str, object]:
    manifest_path = pack_root / MANIFEST_FILENAME
    inventory_path = pack_root / "semantic_inventory.json"
    manifest_payload, manifest_errors = _load_json_object(manifest_path)
    provenance_path = pack_root / PACK_PROVENANCE_FILENAME
    provenance_errors = (
        list(validate_pack_provenance_file(provenance_path)) if provenance_path.exists() else []
    )
    provenance_review = _audit_provenance_review(provenance_path, provenance_errors)
    issues: list[str] = []
    if not manifest_path.exists():
        issues.append("missing_manifest")
    if manifest_errors:
        issues.extend(f"manifest:{error}" for error in manifest_errors)
    if not inventory_path.exists():
        issues.append("missing_semantic_inventory")
    if not provenance_path.exists():
        issues.append("missing_provenance")
    if provenance_errors:
        issues.extend(f"provenance:{error}" for error in provenance_errors)
    return {
        "pack_id": str(manifest_payload.get("pack_id") or pack_root.name),
        "pair": str(manifest_payload.get("pair") or ""),
        "pack_root": str(pack_root),
        "manifest_path": str(manifest_path),
        "manifest_exists": manifest_path.exists(),
        "manifest_errors": manifest_errors,
        "semantic_inventory_path": str(inventory_path),
        "semantic_inventory_exists": inventory_path.exists(),
        "provenance_path": str(provenance_path),
        "provenance_exists": provenance_path.exists(),
        "provenance_valid": provenance_path.exists() and not provenance_errors,
        "provenance_errors": provenance_errors,
        "provenance_review": provenance_review,
        "issues": issues,
    }


def _audit_publication_manifest(path: Path) -> dict[str, object]:
    payload, errors = _load_json_object(path)
    validation = _as_mapping(payload.get("validation"))
    artifacts = _as_mapping(payload.get("artifacts"))
    source_lineage = _as_mapping(payload.get("source_lineage"))
    issues = list(errors)
    generation_id = str(payload.get("generation_id") or "").strip()
    if not generation_id:
        issues.append("missing_generation_id")
    if validation.get("family_valid") is False:
        issues.append("family_valid_false")
    return {
        "path": str(path),
        "pair": str(payload.get("pair") or ""),
        "profile_id": str(payload.get("profile_id") or ""),
        "generation_id": generation_id,
        "family_valid": validation.get("family_valid"),
        "artifact_count": len(artifacts),
        "source_lineage_exists": bool(source_lineage),
        "source_lineage_pack_id": str(source_lineage.get("pack_id") or ""),
        "source_lineage_source_batch_count": len(_sequence(source_lineage.get("source_batches"))),
        "issues": issues,
    }


def _build_summary(
    *,
    family_reports: Mapping[str, object],
    semantic_report: Mapping[str, object],
    publication_report: Mapping[str, object],
    manual_resource_report: Mapping[str, object],
    candidate_reports: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    family_values = [_as_mapping(value) for value in family_reports.values()]
    installed_pack_count = sum(int(family.get("pack_count") or 0) for family in family_values)
    missing_manifest_count = sum(
        int(family.get("missing_manifest_count") or 0) for family in family_values
    ) + int(semantic_report.get("missing_manifest_count") or 0)
    missing_artifact_count = sum(
        int(family.get("missing_artifact_count") or 0) for family in family_values
    )
    missing_provenance_count = sum(
        int(family.get("missing_provenance_count") or 0) for family in family_values
    ) + int(semantic_report.get("missing_provenance_count") or 0)
    invalid_provenance_count = sum(
        int(family.get("invalid_provenance_count") or 0) for family in family_values
    ) + int(semantic_report.get("invalid_provenance_count") or 0)
    provenance_review_required_count = sum(
        int(family.get("provenance_review_required_count") or 0) for family in family_values
    ) + int(semantic_report.get("provenance_review_required_count") or 0)
    publication_invalid_count = int(publication_report.get("invalid_count") or 0)
    manual_resource_review_count = int(manual_resource_report.get("manual_path_review_count") or 0)
    manual_resource_error_count = 1 if manual_resource_report.get("status") == "error" else 0
    candidate_error_count = sum(
        1 for candidate in candidate_reports if candidate.get("status") == "error"
    )
    status = "ok"
    if (
        missing_manifest_count
        or missing_artifact_count
        or invalid_provenance_count
        or publication_invalid_count
        or manual_resource_error_count
        or candidate_error_count
    ):
        status = "error"
    elif (
        missing_provenance_count or manual_resource_review_count or provenance_review_required_count
    ):
        status = "review"
    return {
        "status": status,
        "installed_pack_count": installed_pack_count,
        "semantic_pack_count": int(semantic_report.get("pack_count") or 0),
        "publication_manifest_count": int(publication_report.get("manifest_count") or 0),
        "candidate_sqlite_count": len(candidate_reports),
        "missing_manifest_count": missing_manifest_count,
        "missing_artifact_count": missing_artifact_count,
        "missing_provenance_count": missing_provenance_count,
        "invalid_provenance_count": invalid_provenance_count,
        "provenance_review_required_count": provenance_review_required_count,
        "publication_invalid_count": publication_invalid_count,
        "manual_resource_path_count": int(manual_resource_report.get("manual_path_count") or 0),
        "manual_resource_review_count": manual_resource_review_count,
        "manual_resource_error_count": manual_resource_error_count,
        "candidate_error_count": candidate_error_count,
    }


def _audit_provenance_review(
    provenance_path: Path,
    provenance_errors: Sequence[str],
) -> dict[str, object]:
    payload, load_errors = _load_json_object(provenance_path)
    source = _as_mapping(payload.get("source"))
    artifact = _as_mapping(payload.get("artifact"))
    raw_artifacts = [_as_mapping(item) for item in _sequence(source.get("raw_artifacts"))]
    license_status = str(source.get("license_status") or "").strip()
    source_pointer_kind = _source_pointer_kind(source)
    raw_artifact_checksum_count = sum(1 for item in raw_artifacts if _has_checksum(item))
    artifact_checksum_present = _has_checksum(artifact)
    metrics = _as_mapping(artifact.get("metrics"))
    review_reasons: list[str] = []
    if not provenance_path.exists():
        review_reasons.append("missing_provenance")
    elif load_errors or provenance_errors:
        review_reasons.append("invalid_provenance")
    else:
        if license_status != "confirmed":
            review_reasons.append(f"license_status_{license_status or 'missing'}")
        if not source_pointer_kind:
            review_reasons.append("missing_source_pointer")
        if not raw_artifacts:
            review_reasons.append("missing_raw_artifacts")
        elif raw_artifact_checksum_count < len(raw_artifacts):
            review_reasons.append("raw_artifact_checksum_missing")
        if not artifact_checksum_present:
            review_reasons.append("generated_artifact_checksum_missing")
    return {
        "review_required": bool(review_reasons),
        "review_reasons": review_reasons,
        "source_name": str(source.get("source_name") or "").strip(),
        "license_status": license_status,
        "source_pointer_kind": source_pointer_kind,
        "raw_artifact_count": len(raw_artifacts),
        "raw_artifact_checksum_count": raw_artifact_checksum_count,
        "artifact_checksum_present": artifact_checksum_present,
        "artifact_metrics_present": bool(metrics),
        "artifact_metric_keys": sorted(str(key) for key in metrics),
    }


def _source_pointer_kind(source: Mapping[str, object]) -> str:
    if str(source.get("source_url") or "").strip():
        return "source_url"
    if str(source.get("local_source_path") or "").strip():
        return "local_source_path"
    return ""


def _has_checksum(payload: Mapping[str, object]) -> bool:
    return bool(str(payload.get("sha1") or "").strip() or str(payload.get("sha256") or "").strip())


def _license_status_counts(rows: Sequence[Mapping[str, object]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        review = _as_mapping(row.get("provenance_review"))
        status = str(review.get("license_status") or "").strip() or "missing"
        counts[status] = counts.get(status, 0) + 1
    return dict(sorted(counts.items()))


def _provenance_review_rows(
    report: Mapping[str, object],
) -> list[tuple[str, Mapping[str, object], Mapping[str, object]]]:
    rows: list[tuple[str, Mapping[str, object], Mapping[str, object]]] = []
    families = _as_mapping(report.get("installed_pack_families"))
    for family_name, raw_family in families.items():
        family = _as_mapping(raw_family)
        for row in _sequence(family.get("packs")):
            row_mapping = _as_mapping(row)
            review = _as_mapping(row_mapping.get("provenance_review"))
            if review.get("review_required"):
                rows.append((str(family_name), row_mapping, review))
    semantic = _as_mapping(report.get("semantic_pack_copies"))
    for row in _sequence(semantic.get("packs")):
        row_mapping = _as_mapping(row)
        review = _as_mapping(row_mapping.get("provenance_review"))
        if review.get("review_required"):
            rows.append(("semantic", row_mapping, review))
    return rows


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


def _resolve_artifact_path(pack_root: Path, artifact_relpath: str) -> Path:
    relpath = artifact_relpath or "."
    if relpath == ".":
        return pack_root
    return pack_root / relpath


def _sqlite_tables(conn: sqlite3.Connection) -> list[str]:
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name")
    return [str(row[0]) for row in cursor.fetchall()]


def _first_data_table(tables: Sequence[str]) -> str | None:
    for table in tables:
        if not table.startswith("sqlite_") and table != "meta":
            return table
    return None


def _sqlite_columns(conn: sqlite3.Connection, table: str) -> list[str]:
    cursor = conn.execute(f"PRAGMA table_info({_quote_sqlite_identifier(table)})")
    return [str(row[1]) for row in cursor.fetchall()]


def _sqlite_row_count(conn: sqlite3.Connection, table: str) -> int:
    cursor = conn.execute(f"SELECT COUNT(*) FROM {_quote_sqlite_identifier(table)}")
    return int(cursor.fetchone()[0])


def _sqlite_meta(conn: sqlite3.Connection) -> dict[str, str]:
    try:
        cursor = conn.execute("SELECT key, value FROM meta")
    except sqlite3.Error:
        return {}
    return {str(key): str(value) for key, value in cursor.fetchall()}


def _quote_sqlite_identifier(value: str) -> str:
    escaped = str(value).replace('"', '""')
    return f'"{escaped}"'


def _sanitize_profile_id(value: str | None) -> str:
    raw = str(value or "").strip()
    if not raw:
        return DEFAULT_PROFILE_ID
    normalized = re.sub(r"[^A-Za-z0-9._-]+", "_", raw)
    return normalized or DEFAULT_PROFILE_ID


def _as_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _sequence(value: object) -> Sequence[object]:
    return value if isinstance(value, Sequence) and not isinstance(value, (str, bytes)) else ()


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


if __name__ == "__main__":
    raise SystemExit(main())
