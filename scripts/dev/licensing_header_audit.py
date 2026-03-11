#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / "core"
if str(CORE_ROOT) not in sys.path:
    sys.path.insert(0, str(CORE_ROOT))

from lexishift_core.helper.paths import resolve_data_root  # noqa: E402

try:
    from .licensing_header_audit_support import (
        LicenseAuditReport,
        LicenseAuditRow,
        parse_args,
        parse_pack_ids,
        parse_register_table,
        parse_url_registry,
        print_summary,
        probe_url,
        resolve_artifact_probe,
        resolve_source_url,
        _strip_inline_code,
    )
except Exception:  # noqa: BLE001
    from licensing_header_audit_support import (  # type: ignore[no-redef]
        LicenseAuditReport,
        LicenseAuditRow,
        parse_args,
        parse_pack_ids,
        parse_register_table,
        parse_url_registry,
        print_summary,
        probe_url,
        resolve_artifact_probe,
        resolve_source_url,
        _strip_inline_code,
    )


def build_license_audit_report(
    *,
    register_path: Path,
    url_registry_path: Path,
    data_root: Path,
    status_filter: set[str],
    max_bytes: int,
    max_lines: int,
    timeout_seconds: float,
    skip_remote: bool,
) -> LicenseAuditReport:
    rows = parse_register_table(register_path)
    url_mapping = parse_url_registry(url_registry_path)
    audit_rows: list[LicenseAuditRow] = []
    issues: list[str] = []

    probe_cache: dict[str, object] = {}

    def probe_cached(url: str) -> object:
        if url in probe_cache:
            return probe_cache[url]
        probe = probe_url(
            url,
            max_bytes=max_bytes,
            max_lines=max_lines,
            timeout_seconds=timeout_seconds,
        )
        probe_cache[url] = probe
        return probe

    for row in rows:
        row_status = _strip_inline_code(row.get("License/copyright status", ""))
        if row_status not in status_filter:
            continue

        pack_id_cell = row.get("Pack ID", "")
        distribution_mode = _strip_inline_code(row.get("Recommended distribution mode", ""))
        artifact_cell = row.get("Post-download/post-conversion artifact", "").strip()
        evidence_url = _strip_inline_code(row.get("Evidence URL", ""))
        local_artifact = resolve_artifact_probe(artifact_cell, data_root, max_lines=max_lines)

        evidence_probe = None
        if not skip_remote:
            evidence_probe = probe_cached(evidence_url)

        for pack_id in parse_pack_ids(pack_id_cell):
            source_url, source_url_note = resolve_source_url(pack_id, url_mapping)
            source_probe = None
            if not source_url:
                issues.append(
                    f"Missing source URL mapping for pack_id={pack_id}; no registry URL found."
                )
            elif not skip_remote:
                source_probe = probe_cached(source_url)

            audit_rows.append(
                LicenseAuditRow(
                    pack_id=pack_id,
                    row_status=row_status,
                    distribution_mode=distribution_mode,
                    artifact_cell=artifact_cell,
                    evidence_url=evidence_url,
                    source_url=source_url,
                    source_url_note=source_url_note,
                    local_artifact=local_artifact,
                    evidence_probe=evidence_probe,
                    source_probe=source_probe,
                )
            )

    return LicenseAuditReport(
        generated_at=datetime.now(timezone.utc).isoformat(),
        register_path=str(register_path),
        url_registry_path=str(url_registry_path),
        status_filter=sorted(status_filter),
        max_bytes=max_bytes,
        rows=audit_rows,
        issues=sorted(set(issues)),
    )


def main() -> int:
    args = parse_args(data_root_default=Path(resolve_data_root()))
    selected_statuses = args.status_filters or ["expected-not-verified"]
    status_filter = {str(item).strip() for item in selected_statuses if str(item).strip()}
    report = build_license_audit_report(
        register_path=args.register.expanduser().resolve(strict=False),
        url_registry_path=args.url_registry.expanduser().resolve(strict=False),
        data_root=args.data_root.expanduser().resolve(strict=False),
        status_filter=status_filter,
        max_bytes=max(1, int(args.max_bytes)),
        max_lines=max(1, int(args.max_lines)),
        timeout_seconds=max(1.0, float(args.timeout_seconds)),
        skip_remote=bool(args.skip_remote),
    )

    json_out = args.json_out.expanduser().resolve(strict=False)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(
        json.dumps(report.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print_summary(report)
    print(f"[licensing_header_audit] wrote {json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
