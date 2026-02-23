#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import gzip
import io
import json
from pathlib import Path
import re
import sys
from typing import Any
from urllib import error as url_error
from urllib import request as url_request

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / "core"
if str(CORE_ROOT) not in sys.path:
    sys.path.insert(0, str(CORE_ROOT))

from lexishift_core.helper.paths import resolve_data_root  # noqa: E402

REGISTER_PATH = PROJECT_ROOT / "docs" / "language_pairs" / "data_source_licensing_and_distribution.md"
URL_REGISTRY_PATH = PROJECT_ROOT / "docs" / "language_pairs" / "language_pack_urls.txt"
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "licensing_header_audit"
    / "latest.json"
)

LICENSE_KEYWORDS = (
    "license",
    "licence",
    "copyright",
    "creative commons",
    "cc by",
    "cc-by",
    "sharealike",
    "gpl",
    "agpl",
    "lgpl",
    "bsd",
    "public domain",
)

PACK_ID_ALIASES = {
    "embed-en-cc": "align-en-cc",
    "embed-de-cc": "align-de-cc",
    "embed-es-cc": "align-es-cc",
    "embed-ja-cc": "align-ja-cc",
    "embed-xling-en": "align-en-wiki",
    "embed-xling-de": "align-de-wiki",
    "embed-xling-es": "align-es-wiki",
    "embed-xling-ja": "align-ja-wiki",
}


@dataclass(frozen=True)
class UrlProbe:
    url: str
    ok: bool
    status_code: int | None
    final_url: str | None
    content_type: str | None
    content_length: str | None
    sampled_bytes: int
    preview_lines: list[str] = field(default_factory=list)
    license_hits: list[str] = field(default_factory=list)
    error: str | None = None


@dataclass(frozen=True)
class LocalArtifactProbe:
    path: str | None
    exists: bool
    sqlite_header_ok: bool | None
    preview_lines: list[str] = field(default_factory=list)
    license_hits: list[str] = field(default_factory=list)
    error: str | None = None


@dataclass(frozen=True)
class LicenseAuditRow:
    pack_id: str
    row_status: str
    distribution_mode: str
    artifact_cell: str
    evidence_url: str
    source_url: str | None
    source_url_note: str | None
    local_artifact: LocalArtifactProbe
    evidence_probe: UrlProbe | None
    source_probe: UrlProbe | None


@dataclass(frozen=True)
class LicenseAuditReport:
    generated_at: str
    register_path: str
    url_registry_path: str
    status_filter: list[str]
    max_bytes: int
    rows: list[LicenseAuditRow]
    issues: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Download and inspect header/license snippets for rows in the licensing register."
        )
    )
    parser.add_argument(
        "--register",
        type=Path,
        default=REGISTER_PATH,
        help="Path to the licensing register markdown.",
    )
    parser.add_argument(
        "--url-registry",
        type=Path,
        default=URL_REGISTRY_PATH,
        help="Path to language_pack_urls registry.",
    )
    parser.add_argument(
        "--data-root",
        type=Path,
        default=Path(resolve_data_root()),
        help="LexiShift data root for resolving $DATA_ROOT artifact paths.",
    )
    parser.add_argument(
        "--status",
        dest="status_filters",
        action="append",
        default=None,
        help=(
            "Status filter from the licensing table. Repeat for multiple values. "
            "Default: expected-not-verified."
        ),
    )
    parser.add_argument(
        "--max-bytes",
        type=int,
        default=262_144,
        help="Maximum bytes sampled per URL request (default: 262144).",
    )
    parser.add_argument(
        "--max-lines",
        type=int,
        default=30,
        help="Maximum preview lines retained per probe (default: 30).",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=20.0,
        help="HTTP timeout in seconds (default: 20).",
    )
    parser.add_argument(
        "--skip-remote",
        action="store_true",
        help="Skip URL downloads; only parse table + probe local artifacts.",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        default=DEFAULT_JSON_OUT,
        help="JSON output path.",
    )
    return parser.parse_args()


def parse_register_table(register_path: Path) -> list[dict[str, str]]:
    text = register_path.read_text(encoding="utf-8")
    lines = text.splitlines()

    in_pack_register = False
    headers: list[str] = []
    rows: list[dict[str, str]] = []

    for line in lines:
        stripped = line.strip()
        if stripped == "## Pack Register":
            in_pack_register = True
            headers = []
            continue
        if not in_pack_register:
            continue
        if stripped.startswith("## ") and stripped != "## Pack Register":
            break
        if not stripped.startswith("|"):
            continue

        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if not headers:
            headers = cells
            continue
        if all(set(cell) <= {"-", ":", " "} for cell in cells):
            continue

        if len(cells) < len(headers):
            cells.extend([""] * (len(headers) - len(cells)))
        if len(cells) > len(headers):
            cells = cells[: len(headers)]

        rows.append({headers[index]: cells[index] for index in range(len(headers))})

    return rows


def parse_pack_ids(pack_id_cell: str) -> list[str]:
    tokens = [token.strip() for token in re.findall(r"`([^`]+)`", pack_id_cell)]
    if not tokens:
        tokens = [pack_id_cell.strip().strip("`")]

    expanded: list[str] = []
    for token in tokens:
        if not token:
            continue
        if token == "embed-xling-en/de/es/ja":
            expanded.extend(
                [
                    "embed-xling-en",
                    "embed-xling-de",
                    "embed-xling-es",
                    "embed-xling-ja",
                ]
            )
            continue
        expanded.append(token)

    deduped: list[str] = []
    seen: set[str] = set()
    for item in expanded:
        if item not in seen:
            seen.add(item)
            deduped.append(item)
    return deduped


def parse_url_registry(url_registry_path: Path) -> dict[str, str]:
    mapping: dict[str, str] = {}
    current_pack_id: str | None = None

    for raw_line in url_registry_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line.startswith("pack_id:"):
            current_pack_id = line.split(":", 1)[1].strip()
            continue
        if current_pack_id and line.startswith("url:"):
            mapping[current_pack_id] = line.split(":", 1)[1].strip()

    return mapping


def resolve_source_url(
    pack_id: str,
    url_mapping: dict[str, str],
) -> tuple[str | None, str | None]:
    direct = url_mapping.get(pack_id)
    if direct:
        return direct, "registry"
    alias = PACK_ID_ALIASES.get(pack_id)
    if alias:
        aliased = url_mapping.get(alias)
        if aliased:
            return aliased, f"alias:{alias}"
    return None, None


def _scan_license_hits(lines: list[str]) -> list[str]:
    hits: list[str] = []
    for line in lines:
        lower = line.lower()
        if any(keyword in lower for keyword in LICENSE_KEYWORDS):
            hits.append(line)
    return hits[:10]


def _strip_inline_code(text: str) -> str:
    return str(text or "").strip().strip("`").strip()


def _clean_preview_line(line: str) -> str:
    return " ".join(line.strip().split())


def _decode_text_preview(raw_bytes: bytes, *, max_lines: int) -> list[str]:
    if not raw_bytes:
        return []
    if b"\x00" in raw_bytes[:2048]:
        return []
    decoded = raw_bytes.decode("utf-8", errors="replace")
    sample = decoded[:4096]
    if not sample:
        return []
    printable = sum(1 for char in sample if (char.isprintable() or char in "\n\r\t"))
    if printable / max(1, len(sample)) < 0.70:
        return []
    lines = [_clean_preview_line(line) for line in decoded.splitlines()]
    lines = [line for line in lines if line]
    return lines[:max_lines]


def _maybe_decode_gzip_preview(raw_bytes: bytes, *, max_lines: int) -> list[str]:
    if not raw_bytes:
        return []
    try:
        with gzip.GzipFile(fileobj=io.BytesIO(raw_bytes)) as gz_handle:
            decoded = gz_handle.read(512_000)
    except Exception:  # noqa: BLE001
        return []
    return _decode_text_preview(decoded, max_lines=max_lines)


def _looks_gzip(url: str, content_type: str | None) -> bool:
    lower_url = url.lower()
    lower_type = (content_type or "").lower()
    if lower_url.endswith(".gz") or lower_url.endswith(".gzip"):
        return True
    return "application/gzip" in lower_type or "application/x-gzip" in lower_type


def probe_url(
    url: str,
    *,
    max_bytes: int,
    max_lines: int,
    timeout_seconds: float,
) -> UrlProbe:
    cleaned_url = str(url or "").strip().strip("`")
    if not cleaned_url or cleaned_url.lower() == "local file":
        return UrlProbe(
            url=cleaned_url,
            ok=False,
            status_code=None,
            final_url=None,
            content_type=None,
            content_length=None,
            sampled_bytes=0,
            error="No remote URL to probe.",
        )

    headers = {"User-Agent": "LexiShift licensing-header-audit/1.0"}
    request = url_request.Request(
        cleaned_url,
        headers={**headers, "Range": f"bytes=0-{max(0, max_bytes - 1)}"},
    )

    try:
        with url_request.urlopen(request, timeout=timeout_seconds) as response:
            status_code = getattr(response, "status", None)
            final_url = response.geturl()
            content_type = response.headers.get("Content-Type")
            content_length = response.headers.get("Content-Length")
            payload = response.read(max_bytes)
    except url_error.HTTPError as exc:
        return UrlProbe(
            url=cleaned_url,
            ok=False,
            status_code=exc.code,
            final_url=cleaned_url,
            content_type=exc.headers.get("Content-Type") if exc.headers else None,
            content_length=exc.headers.get("Content-Length") if exc.headers else None,
            sampled_bytes=0,
            error=f"HTTPError: {exc.code} {exc.reason}",
        )
    except Exception as exc:  # noqa: BLE001
        return UrlProbe(
            url=cleaned_url,
            ok=False,
            status_code=None,
            final_url=cleaned_url,
            content_type=None,
            content_length=None,
            sampled_bytes=0,
            error=str(exc),
        )

    preview_lines = _decode_text_preview(payload, max_lines=max_lines)
    if not preview_lines and _looks_gzip(cleaned_url, content_type):
        preview_lines = _maybe_decode_gzip_preview(payload, max_lines=max_lines)
    license_hits = _scan_license_hits(preview_lines)

    return UrlProbe(
        url=cleaned_url,
        ok=(status_code is not None and 200 <= status_code < 400),
        status_code=status_code,
        final_url=final_url,
        content_type=content_type,
        content_length=content_length,
        sampled_bytes=len(payload),
        preview_lines=preview_lines,
        license_hits=license_hits,
        error=None,
    )


def _resolve_artifact_path(artifact_cell: str, data_root: Path) -> Path | None:
    cleaned = artifact_cell.replace("`", "").strip()
    if "$DATA_ROOT" not in cleaned:
        return None
    cleaned = cleaned.split("(", 1)[0].strip()
    if "*" in cleaned:
        return None
    resolved = cleaned.replace("$DATA_ROOT", str(data_root))
    return Path(resolved).expanduser().resolve(strict=False)


def probe_local_artifact(path: Path | None, *, max_lines: int) -> LocalArtifactProbe:
    if path is None:
        return LocalArtifactProbe(
            path=None,
            exists=False,
            sqlite_header_ok=None,
            error="Artifact path not concrete (wildcard or non-$DATA_ROOT path).",
        )
    if not path.exists():
        return LocalArtifactProbe(
            path=str(path),
            exists=False,
            sqlite_header_ok=None,
            error=f"Missing local artifact: {path}",
        )
    if path.is_dir():
        candidate_files: list[Path] = []
        for pattern in ("LICENSE*", "COPYING*", "README*", "*.md", "*.txt"):
            candidate_files.extend(path.glob(pattern))
        candidate_files = sorted(
            {candidate.resolve(strict=False) for candidate in candidate_files if candidate.is_file()},
            key=lambda item: item.name.lower(),
        )
        if candidate_files:
            first_file = candidate_files[0]
            try:
                raw = first_file.read_bytes()[:262_144]
            except OSError as exc:
                return LocalArtifactProbe(
                    path=str(path),
                    exists=True,
                    sqlite_header_ok=None,
                    error=f"Directory probe failed on {first_file.name}: {exc}",
                )
            preview_lines = _decode_text_preview(raw, max_lines=max_lines)
            return LocalArtifactProbe(
                path=str(path),
                exists=True,
                sqlite_header_ok=None,
                preview_lines=preview_lines,
                license_hits=_scan_license_hits(preview_lines),
                error=f"Directory artifact; inspected {first_file.name}.",
            )
        return LocalArtifactProbe(
            path=str(path),
            exists=True,
            sqlite_header_ok=None,
            preview_lines=[],
            license_hits=[],
            error="Directory artifact; no obvious LICENSE/README text file found.",
        )
    if not path.is_file():
        return LocalArtifactProbe(
            path=str(path),
            exists=False,
            sqlite_header_ok=None,
            error=f"Artifact exists but is not a regular file: {path}",
        )

    try:
        with path.open("rb") as handle:
            header = handle.read(16)
    except OSError as exc:
        return LocalArtifactProbe(
            path=str(path),
            exists=False,
            sqlite_header_ok=None,
            error=f"Failed to read file: {exc}",
        )

    if header.startswith(b"SQLite format 3"):
        return LocalArtifactProbe(
            path=str(path),
            exists=True,
            sqlite_header_ok=True,
            preview_lines=[],
            license_hits=[],
            error=None,
        )

    try:
        raw = path.read_bytes()[:262_144]
    except OSError as exc:
        return LocalArtifactProbe(
            path=str(path),
            exists=True,
            sqlite_header_ok=False,
            error=f"Failed to read preview bytes: {exc}",
        )
    preview_lines = _decode_text_preview(raw, max_lines=max_lines)
    return LocalArtifactProbe(
        path=str(path),
        exists=True,
        sqlite_header_ok=False,
        preview_lines=preview_lines,
        license_hits=_scan_license_hits(preview_lines),
        error=None,
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

    probe_cache: dict[str, UrlProbe] = {}

    def probe_cached(url: str) -> UrlProbe:
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
        local_artifact = probe_local_artifact(
            _resolve_artifact_path(artifact_cell, data_root),
            max_lines=max_lines,
        )

        evidence_probe: UrlProbe | None = None
        if not skip_remote:
            evidence_probe = probe_cached(evidence_url)

        for pack_id in parse_pack_ids(pack_id_cell):
            source_url, source_url_note = resolve_source_url(pack_id, url_mapping)
            source_probe: UrlProbe | None = None
            if not source_url:
                issues.append(
                    f"Missing source URL mapping for pack_id={pack_id}; "
                    "no registry URL found."
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

    report = LicenseAuditReport(
        generated_at=datetime.now(timezone.utc).isoformat(),
        register_path=str(register_path),
        url_registry_path=str(url_registry_path),
        status_filter=sorted(status_filter),
        max_bytes=max_bytes,
        rows=audit_rows,
        issues=sorted(set(issues)),
    )
    return report


def _print_summary(report: LicenseAuditReport) -> None:
    total = len(report.rows)
    evidence_hits = 0
    source_hits = 0
    missing_local = 0

    for row in report.rows:
        if row.evidence_probe and row.evidence_probe.license_hits:
            evidence_hits += 1
        if row.source_probe and row.source_probe.license_hits:
            source_hits += 1
        if not row.local_artifact.exists:
            missing_local += 1

    print(
        f"[licensing_header_audit] rows={total} "
        f"evidence_hits={evidence_hits} source_hits={source_hits} "
        f"missing_local_artifacts={missing_local}"
    )
    if report.issues:
        print("[licensing_header_audit] issues:")
        for issue in report.issues:
            print(f"  - {issue}")


def main() -> int:
    args = parse_args()
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
    json_out.write_text(json.dumps(report.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    _print_summary(report)
    print(f"[licensing_header_audit] wrote {json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
