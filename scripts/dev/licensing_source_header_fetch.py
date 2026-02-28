#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

try:
    from .licensing_source_header_fetch_support import (
        FetchReport,
        PackFetchRow,
        _download,
        _strip_code,
        _url_basename,
        inspect_downloaded_file,
        parse_args,
        parse_pack_ids,
        parse_register_table,
        parse_url_registry_entries,
        print_summary,
    )
except Exception:  # noqa: BLE001
    from licensing_source_header_fetch_support import (  # type: ignore[no-redef]
        FetchReport,
        PackFetchRow,
        _download,
        _strip_code,
        _url_basename,
        inspect_downloaded_file,
        parse_args,
        parse_pack_ids,
        parse_register_table,
        parse_url_registry_entries,
        print_summary,
    )


def build_report(
    *,
    register_path: Path,
    url_registry_path: Path,
    status_filter: set[str],
    pack_filter: set[str],
    cache_dir: Path,
    max_download_bytes: int,
    sample_bytes: int,
    max_lines: int,
    timeout_seconds: float,
    force_redownload: bool,
) -> FetchReport:
    register_rows = parse_register_table(register_path)
    registry = parse_url_registry_entries(url_registry_path)

    rows: list[PackFetchRow] = []
    issues: list[str] = []

    for row in register_rows:
        row_status = _strip_code(row.get("License/copyright status", ""))
        if row_status not in status_filter:
            continue
        pack_ids = parse_pack_ids(row.get("Pack ID", ""))
        for pack_id in pack_ids:
            if pack_filter and pack_id not in pack_filter:
                continue
            registry_entry = registry.get(pack_id)
            if not registry_entry:
                issues.append(f"No URL registry entry for pack_id={pack_id}")
                rows.append(
                    PackFetchRow(
                        pack_id=pack_id,
                        row_status=row_status,
                        source_url="",
                        source_note="missing-url-registry-entry",
                        downloaded_path=None,
                        downloaded_bytes=None,
                        status="missing_source_url",
                        target_name=None,
                        probes=[],
                        error="No language_pack_urls entry for pack_id.",
                    )
                )
                continue

            source_url = str(registry_entry.get("url", "")).strip()
            filename = str(registry_entry.get("filename", "")).strip() or _url_basename(source_url)
            target_name = str(registry_entry.get("unzipped_name", "")).strip() or None
            cached_path = (cache_dir / pack_id / filename).expanduser().resolve(strict=False)

            if cached_path.exists() and cached_path.is_file() and not force_redownload:
                download_status = "cached"
                downloaded_bytes = cached_path.stat().st_size
                download_error = None
            else:
                download_status, downloaded_bytes, download_error = _download(
                    url=source_url,
                    dest_path=cached_path,
                    max_download_bytes=max_download_bytes,
                    timeout_seconds=timeout_seconds,
                )
                if download_status != "downloaded":
                    if download_status == "skipped_too_large" and cached_path.exists():
                        try:
                            cached_path.unlink()
                        except OSError:
                            pass

            if download_status in {"download_error", "missing_source_url"}:
                rows.append(
                    PackFetchRow(
                        pack_id=pack_id,
                        row_status=row_status,
                        source_url=source_url,
                        source_note="registry",
                        downloaded_path=str(cached_path),
                        downloaded_bytes=downloaded_bytes,
                        status=download_status,
                        target_name=target_name,
                        probes=[],
                        error=download_error,
                    )
                )
                continue

            if download_status == "skipped_too_large":
                rows.append(
                    PackFetchRow(
                        pack_id=pack_id,
                        row_status=row_status,
                        source_url=source_url,
                        source_note="registry",
                        downloaded_path=str(cached_path),
                        downloaded_bytes=downloaded_bytes,
                        status="skipped_too_large",
                        target_name=target_name,
                        probes=[],
                        error=download_error,
                    )
                )
                continue

            probes, inspect_error = inspect_downloaded_file(
                cached_path,
                target_name=target_name,
                sample_bytes=sample_bytes,
                max_lines=max_lines,
            )
            status = "inspected" if inspect_error is None else "inspect_error"
            rows.append(
                PackFetchRow(
                    pack_id=pack_id,
                    row_status=row_status,
                    source_url=source_url,
                    source_note="registry",
                    downloaded_path=str(cached_path),
                    downloaded_bytes=downloaded_bytes,
                    status=status,
                    target_name=target_name,
                    probes=probes,
                    error=inspect_error,
                )
            )

    return FetchReport(
        generated_at=datetime.now(timezone.utc).isoformat(),
        register_path=str(register_path),
        url_registry_path=str(url_registry_path),
        cache_dir=str(cache_dir.expanduser().resolve(strict=False)),
        status_filter=sorted(status_filter),
        pack_filter=sorted(pack_filter),
        max_download_bytes=max_download_bytes,
        rows=rows,
        issues=sorted(set(issues)),
    )


def main() -> int:
    args = parse_args()
    status_filters = args.status_filters or ["expected-not-verified"]
    status_filter = {str(item).strip() for item in status_filters if str(item).strip()}
    pack_filter = {str(item).strip() for item in (args.pack_ids or []) if str(item).strip()}

    report = build_report(
        register_path=args.register.expanduser().resolve(strict=False),
        url_registry_path=args.url_registry.expanduser().resolve(strict=False),
        status_filter=status_filter,
        pack_filter=pack_filter,
        cache_dir=args.cache_dir.expanduser().resolve(strict=False),
        max_download_bytes=max(1, int(args.max_download_bytes)),
        sample_bytes=max(1024, int(args.sample_bytes)),
        max_lines=max(1, int(args.max_lines)),
        timeout_seconds=max(1.0, float(args.timeout_seconds)),
        force_redownload=bool(args.force_redownload),
    )

    json_out = args.json_out.expanduser().resolve(strict=False)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(report.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")

    print_summary(report)
    print(f"[licensing_source_header_fetch] wrote {json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
