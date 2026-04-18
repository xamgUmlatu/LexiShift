from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any, Callable, Iterable
from urllib import error as url_error
from urllib import request as url_request

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / "core"
GUI_SRC = PROJECT_ROOT / "apps" / "gui" / "src"
for candidate in (GUI_SRC, CORE_ROOT):
    candidate_text = str(candidate)
    if candidate_text not in sys.path:
        sys.path.insert(0, candidate_text)

from language_packs_catalog import (  # noqa: E402
    PackTransportOverride,
    build_pack_catalogs,
)
from pack_source_manifest import (  # noqa: E402
    PACK_SOURCE_MANIFEST_SCHEMA_VERSION,
    PackSourceManifestSnapshot,
    fetch_pack_source_manifest,
    pack_source_manifest_snapshot_from_payload,
)

DEFAULT_MANIFEST_PATH = PROJECT_ROOT / "docs" / "pack_source_manifest.json"
DEFAULT_JSON_OUT = PROJECT_ROOT / "docs" / "test_outputs" / "pack_source_url_audit" / "latest.json"
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "pack_source_url_audit" / "latest.md"
)
DEFAULT_TIMEOUT_SECONDS = 20.0
DEFAULT_USER_AGENT = "LexiShift/1.0"
_HEAD_FALLBACK_STATUS_CODES = frozenset({403, 405, 500, 501})


@dataclass(frozen=True)
class UrlProbe:
    url: str
    ok: bool
    method: str
    status_code: int | None
    final_url: str | None
    content_type: str | None
    content_length: str | None
    error: str | None = None


@dataclass(frozen=True)
class PackSourceAuditRow:
    pack_id: str
    pack_kind: str
    display_name: str
    source: str
    filename: str
    transport_origin: str
    primary_probe: UrlProbe
    archive_probe: UrlProbe | None


@dataclass(frozen=True)
class PackSourceUrlAuditReport:
    generated_at: str
    overall_status: str
    manifest_source: str
    manifest_schema_version: int
    manifest_override_count: int
    manifest_generated_at: str | None
    pack_count: int
    primary_ok_count: int
    primary_fail_count: int
    archive_ok_count: int
    archive_fail_count: int
    archive_skipped_count: int
    include_archive: bool
    pack_kinds: list[str]
    pack_id_filter: list[str]
    rows: list[PackSourceAuditRow]
    issues: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def parse_args() -> Any:
    import argparse

    parser = argparse.ArgumentParser(
        description=(
            "DEV-only tool: validate the pack source manifest and probe bundled/effective "
            "pack download URLs with HEAD plus lightweight GET fallback."
        )
    )
    parser.add_argument(
        "--manifest-path",
        type=Path,
        default=DEFAULT_MANIFEST_PATH,
        help="Local manifest JSON to validate and overlay before probing.",
    )
    parser.add_argument(
        "--manifest-url",
        help="Optional remote manifest URL to fetch instead of --manifest-path.",
    )
    parser.add_argument(
        "--pack-id",
        dest="pack_ids",
        action="append",
        default=None,
        help="Optional pack-id filter (repeatable).",
    )
    parser.add_argument(
        "--pack-kind",
        dest="pack_kinds",
        action="append",
        default=None,
        choices=("language", "frequency", "embedding", "cross_embedding"),
        help="Optional pack-kind filter (repeatable).",
    )
    parser.add_argument(
        "--skip-archive",
        action="store_true",
        help="Skip probing archive/Wayback URLs.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=DEFAULT_TIMEOUT_SECONDS,
        help=f"HTTP timeout in seconds (default: {DEFAULT_TIMEOUT_SECONDS}).",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        default=DEFAULT_JSON_OUT,
        help="JSON output path.",
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=DEFAULT_MARKDOWN_OUT,
        help="Markdown output path.",
    )
    return parser.parse_args()


def build_pack_source_url_audit_report(
    *,
    manifest_path: Path | None,
    manifest_url: str | None,
    pack_ids: Iterable[str] | None,
    pack_kinds: Iterable[str] | None,
    include_archive: bool,
    timeout_seconds: float,
    opener: Callable[..., Any] = url_request.urlopen,
) -> PackSourceUrlAuditReport:
    manifest_snapshot = load_manifest_snapshot(
        manifest_path=manifest_path,
        manifest_url=manifest_url,
        timeout_seconds=timeout_seconds,
    )
    rows, issues = build_audit_rows(
        overrides=manifest_snapshot.overrides,
        pack_ids=pack_ids,
        pack_kinds=pack_kinds,
        include_archive=include_archive,
        timeout_seconds=timeout_seconds,
        opener=opener,
    )

    primary_ok_count = sum(1 for row in rows if row.primary_probe.ok)
    primary_fail_count = len(rows) - primary_ok_count
    archive_rows = [row.archive_probe for row in rows if row.archive_probe is not None]
    archive_ok_count = sum(1 for probe in archive_rows if probe and probe.ok)
    archive_fail_count = sum(1 for probe in archive_rows if probe and not probe.ok)
    archive_skipped_count = len(rows) - len(archive_rows)
    overall_status = "FAIL" if primary_fail_count else "WARN" if archive_fail_count else "PASS"

    pack_kind_values = sorted({row.pack_kind for row in rows})
    pack_id_filter = sorted(
        {str(item or "").strip() for item in pack_ids or () if str(item or "").strip()}
    )
    generated_at = datetime.now(timezone.utc).isoformat()
    manifest_generated_at = (
        manifest_snapshot.generated_at.isoformat() if manifest_snapshot.generated_at else None
    )
    return PackSourceUrlAuditReport(
        generated_at=generated_at,
        overall_status=overall_status,
        manifest_source=manifest_snapshot.source_url,
        manifest_schema_version=PACK_SOURCE_MANIFEST_SCHEMA_VERSION,
        manifest_override_count=len(manifest_snapshot.overrides),
        manifest_generated_at=manifest_generated_at,
        pack_count=len(rows),
        primary_ok_count=primary_ok_count,
        primary_fail_count=primary_fail_count,
        archive_ok_count=archive_ok_count,
        archive_fail_count=archive_fail_count,
        archive_skipped_count=archive_skipped_count,
        include_archive=include_archive,
        pack_kinds=pack_kind_values,
        pack_id_filter=pack_id_filter,
        rows=rows,
        issues=sorted(set(issues)),
    )


def load_manifest_snapshot(
    *,
    manifest_path: Path | None,
    manifest_url: str | None,
    timeout_seconds: float,
) -> PackSourceManifestSnapshot:
    resolved_url = str(manifest_url or "").strip()
    resolved_path = (
        Path(manifest_path).expanduser().resolve(strict=False) if manifest_path else None
    )
    if resolved_url and resolved_path is not None:
        raise ValueError("Specify either --manifest-path or --manifest-url, not both.")
    if resolved_url:
        return fetch_pack_source_manifest(
            manifest_url=resolved_url,
            timeout_seconds=timeout_seconds,
        )
    target = resolved_path or DEFAULT_MANIFEST_PATH.resolve(strict=False)
    payload = json.loads(target.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Manifest payload at {target} must be a JSON object.")
    return pack_source_manifest_snapshot_from_payload(
        payload,
        source_url=target.as_uri(),
        fetched_at=datetime.now(timezone.utc),
    )


def build_audit_rows(
    *,
    overrides: dict[str, PackTransportOverride],
    pack_ids: Iterable[str] | None,
    pack_kinds: Iterable[str] | None,
    include_archive: bool,
    timeout_seconds: float,
    opener: Callable[..., Any],
) -> tuple[list[PackSourceAuditRow], list[str]]:
    rows: list[PackSourceAuditRow] = []
    issues: list[str] = []
    normalized_pack_ids = {
        str(item or "").strip() for item in pack_ids or () if str(item or "").strip()
    }
    normalized_kinds = {
        str(item or "").strip() for item in pack_kinds or () if str(item or "").strip()
    }

    bundled_snapshot = build_pack_catalogs()
    effective_snapshot = build_pack_catalogs(source_overrides=overrides)

    bundle_by_kind = {
        "language": {pack.pack_id: pack for pack in bundled_snapshot.language_packs},
        "frequency": {pack.pack_id: pack for pack in bundled_snapshot.frequency_packs},
        "embedding": {pack.pack_id: pack for pack in bundled_snapshot.embedding_packs},
        "cross_embedding": {pack.pack_id: pack for pack in bundled_snapshot.cross_embedding_packs},
    }
    effective_by_kind = {
        "language": effective_snapshot.language_packs,
        "frequency": effective_snapshot.frequency_packs,
        "embedding": effective_snapshot.embedding_packs,
        "cross_embedding": effective_snapshot.cross_embedding_packs,
    }

    seen_pack_ids = {pack_id for packs in bundle_by_kind.values() for pack_id in packs}
    unknown_requested = sorted(normalized_pack_ids - seen_pack_ids)
    for pack_id in unknown_requested:
        issues.append(f"Unknown pack_id filter: {pack_id}")

    for pack_kind, packs in effective_by_kind.items():
        if normalized_kinds and pack_kind not in normalized_kinds:
            continue
        bundled_by_id = bundle_by_kind[pack_kind]
        for pack in packs:
            if normalized_pack_ids and pack.pack_id not in normalized_pack_ids:
                continue
            bundled_pack = bundled_by_id[pack.pack_id]
            transport_origin = (
                "manifest_override"
                if (
                    pack.url != bundled_pack.url
                    or pack.wayback_url != bundled_pack.wayback_url
                    or pack.filename != bundled_pack.filename
                )
                else "bundled"
            )
            primary_probe = probe_url(
                pack.url,
                timeout_seconds=timeout_seconds,
                opener=opener,
            )
            archive_probe = None
            if include_archive and str(pack.wayback_url or "").strip():
                archive_probe = probe_url(
                    pack.wayback_url,
                    timeout_seconds=timeout_seconds,
                    opener=opener,
                )
            rows.append(
                PackSourceAuditRow(
                    pack_id=pack.pack_id,
                    pack_kind=pack_kind,
                    display_name=pack.name,
                    source=pack.source,
                    filename=pack.filename,
                    transport_origin=transport_origin,
                    primary_probe=primary_probe,
                    archive_probe=archive_probe,
                )
            )
    rows.sort(key=lambda row: (row.pack_kind, row.pack_id))
    return rows, issues


def probe_url(
    url: str,
    *,
    timeout_seconds: float,
    opener: Callable[..., Any] = url_request.urlopen,
) -> UrlProbe:
    head_request = _build_request(url, method="HEAD")
    try:
        return _probe_request(
            head_request, method="HEAD", timeout_seconds=timeout_seconds, opener=opener
        )
    except url_error.HTTPError as exc:
        if int(getattr(exc, "code", 0) or 0) in _HEAD_FALLBACK_STATUS_CODES:
            get_request = _build_request(url, method="GET", range_request=True)
            try:
                return _probe_request(
                    get_request,
                    method="GET",
                    timeout_seconds=timeout_seconds,
                    opener=opener,
                )
            except url_error.HTTPError as get_exc:
                return _probe_from_http_error(get_exc, method="GET")
            except Exception as get_exc:  # noqa: BLE001
                return _probe_from_exception(url, get_exc, method="GET")
        return _probe_from_http_error(exc, method="HEAD")
    except Exception as exc:  # noqa: BLE001
        return _probe_from_exception(url, exc, method="HEAD")


def render_markdown(
    report: PackSourceUrlAuditReport,
    *,
    title: str = "Pack Source URL Audit",
    max_findings: int = 20,
) -> str:
    lines = [
        f"# {title}",
        "",
        f"- Status: {report.overall_status}",
        f"- Manifest source: `{report.manifest_source}`",
        f"- Manifest schema version: {report.manifest_schema_version}",
        f"- Manifest overrides: {report.manifest_override_count}",
        f"- Packs checked: {report.pack_count}",
        ("- Primary URLs: " f"ok={report.primary_ok_count} " f"fail={report.primary_fail_count}"),
        (
            "- Archive URLs: "
            f"ok={report.archive_ok_count} "
            f"fail={report.archive_fail_count} "
            f"skipped={report.archive_skipped_count}"
        ),
    ]
    if report.manifest_generated_at:
        lines.append(f"- Manifest generated at: `{report.manifest_generated_at}`")
    if report.pack_kinds:
        lines.append(f"- Pack kinds: {', '.join(report.pack_kinds)}")
    if report.pack_id_filter:
        lines.append(f"- Pack-id filter: {', '.join(report.pack_id_filter)}")

    lines.extend(["", "## Actionable Findings", ""])
    findings: list[str] = []
    for row in report.rows:
        if not row.primary_probe.ok:
            findings.append(
                _format_probe_finding(row, row.primary_probe, severity="FAIL", role="primary")
            )
        archive_probe = row.archive_probe
        if archive_probe is not None and not archive_probe.ok:
            findings.append(
                _format_probe_finding(row, archive_probe, severity="WARN", role="archive")
            )
    if findings:
        for index, line in enumerate(findings[: max(1, int(max_findings))], start=1):
            lines.append(f"{index}. {line}")
    else:
        lines.append("None.")

    if report.issues:
        lines.extend(["", "## Issues", ""])
        for issue in report.issues:
            lines.append(f"- {issue}")

    lines.extend(
        [
            "",
            "## Probe Table",
            "",
            "| Pack | Kind | Transport | Primary | Archive |",
            "|---|---|---|---|---|",
        ]
    )
    for row in report.rows:
        archive = _probe_status_label(row.archive_probe) if row.archive_probe is not None else "-"
        lines.append(
            "| "
            f"`{row.pack_id}` | "
            f"{row.pack_kind} | "
            f"{row.transport_origin} | "
            f"{_probe_status_label(row.primary_probe)} | "
            f"{archive} |"
        )

    lines.append("")
    return "\n".join(lines)


def print_summary(report: PackSourceUrlAuditReport) -> None:
    print(f"status: {report.overall_status}")
    print(f"manifest_source: {report.manifest_source}")
    print(f"packs_checked: {report.pack_count}")
    print(f"primary_failures: {report.primary_fail_count}")
    print(f"archive_failures: {report.archive_fail_count}")


def _build_request(url: str, *, method: str, range_request: bool = False) -> url_request.Request:
    headers = {"User-Agent": DEFAULT_USER_AGENT}
    if range_request:
        headers["Range"] = "bytes=0-0"
    return url_request.Request(url, headers=headers, method=method)


def _probe_request(
    request: url_request.Request,
    *,
    method: str,
    timeout_seconds: float,
    opener: Callable[..., Any],
) -> UrlProbe:
    with opener(request, timeout=timeout_seconds) as response:
        status_code = _status_code_from_response(response)
        return UrlProbe(
            url=request.full_url,
            ok=status_code is not None and 200 <= status_code < 400,
            method=method,
            status_code=status_code,
            final_url=_final_url_from_response(response, request.full_url),
            content_type=_header_value(getattr(response, "headers", None), "Content-Type"),
            content_length=_header_value(getattr(response, "headers", None), "Content-Length"),
        )


def _probe_from_http_error(exc: url_error.HTTPError, *, method: str) -> UrlProbe:
    status_code = int(getattr(exc, "code", 0) or 0) or None
    return UrlProbe(
        url=str(getattr(exc, "url", "") or ""),
        ok=False,
        method=method,
        status_code=status_code,
        final_url=str(getattr(exc, "url", "") or "") or None,
        content_type=_header_value(getattr(exc, "headers", None), "Content-Type"),
        content_length=_header_value(getattr(exc, "headers", None), "Content-Length"),
        error=str(exc),
    )


def _probe_from_exception(url: str, exc: Exception, *, method: str) -> UrlProbe:
    return UrlProbe(
        url=url,
        ok=False,
        method=method,
        status_code=None,
        final_url=None,
        content_type=None,
        content_length=None,
        error=str(exc),
    )


def _status_code_from_response(response: Any) -> int | None:
    status = getattr(response, "status", None)
    if status is not None:
        try:
            return int(status)
        except (TypeError, ValueError):
            return None
    getcode = getattr(response, "getcode", None)
    if callable(getcode):
        try:
            value = getcode()
        except Exception:  # pragma: no cover - defensive
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None
    return None


def _final_url_from_response(response: Any, fallback: str) -> str | None:
    geturl = getattr(response, "geturl", None)
    if callable(geturl):
        try:
            return str(geturl() or "").strip() or fallback
        except Exception:  # pragma: no cover - defensive
            return fallback
    return fallback


def _header_value(headers: Any, key: str) -> str | None:
    if headers is None:
        return None
    getter = getattr(headers, "get", None)
    if callable(getter):
        value = getter(key)
        if value is not None:
            text = str(value).strip()
            return text or None
    return None


def _format_probe_finding(
    row: PackSourceAuditRow,
    probe: UrlProbe,
    *,
    severity: str,
    role: str,
) -> str:
    detail = probe.error or f"status={probe.status_code or 'unknown'}"
    return (
        f"[{severity}] `{row.pack_id}` ({row.pack_kind}, {role}, {row.transport_origin}) "
        f"`{detail}` -> {probe.url}"
    )


def _probe_status_label(probe: UrlProbe | None) -> str:
    if probe is None:
        return "-"
    if probe.ok:
        return f"OK ({probe.method} {probe.status_code or '?'})"
    if probe.status_code is not None:
        return f"FAIL ({probe.method} {probe.status_code})"
    return f"FAIL ({probe.method})"


__all__ = [
    "DEFAULT_JSON_OUT",
    "DEFAULT_MANIFEST_PATH",
    "DEFAULT_MARKDOWN_OUT",
    "DEFAULT_TIMEOUT_SECONDS",
    "PackSourceAuditRow",
    "PackSourceUrlAuditReport",
    "UrlProbe",
    "build_pack_source_url_audit_report",
    "parse_args",
    "print_summary",
    "probe_url",
    "render_markdown",
]
