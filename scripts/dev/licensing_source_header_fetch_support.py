from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, field
import gzip
from pathlib import Path
import re
import tarfile
from typing import Any
from urllib import error as url_error
from urllib import parse as url_parse
from urllib import request as url_request
import zipfile

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REGISTER_PATH = PROJECT_ROOT / "docs" / "language_pairs" / "data_source_licensing_and_distribution.md"
URL_REGISTRY_PATH = PROJECT_ROOT / "docs" / "language_pairs" / "language_pack_urls.txt"
DEFAULT_JSON_OUT = (
    PROJECT_ROOT
    / "docs"
    / "test_outputs"
    / "licensing_header_audit"
    / "downloaded_headers_latest.json"
)
DEFAULT_CACHE_DIR = Path.home() / ".cache" / "lexishift" / "licensing_source_header_fetch"

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


@dataclass(frozen=True)
class EntryHeaderProbe:
    entry_name: str
    kind: str
    sampled_bytes: int
    sqlite_header_ok: bool
    preview_lines: list[str] = field(default_factory=list)
    license_hits: list[str] = field(default_factory=list)
    error: str | None = None


@dataclass(frozen=True)
class PackFetchRow:
    pack_id: str
    row_status: str
    source_url: str
    source_note: str
    downloaded_path: str | None
    downloaded_bytes: int | None
    status: str
    target_name: str | None
    probes: list[EntryHeaderProbe]
    error: str | None = None


@dataclass(frozen=True)
class FetchReport:
    generated_at: str
    register_path: str
    url_registry_path: str
    cache_dir: str
    status_filter: list[str]
    pack_filter: list[str]
    max_download_bytes: int
    rows: list[PackFetchRow]
    issues: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "DEV-only tool: download source archives/files and inspect extracted header text "
            "for licensing verification."
        )
    )
    parser.add_argument(
        "--register",
        type=Path,
        default=REGISTER_PATH,
        help="Path to licensing register markdown.",
    )
    parser.add_argument(
        "--url-registry",
        type=Path,
        default=URL_REGISTRY_PATH,
        help="Path to language_pack_urls registry.",
    )
    parser.add_argument(
        "--status",
        dest="status_filters",
        action="append",
        default=None,
        help="Status filter from licensing register (repeatable). Default: expected-not-verified.",
    )
    parser.add_argument(
        "--pack-id",
        dest="pack_ids",
        action="append",
        default=None,
        help="Optional pack-id filter (repeatable).",
    )
    parser.add_argument(
        "--max-download-bytes",
        type=int,
        default=800_000_000,
        help="Skip download when content-length exceeds this size (default: 800MB).",
    )
    parser.add_argument(
        "--sample-bytes",
        type=int,
        default=262_144,
        help="Bytes sampled from each inspected file/member (default: 262144).",
    )
    parser.add_argument(
        "--max-lines",
        type=int,
        default=40,
        help="Maximum preview lines retained per probe (default: 40).",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=60.0,
        help="HTTP timeout in seconds (default: 60).",
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=DEFAULT_CACHE_DIR,
        help="Download cache directory.",
    )
    parser.add_argument(
        "--force-redownload",
        action="store_true",
        help="Redownload even when cached file exists.",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        default=DEFAULT_JSON_OUT,
        help="JSON output report path.",
    )
    return parser.parse_args()


def _strip_code(text: str) -> str:
    return str(text or "").strip().strip("`").strip()


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


def parse_pack_ids(pack_cell: str) -> list[str]:
    tokens = [token.strip() for token in re.findall(r"`([^`]+)`", str(pack_cell or ""))]
    if not tokens:
        tokens = [str(pack_cell or "").strip()]

    expanded: list[str] = []
    for token in tokens:
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
        if not item:
            continue
        if item in seen:
            continue
        seen.add(item)
        deduped.append(item)
    return deduped


def parse_url_registry_entries(url_registry_path: Path) -> dict[str, dict[str, str]]:
    entries: dict[str, dict[str, str]] = {}
    current_pack_id: str | None = None
    current: dict[str, str] = {}

    for raw_line in url_registry_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("-- "):
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if key == "pack_id":
            if current_pack_id and current:
                entries[current_pack_id] = current
            current_pack_id = value
            current = {"pack_id": value}
            continue
        if current_pack_id is None:
            continue
        current[key] = value

    if current_pack_id and current:
        entries[current_pack_id] = current
    return entries


def _url_basename(url: str) -> str:
    parsed = url_parse.urlparse(url)
    name = Path(parsed.path).name
    return name or "download.bin"


def _clean_line(line: str) -> str:
    return " ".join(str(line or "").strip().split())


def _decode_preview_lines(raw: bytes, *, max_lines: int) -> list[str]:
    if not raw:
        return []
    if b"\x00" in raw[:2048]:
        return []
    decoded = raw.decode("utf-8", errors="replace")
    sample = decoded[:4096]
    if not sample:
        return []
    printable = sum(1 for char in sample if (char.isprintable() or char in "\n\r\t"))
    if printable / max(1, len(sample)) < 0.70:
        return []
    lines = [_clean_line(line) for line in decoded.splitlines()]
    lines = [line for line in lines if line]
    return lines[:max_lines]


def _license_hits(lines: list[str]) -> list[str]:
    hits: list[str] = []
    for line in lines:
        lower = line.lower()
        if any(keyword in lower for keyword in LICENSE_KEYWORDS):
            hits.append(line)
    return hits[:12]


def _probe_blob(name: str, blob: bytes, *, max_lines: int) -> EntryHeaderProbe:
    sqlite_header_ok = blob.startswith(b"SQLite format 3")
    if sqlite_header_ok:
        return EntryHeaderProbe(
            entry_name=name,
            kind="sqlite",
            sampled_bytes=len(blob),
            sqlite_header_ok=True,
            preview_lines=[],
            license_hits=[],
            error=None,
        )
    preview_lines = _decode_preview_lines(blob, max_lines=max_lines)
    kind = "text" if preview_lines else "binary"
    return EntryHeaderProbe(
        entry_name=name,
        kind=kind,
        sampled_bytes=len(blob),
        sqlite_header_ok=False,
        preview_lines=preview_lines,
        license_hits=_license_hits(preview_lines),
        error=None,
    )


def _choose_zip_member(names: list[str], *, target_name: str | None) -> str | None:
    if not names:
        return None
    if target_name:
        target_base = Path(target_name).name
        for name in names:
            if Path(name).name == target_base:
                return name
    for marker in ("license", "licence", "copying", "readme"):
        for name in names:
            if marker in name.lower():
                return name
    for name in names:
        if not name.endswith("/"):
            return name
    return None


def _choose_tar_member(names: list[str], *, target_name: str | None) -> str | None:
    return _choose_zip_member(names, target_name=target_name)


def inspect_downloaded_file(
    path: Path,
    *,
    target_name: str | None,
    sample_bytes: int,
    max_lines: int,
) -> tuple[list[EntryHeaderProbe], str | None]:
    probes: list[EntryHeaderProbe] = []
    filename = path.name.lower()

    try:
        if filename.endswith((".tar.gz", ".tgz", ".tar.xz", ".txz")):
            with tarfile.open(path, "r:*") as archive:
                file_members = [member for member in archive.getmembers() if member.isfile()]
                chosen_name = _choose_tar_member(
                    [member.name for member in file_members], target_name=target_name
                )
                if not chosen_name:
                    return [], "No file members found in tar archive."
                member = next((item for item in file_members if item.name == chosen_name), None)
                if member is None:
                    return [], f"Chosen tar member missing: {chosen_name}"
                handle = archive.extractfile(member)
                if handle is None:
                    return [], f"Could not extract tar member: {chosen_name}"
                blob = handle.read(sample_bytes)
                probes.append(_probe_blob(chosen_name, blob, max_lines=max_lines))
            return probes, None

        if filename.endswith(".zip"):
            with zipfile.ZipFile(path, "r") as archive:
                names = archive.namelist()
                chosen_name = _choose_zip_member(names, target_name=target_name)
                if not chosen_name:
                    return [], "No file members found in zip archive."
                with archive.open(chosen_name, "r") as handle:
                    blob = handle.read(sample_bytes)
                probes.append(_probe_blob(chosen_name, blob, max_lines=max_lines))
            return probes, None

        if filename.endswith(".gz") and not filename.endswith((".tar.gz", ".tgz")):
            with gzip.open(path, "rb") as handle:
                blob = handle.read(sample_bytes)
            entry_name = target_name or Path(path.stem).name
            probes.append(_probe_blob(entry_name, blob, max_lines=max_lines))
            return probes, None

        blob = path.read_bytes()[:sample_bytes]
        probes.append(_probe_blob(path.name, blob, max_lines=max_lines))
        return probes, None
    except Exception as exc:  # noqa: BLE001
        return probes, str(exc)


def _download(
    *,
    url: str,
    dest_path: Path,
    max_download_bytes: int,
    timeout_seconds: float,
) -> tuple[str, int | None, str | None]:
    request = url_request.Request(url, headers={"User-Agent": "LexiShift licensing-source-fetch/1.0"})
    try:
        with url_request.urlopen(request, timeout=timeout_seconds) as response:
            content_length_text = response.headers.get("Content-Length")
            content_length = int(content_length_text) if content_length_text and content_length_text.isdigit() else None
            if content_length is not None and content_length > max_download_bytes:
                return "skipped_too_large", content_length, (
                    f"content-length {content_length} exceeds max-download-bytes {max_download_bytes}"
                )
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            downloaded = 0
            with dest_path.open("wb") as handle:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    downloaded += len(chunk)
                    if downloaded > max_download_bytes:
                        return "skipped_too_large", downloaded, (
                            f"download exceeded max-download-bytes {max_download_bytes}"
                        )
                    handle.write(chunk)
            return "downloaded", downloaded, None
    except url_error.HTTPError as exc:
        return "download_error", None, f"HTTPError: {exc.code} {exc.reason}"
    except Exception as exc:  # noqa: BLE001
        return "download_error", None, str(exc)


def print_summary(report: FetchReport) -> None:
    by_status: dict[str, int] = {}
    with_hits = 0
    sqlite_headers = 0
    for row in report.rows:
        by_status[row.status] = by_status.get(row.status, 0) + 1
        for probe in row.probes:
            if probe.license_hits:
                with_hits += 1
            if probe.sqlite_header_ok:
                sqlite_headers += 1

    status_frag = ", ".join(f"{key}={value}" for key, value in sorted(by_status.items()))
    print(
        f"[licensing_source_header_fetch] rows={len(report.rows)} "
        f"license_hit_probes={with_hits} sqlite_header_probes={sqlite_headers} "
        f"statuses: {status_frag}"
    )
    if report.issues:
        print("[licensing_source_header_fetch] issues:")
        for issue in report.issues:
            print(f"  - {issue}")
