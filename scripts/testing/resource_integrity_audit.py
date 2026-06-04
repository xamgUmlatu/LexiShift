#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
import sqlite3
import sys
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / "core"
if str(CORE_ROOT) not in sys.path:
    sys.path.insert(0, str(CORE_ROOT))

from lexishift_core.frequency.sqlite_store import validate_frequency_sqlite_db  # noqa: E402
from lexishift_core.helper.lp_capabilities import (  # noqa: E402
    default_frequency_db_path,
    known_pairs,
    resolve_pair_capability,
)
from lexishift_core.helper.paths import resolve_data_root  # noqa: E402


@dataclass(frozen=True)
class SqliteProbe:
    path: str
    exists: bool
    header_ok: bool
    has_frequency_table: bool
    row_count: int | None
    columns: list[str] = field(default_factory=list)
    error: str | None = None


@dataclass(frozen=True)
class PairAuditRow:
    pair: str
    srs_selectable: bool
    expected_pack_id: str
    expected_filename: str
    linked_key: str | None
    linked_path: str | None
    fallback_path: str
    resolved_path: str | None
    status: str
    row_count: int | None


@dataclass(frozen=True)
class SettingsEntryAuditRow:
    key: str
    path: str
    exists: bool
    header_ok: bool
    has_frequency_table: bool
    row_count: int | None
    status: str


@dataclass(frozen=True)
class FileAuditRow:
    filename: str
    path: str
    linked_keys: list[str]
    used_by_pairs: list[str]
    header_ok: bool
    has_frequency_table: bool
    row_count: int | None
    status: str


@dataclass(frozen=True)
class AuditIssue:
    severity: str
    code: str
    message: str


@dataclass(frozen=True)
class AuditReport:
    data_root: str
    settings_path: str
    frequency_dir: str
    pair_rows: list[PairAuditRow]
    settings_rows: list[SettingsEntryAuditRow]
    file_rows: list[FileAuditRow]
    issues: list[AuditIssue]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _canonical_path(path: str | Path) -> Path:
    return Path(path).expanduser().resolve(strict=False)


def _read_settings_frequency_map(settings_path: Path) -> tuple[dict[str, str], list[AuditIssue]]:
    issues: list[AuditIssue] = []
    if not settings_path.exists():
        issues.append(
            AuditIssue(
                severity="WARN",
                code="SETTINGS_MISSING",
                message=f"Settings file does not exist: {settings_path}",
            )
        )
        return {}, issues
    try:
        payload = json.loads(settings_path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        issues.append(
            AuditIssue(
                severity="ERROR",
                code="SETTINGS_PARSE_ERROR",
                message=f"Could not parse settings JSON at {settings_path}: {exc}",
            )
        )
        return {}, issues
    synonyms = payload.get("synonyms") if isinstance(payload, dict) else None
    if not isinstance(synonyms, dict):
        return {}, issues
    frequency_pack_paths = synonyms.get("frequency_pack_paths", synonyms.get("frequency_packs"))
    if not isinstance(frequency_pack_paths, dict):
        return {}, issues
    result: dict[str, str] = {}
    for key, value in frequency_pack_paths.items():
        key_text = str(key or "").strip()
        value_text = str(value or "").strip()
        if key_text:
            result[key_text] = value_text
    return result, issues


def _probe_sqlite(path: Path) -> SqliteProbe:
    candidate = _canonical_path(path)
    if not candidate.exists() or not candidate.is_file():
        return SqliteProbe(
            path=str(candidate),
            exists=False,
            header_ok=False,
            has_frequency_table=False,
            row_count=None,
            error=f"Missing file: {candidate}",
        )
    try:
        with candidate.open("rb") as handle:
            header = handle.read(16)
    except OSError as exc:
        return SqliteProbe(
            path=str(candidate),
            exists=False,
            header_ok=False,
            has_frequency_table=False,
            row_count=None,
            error=f"Failed to read file header: {exc}",
        )
    header_ok = header.startswith(b"SQLite format 3")
    if not header_ok:
        return SqliteProbe(
            path=str(candidate),
            exists=True,
            header_ok=False,
            has_frequency_table=False,
            row_count=None,
            error="Invalid SQLite header.",
        )
    try:
        validate_frequency_sqlite_db(candidate, table="frequency")
    except Exception as exc:  # noqa: BLE001
        return SqliteProbe(
            path=str(candidate),
            exists=True,
            header_ok=True,
            has_frequency_table=False,
            row_count=None,
            error=str(exc),
        )
    try:
        uri = f"{candidate.as_uri()}?mode=ro"
        with sqlite3.connect(uri, uri=True) as conn:
            row_count = int(conn.execute("SELECT COUNT(*) FROM frequency;").fetchone()[0])
            columns = [row[1] for row in conn.execute("PRAGMA table_info(frequency);").fetchall()]
    except sqlite3.Error as exc:
        return SqliteProbe(
            path=str(candidate),
            exists=True,
            header_ok=True,
            has_frequency_table=True,
            row_count=None,
            error=f"SQLite query failed: {exc}",
        )
    return SqliteProbe(
        path=str(candidate),
        exists=True,
        header_ok=True,
        has_frequency_table=True,
        row_count=row_count,
        columns=columns,
        error=None,
    )


def _expected_lookup_keys(filename: str) -> tuple[str, ...]:
    if filename.endswith(".sqlite"):
        pack_id = filename[: -len(".sqlite")]
        return pack_id, filename
    return filename, filename


def _build_pair_rows(
    *,
    frequency_dir: Path,
    settings_frequency_pack_paths: dict[str, str],
) -> tuple[list[PairAuditRow], list[AuditIssue], dict[str, list[str]]]:
    pair_rows: list[PairAuditRow] = []
    issues: list[AuditIssue] = []
    pairs_by_filename: dict[str, list[str]] = {}

    for pair in known_pairs():
        capability = resolve_pair_capability(pair)
        expected_path = default_frequency_db_path(pair, frequency_packs_dir=frequency_dir)
        if expected_path is None:
            pair_rows.append(
                PairAuditRow(
                    pair=pair,
                    srs_selectable=capability.srs_selectable,
                    expected_pack_id="-",
                    expected_filename="-",
                    linked_key=None,
                    linked_path=None,
                    fallback_path="",
                    resolved_path=None,
                    status="no_frequency_declared",
                    row_count=None,
                )
            )
            continue

        expected_filename = expected_path.name
        expected_pack_id = (
            expected_filename[: -len(".sqlite")]
            if expected_filename.endswith(".sqlite")
            else expected_filename
        )
        pairs_by_filename.setdefault(expected_filename, []).append(pair)
        lookup_keys = _expected_lookup_keys(expected_filename)

        linked_key: str | None = None
        linked_path: str | None = None
        for key in lookup_keys:
            raw_path = str(settings_frequency_pack_paths.get(key, "")).strip()
            if raw_path:
                linked_key = key
                linked_path = raw_path
                break

        fallback_path = _canonical_path(expected_path)
        linked_candidate = _canonical_path(linked_path) if linked_path else None
        fallback_exists = fallback_path.is_file()
        linked_exists = bool(linked_candidate and linked_candidate.is_file())

        resolved_path: Path | None = None
        status = "missing"

        if linked_candidate is not None and linked_exists:
            resolved_path = linked_candidate
            status = "linked"
        elif linked_candidate is not None and not linked_exists:
            if fallback_exists:
                resolved_path = fallback_path
                status = "linked_missing_fallback"
                issues.append(
                    AuditIssue(
                        severity="WARN",
                        code="FREQ_LINK_BROKEN_FALLBACK_USED",
                        message=(
                            f"{pair}: settings key '{linked_key}' points to missing file "
                            f"({linked_candidate}), fallback file exists at {fallback_path}."
                        ),
                    )
                )
            else:
                status = "linked_missing"
                level = "ERROR" if capability.srs_selectable else "WARN"
                issues.append(
                    AuditIssue(
                        severity=level,
                        code="FREQ_LINK_BROKEN",
                        message=(
                            f"{pair}: settings key '{linked_key}' points to missing file "
                            f"({linked_candidate}), and fallback file is missing ({fallback_path})."
                        ),
                    )
                )
        elif fallback_exists:
            resolved_path = fallback_path
            status = "downloaded_unlinked"
            issues.append(
                AuditIssue(
                    severity="WARN",
                    code="FREQ_DOWNLOADED_UNLINKED",
                    message=(
                        f"{pair}: downloaded frequency DB exists at {fallback_path} but no "
                        f"settings link was found for keys {lookup_keys}."
                    ),
                )
            )
        else:
            level = "ERROR" if capability.srs_selectable else "WARN"
            issues.append(
                AuditIssue(
                    severity=level,
                    code="FREQ_MISSING",
                    message=(
                        f"{pair}: no linked frequency DB and fallback file missing ({fallback_path})."
                    ),
                )
            )

        row_count: int | None = None
        if resolved_path is not None:
            probe = _probe_sqlite(resolved_path)
            if probe.has_frequency_table:
                row_count = probe.row_count
            if not probe.header_ok or not probe.has_frequency_table:
                issues.append(
                    AuditIssue(
                        severity="ERROR",
                        code="FREQ_INVALID_SQLITE",
                        message=f"{pair}: {probe.error or f'Invalid SQLite file at {resolved_path}'}",
                    )
                )
                status = "invalid_sqlite"
            elif probe.row_count == 0:
                issues.append(
                    AuditIssue(
                        severity="WARN",
                        code="FREQ_EMPTY_TABLE",
                        message=f"{pair}: frequency table is empty in {resolved_path}.",
                    )
                )
                if status == "linked":
                    status = "linked_empty"
                elif status == "downloaded_unlinked":
                    status = "downloaded_unlinked_empty"
            elif (
                status == "linked"
                and fallback_exists
                and linked_candidate is not None
                and linked_candidate != fallback_path
            ):
                status = "linked_external"

        pair_rows.append(
            PairAuditRow(
                pair=pair,
                srs_selectable=capability.srs_selectable,
                expected_pack_id=expected_pack_id,
                expected_filename=expected_filename,
                linked_key=linked_key,
                linked_path=str(linked_candidate) if linked_candidate else None,
                fallback_path=str(fallback_path),
                resolved_path=str(resolved_path) if resolved_path else None,
                status=status,
                row_count=row_count,
            )
        )

    return pair_rows, issues, pairs_by_filename


def _build_settings_rows(
    *,
    settings_frequency_pack_paths: dict[str, str],
    known_lookup_keys: set[str],
) -> tuple[list[SettingsEntryAuditRow], list[AuditIssue]]:
    rows: list[SettingsEntryAuditRow] = []
    issues: list[AuditIssue] = []

    for key in sorted(settings_frequency_pack_paths):
        raw_path = str(settings_frequency_pack_paths.get(key, "")).strip()
        candidate = _canonical_path(raw_path) if raw_path else Path("")
        probe = (
            _probe_sqlite(candidate)
            if raw_path
            else SqliteProbe(
                path="",
                exists=False,
                header_ok=False,
                has_frequency_table=False,
                row_count=None,
                error="Empty path.",
            )
        )

        status = "ok"
        if not raw_path:
            status = "empty_path"
            issues.append(
                AuditIssue(
                    severity="ERROR",
                    code="SETTINGS_EMPTY_PATH",
                    message=f"settings.synonyms.frequency_pack_paths['{key}'] is empty.",
                )
            )
        elif not probe.exists:
            status = "missing"
            issues.append(
                AuditIssue(
                    severity="ERROR",
                    code="SETTINGS_PATH_MISSING",
                    message=f"settings key '{key}' points to missing file: {candidate}",
                )
            )
        elif not probe.header_ok or not probe.has_frequency_table:
            status = "invalid_sqlite"
            issues.append(
                AuditIssue(
                    severity="ERROR",
                    code="SETTINGS_INVALID_SQLITE",
                    message=f"settings key '{key}' has invalid DB: {probe.error}",
                )
            )
        elif probe.row_count == 0:
            status = "empty_table"
            issues.append(
                AuditIssue(
                    severity="WARN",
                    code="SETTINGS_EMPTY_TABLE",
                    message=f"settings key '{key}' points to an empty frequency table: {candidate}",
                )
            )

        if key not in known_lookup_keys:
            issues.append(
                AuditIssue(
                    severity="WARN",
                    code="SETTINGS_UNKNOWN_KEY",
                    message=(
                        f"settings key '{key}' is not used by current pair defaults. "
                        "Check for stale or typo keys."
                    ),
                )
            )
            if status == "ok":
                status = "ok_unknown_key"

        rows.append(
            SettingsEntryAuditRow(
                key=key,
                path=str(candidate),
                exists=probe.exists,
                header_ok=probe.header_ok,
                has_frequency_table=probe.has_frequency_table,
                row_count=probe.row_count,
                status=status,
            )
        )
    return rows, issues


def _build_file_rows(
    *,
    frequency_dir: Path,
    settings_frequency_pack_paths: dict[str, str],
    pairs_by_filename: dict[str, list[str]],
) -> tuple[list[FileAuditRow], list[AuditIssue]]:
    issues: list[AuditIssue] = []
    rows: list[FileAuditRow] = []

    linked_by_path: dict[str, list[str]] = {}
    for key, raw_path in settings_frequency_pack_paths.items():
        path_text = str(raw_path or "").strip()
        if not path_text:
            continue
        canonical = str(_canonical_path(path_text))
        linked_by_path.setdefault(canonical, []).append(key)

    discovered_paths: set[Path] = set()
    if frequency_dir.exists():
        for pattern in ("*.sqlite", "*.sqlite3", "*.db"):
            for file_path in sorted(frequency_dir.glob(pattern)):
                if file_path.is_file():
                    discovered_paths.add(_canonical_path(file_path))

    for file_path in sorted(discovered_paths):
        probe = _probe_sqlite(file_path)
        linked_keys = sorted(linked_by_path.get(str(file_path), []))
        used_by_pairs = sorted(pairs_by_filename.get(file_path.name, []))
        status = "ok"

        if not probe.header_ok or not probe.has_frequency_table:
            status = "invalid_sqlite"
            issues.append(
                AuditIssue(
                    severity="ERROR",
                    code="FILE_INVALID_SQLITE",
                    message=f"Downloaded DB is invalid: {file_path} ({probe.error})",
                )
            )
        elif probe.row_count == 0:
            status = "empty_table"
            issues.append(
                AuditIssue(
                    severity="WARN",
                    code="FILE_EMPTY_TABLE",
                    message=f"Downloaded DB has empty frequency table: {file_path}",
                )
            )

        if not linked_keys:
            issues.append(
                AuditIssue(
                    severity="WARN",
                    code="FILE_UNLINKED",
                    message=f"Downloaded DB is not linked in settings: {file_path}",
                )
            )
            if status == "ok":
                status = "unlinked"
            elif status == "empty_table":
                status = "unlinked_empty"

        rows.append(
            FileAuditRow(
                filename=file_path.name,
                path=str(file_path),
                linked_keys=linked_keys,
                used_by_pairs=used_by_pairs,
                header_ok=probe.header_ok,
                has_frequency_table=probe.has_frequency_table,
                row_count=probe.row_count,
                status=status,
            )
        )

    return rows, issues


def run_audit(
    *,
    data_root: Path,
    settings_path: Path,
    frequency_dir: Path,
) -> AuditReport:
    settings_frequency_pack_paths, settings_issues = _read_settings_frequency_map(settings_path)
    pair_rows, pair_issues, pairs_by_filename = _build_pair_rows(
        frequency_dir=frequency_dir,
        settings_frequency_pack_paths=settings_frequency_pack_paths,
    )
    known_lookup_keys: set[str] = set()
    for row in pair_rows:
        if row.expected_filename and row.expected_filename != "-":
            known_lookup_keys.update(_expected_lookup_keys(row.expected_filename))
    settings_rows, settings_entry_issues = _build_settings_rows(
        settings_frequency_pack_paths=settings_frequency_pack_paths,
        known_lookup_keys=known_lookup_keys,
    )
    file_rows, file_issues = _build_file_rows(
        frequency_dir=frequency_dir,
        settings_frequency_pack_paths=settings_frequency_pack_paths,
        pairs_by_filename=pairs_by_filename,
    )
    all_issues = [*settings_issues, *pair_issues, *settings_entry_issues, *file_issues]
    unique_issues: dict[tuple[str, str, str], AuditIssue] = {}
    for issue in all_issues:
        key = (issue.severity, issue.code, issue.message)
        unique_issues[key] = issue
    return AuditReport(
        data_root=str(_canonical_path(data_root)),
        settings_path=str(_canonical_path(settings_path)),
        frequency_dir=str(_canonical_path(frequency_dir)),
        pair_rows=pair_rows,
        settings_rows=settings_rows,
        file_rows=file_rows,
        issues=list(unique_issues.values()),
    )


def _short_path(path_text: str | None, *, data_root: Path) -> str:
    if not path_text:
        return "-"
    path = _canonical_path(path_text)
    root = _canonical_path(data_root)
    try:
        relative = path.relative_to(root)
        return f"$DATA_ROOT/{relative.as_posix()}"
    except ValueError:
        return str(path)


def _render_table(headers: list[str], rows: list[list[str]]) -> str:
    if not rows:
        return "(none)"
    widths = [len(header) for header in headers]
    for row in rows:
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], len(cell))
    sep = "-+-".join("-" * width for width in widths)
    header_line = " | ".join(header.ljust(widths[idx]) for idx, header in enumerate(headers))
    lines = [header_line, sep]
    for row in rows:
        lines.append(" | ".join(cell.ljust(widths[idx]) for idx, cell in enumerate(row)))
    return "\n".join(lines)


def print_report(report: AuditReport) -> None:
    data_root = Path(report.data_root)
    error_count = sum(1 for item in report.issues if item.severity == "ERROR")
    warning_count = sum(1 for item in report.issues if item.severity == "WARN")
    print("LexiShift Frequency Resource Audit")
    print(f"- data_root: {report.data_root}")
    print(f"- settings: {report.settings_path}")
    print(f"- frequency_dir: {report.frequency_dir}")
    print(
        f"- pairs: {len(report.pair_rows)} | settings entries: {len(report.settings_rows)} "
        f"| files: {len(report.file_rows)}"
    )
    print(f"- errors: {error_count} | warnings: {warning_count}")

    pair_table = []
    for row in report.pair_rows:
        pair_table.append(
            [
                row.pair,
                "yes" if row.srs_selectable else "no",
                row.expected_filename,
                row.linked_key or "-",
                _short_path(row.resolved_path, data_root=data_root),
                row.status,
                str(row.row_count) if row.row_count is not None else "-",
            ]
        )
    print("\nPair Coverage")
    print(
        _render_table(
            ["pair", "srs", "expected_db", "link_key", "resolved_path", "status", "rows"],
            pair_table,
        )
    )

    settings_table = []
    for row in report.settings_rows:
        settings_table.append(
            [
                row.key,
                _short_path(row.path, data_root=data_root),
                "yes" if row.exists else "no",
                "yes" if row.header_ok else "no",
                "yes" if row.has_frequency_table else "no",
                str(row.row_count) if row.row_count is not None else "-",
                row.status,
            ]
        )
    print("\nSettings Entries")
    print(
        _render_table(
            ["key", "path", "exists", "sqlite", "frequency_table", "rows", "status"],
            settings_table,
        )
    )

    file_table = []
    for row in report.file_rows:
        file_table.append(
            [
                row.filename,
                ",".join(row.linked_keys) if row.linked_keys else "-",
                ",".join(row.used_by_pairs) if row.used_by_pairs else "-",
                "yes" if row.header_ok else "no",
                "yes" if row.has_frequency_table else "no",
                str(row.row_count) if row.row_count is not None else "-",
                row.status,
            ]
        )
    print("\nDownloaded Files")
    print(
        _render_table(
            ["filename", "linked_keys", "pairs", "sqlite", "frequency_table", "rows", "status"],
            file_table,
        )
    )

    print("\nIssues")
    if not report.issues:
        print("- none")
        return
    ordered = sorted(
        report.issues,
        key=lambda issue: (0 if issue.severity == "ERROR" else 1, issue.code, issue.message),
    )
    for issue in ordered:
        print(f"- [{issue.severity}] {issue.code}: {issue.message}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Audit frequency pack linkage/integrity for LexiShift.\n"
            "Checks file existence, SQLite header, required frequency table, and settings links."
        )
    )
    parser.add_argument(
        "--data-root",
        type=Path,
        help=("LexiShift data root override. Default is platform path or LEXISHIFT_DATA_DIR."),
    )
    parser.add_argument(
        "--settings-path",
        type=Path,
        help="settings.json override. Default: <data_root>/settings.json.",
    )
    parser.add_argument(
        "--frequency-dir",
        type=Path,
        help="frequency_packs dir override. Default: <data_root>/frequency_packs.",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        help="Optional path to write the full JSON report.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with code 1 when warnings are present (not only errors).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    data_root = _canonical_path(args.data_root or resolve_data_root())
    settings_path = _canonical_path(args.settings_path or (data_root / "settings.json"))
    frequency_dir = _canonical_path(args.frequency_dir or (data_root / "frequency_packs"))

    report = run_audit(
        data_root=data_root,
        settings_path=settings_path,
        frequency_dir=frequency_dir,
    )
    print_report(report)

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(
            json.dumps(report.to_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"\nWrote JSON report: {args.json_out}")

    error_count = sum(1 for item in report.issues if item.severity == "ERROR")
    warning_count = sum(1 for item in report.issues if item.severity == "WARN")
    if error_count:
        return 1
    if args.strict and warning_count:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
