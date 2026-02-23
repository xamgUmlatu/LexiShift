#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import sqlite3
import sys
from typing import Any, Mapping

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / "core"
if str(CORE_ROOT) not in sys.path:
    sys.path.insert(0, str(CORE_ROOT))

from lexishift_core.helper.lp_capabilities import default_frequency_db_path, known_pairs  # noqa: E402
from lexishift_core.helper.paths import resolve_data_root  # noqa: E402


@dataclass(frozen=True)
class PackPosAuditRow:
    filename: str
    path: str
    exists: bool
    status: str
    row_count: int | None
    rows_with_pos: int | None
    rows_without_pos: int | None
    pos_inventory_size: int | None
    unknown_pos_inventory_size: int | None
    pos_source_provider: str | None
    pos_mapping_profile: str | None
    pos_columns_resolved: list[str]
    unknown_pos_inventory_top: list[dict[str, object]]
    error: str | None = None


@dataclass(frozen=True)
class PosAuditIssue:
    severity: str
    code: str
    message: str


@dataclass(frozen=True)
class PosInventoryAuditReport:
    data_root: str
    frequency_dir: str
    rows: list[PackPosAuditRow]
    issues: list[PosAuditIssue]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit frequency pack POS inventory metadata (rows_with_pos/unknown tags/provider profile)."
    )
    parser.add_argument(
        "--data-root",
        type=Path,
        default=Path(resolve_data_root()),
        help="LexiShift data root (default: helper resolve_data_root())",
    )
    parser.add_argument(
        "--top-unknown",
        type=int,
        default=10,
        help="Top unknown POS tags to include per pack (default: 10)",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        default=None,
        help="Optional output path for JSON report artifact",
    )
    return parser.parse_args()


def _read_meta_metadata(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    if not path.exists() or not path.is_file():
        return None, f"Missing file: {path}"
    try:
        with path.open("rb") as handle:
            header = handle.read(16)
        if not header.startswith(b"SQLite format 3"):
            return None, "Invalid SQLite header."
    except OSError as exc:
        return None, f"Failed to read SQLite header: {exc}"
    try:
        uri = f"{path.as_uri()}?mode=ro"
        with sqlite3.connect(uri, uri=True) as conn:
            row = conn.execute("SELECT value FROM meta WHERE key='metadata';").fetchone()
            if row is None:
                return None, "Missing meta.metadata row."
            payload = json.loads(str(row[0]))
            if not isinstance(payload, dict):
                return None, "meta.metadata is not a JSON object."
            return payload, None
    except sqlite3.Error as exc:
        return None, f"SQLite query failed: {exc}"
    except Exception as exc:  # noqa: BLE001
        return None, f"Failed to parse metadata JSON: {exc}"


def _as_int(value: object) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _as_str(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _as_str_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    result: list[str] = []
    for item in value:
        text = str(item or "").strip()
        if text:
            result.append(text)
    return result


def _as_dict_list(value: object, *, limit: int) -> list[dict[str, object]]:
    if not isinstance(value, list):
        return []
    result: list[dict[str, object]] = []
    for item in value[: max(0, int(limit))]:
        if isinstance(item, dict):
            tag = str(item.get("tag") or "").strip()
            count = _as_int(item.get("count"))
            if tag and count is not None:
                result.append({"tag": tag, "count": count})
    return result


def _extract_pos_payload(meta_metadata: Mapping[str, object]) -> Mapping[str, object]:
    # DE build path writes POS inventory under `meta.metadata.pos_inventory`.
    nested = meta_metadata.get("pos_inventory")
    if isinstance(nested, Mapping):
        return nested
    return meta_metadata


def _collect_candidate_paths(frequency_dir: Path) -> list[Path]:
    candidates: dict[str, Path] = {}

    for pair in known_pairs():
        default_path = default_frequency_db_path(pair, frequency_packs_dir=frequency_dir)
        if default_path is None:
            continue
        resolved = default_path.expanduser().resolve(strict=False)
        candidates[str(resolved)] = resolved

    if frequency_dir.exists() and frequency_dir.is_dir():
        for path in frequency_dir.glob("*.sqlite"):
            resolved = path.expanduser().resolve(strict=False)
            candidates[str(resolved)] = resolved

    ordered = sorted(candidates.values(), key=lambda item: item.name.lower())
    return ordered


def build_pos_inventory_report(
    *,
    data_root: Path,
    top_unknown: int,
) -> PosInventoryAuditReport:
    resolved_root = data_root.expanduser().resolve(strict=False)
    frequency_dir = resolved_root / "frequency_packs"
    rows: list[PackPosAuditRow] = []
    issues: list[PosAuditIssue] = []

    for path in _collect_candidate_paths(frequency_dir):
        filename = path.name
        if not path.exists():
            rows.append(
                PackPosAuditRow(
                    filename=filename,
                    path=str(path),
                    exists=False,
                    status="missing",
                    row_count=None,
                    rows_with_pos=None,
                    rows_without_pos=None,
                    pos_inventory_size=None,
                    unknown_pos_inventory_size=None,
                    pos_source_provider=None,
                    pos_mapping_profile=None,
                    pos_columns_resolved=[],
                    unknown_pos_inventory_top=[],
                    error="Missing file.",
                )
            )
            continue

        meta_metadata, error = _read_meta_metadata(path)
        if meta_metadata is None:
            rows.append(
                PackPosAuditRow(
                    filename=filename,
                    path=str(path),
                    exists=True,
                    status="invalid_or_missing_meta",
                    row_count=None,
                    rows_with_pos=None,
                    rows_without_pos=None,
                    pos_inventory_size=None,
                    unknown_pos_inventory_size=None,
                    pos_source_provider=None,
                    pos_mapping_profile=None,
                    pos_columns_resolved=[],
                    unknown_pos_inventory_top=[],
                    error=error,
                )
            )
            issues.append(
                PosAuditIssue(
                    severity="ERROR",
                    code="POS_AUDIT_METADATA_UNREADABLE",
                    message=f"{filename}: {error}",
                )
            )
            continue

        row_count = _as_int(meta_metadata.get("row_count"))
        pos_payload = _extract_pos_payload(meta_metadata)
        rows_with_pos = _as_int(pos_payload.get("rows_with_pos"))
        rows_without_pos = _as_int(pos_payload.get("rows_without_pos"))
        pos_inventory_size = _as_int(pos_payload.get("pos_inventory_size"))
        unknown_pos_inventory_size = _as_int(pos_payload.get("unknown_pos_inventory_size"))
        pos_source_provider = _as_str(pos_payload.get("pos_source_provider"))
        pos_mapping_profile = _as_str(pos_payload.get("pos_mapping_profile"))
        pos_columns_resolved = _as_str_list(pos_payload.get("pos_columns_resolved"))
        unknown_pos_inventory_top = _as_dict_list(
            pos_payload.get("unknown_pos_inventory_top"),
            limit=top_unknown,
        )

        has_inventory = (
            rows_with_pos is not None
            and rows_without_pos is not None
            and pos_inventory_size is not None
            and unknown_pos_inventory_size is not None
        )
        if has_inventory:
            status = "ok"
        else:
            status = "missing_pos_inventory"
            issues.append(
                PosAuditIssue(
                    severity="WARN",
                    code="POS_INVENTORY_MISSING",
                    message=f"{filename}: metadata exists but POS inventory fields are missing.",
                )
            )

        if unknown_pos_inventory_size and unknown_pos_inventory_size > 0:
            issues.append(
                PosAuditIssue(
                    severity="WARN",
                    code="POS_UNKNOWN_TAGS_PRESENT",
                    message=(
                        f"{filename}: unknown_pos_inventory_size={unknown_pos_inventory_size}; "
                        f"top={unknown_pos_inventory_top[:3]}"
                    ),
                )
            )

        rows.append(
            PackPosAuditRow(
                filename=filename,
                path=str(path),
                exists=True,
                status=status,
                row_count=row_count,
                rows_with_pos=rows_with_pos,
                rows_without_pos=rows_without_pos,
                pos_inventory_size=pos_inventory_size,
                unknown_pos_inventory_size=unknown_pos_inventory_size,
                pos_source_provider=pos_source_provider,
                pos_mapping_profile=pos_mapping_profile,
                pos_columns_resolved=pos_columns_resolved,
                unknown_pos_inventory_top=unknown_pos_inventory_top,
                error=None,
            )
        )

    return PosInventoryAuditReport(
        data_root=str(resolved_root),
        frequency_dir=str(frequency_dir),
        rows=rows,
        issues=issues,
    )


def _print_summary(report: PosInventoryAuditReport) -> None:
    print("LexiShift POS Inventory Audit")
    print(f"- data_root: {report.data_root}")
    print(f"- frequency_dir: {report.frequency_dir}")
    print(f"- packs: {len(report.rows)}")
    warn_count = sum(1 for issue in report.issues if issue.severity == "WARN")
    err_count = sum(1 for issue in report.issues if issue.severity == "ERROR")
    print(f"- errors: {err_count} | warnings: {warn_count}")
    print("")
    print("Pack Summary")
    print(
        "filename".ljust(22)
        + " | "
        + "status".ljust(22)
        + " | "
        + "rows_with_pos".rjust(12)
        + " | "
        + "unknown".rjust(8)
        + " | "
        + "provider/profile"
    )
    print("-" * 96)
    for row in report.rows:
        provider = row.pos_source_provider or "-"
        profile = row.pos_mapping_profile or "-"
        provider_profile = f"{provider}/{profile}"
        rows_with_pos = "-" if row.rows_with_pos is None else str(row.rows_with_pos)
        unknown = "-" if row.unknown_pos_inventory_size is None else str(row.unknown_pos_inventory_size)
        print(
            row.filename.ljust(22)
            + " | "
            + row.status.ljust(22)
            + " | "
            + rows_with_pos.rjust(12)
            + " | "
            + unknown.rjust(8)
            + " | "
            + provider_profile
        )
    if report.issues:
        print("")
        print("Issues")
        for issue in report.issues:
            print(f"- [{issue.severity}] {issue.code}: {issue.message}")


def main() -> int:
    args = _parse_args()
    report = build_pos_inventory_report(
        data_root=Path(args.data_root),
        top_unknown=max(0, int(args.top_unknown)),
    )
    _print_summary(report)
    if args.json_out:
        out_path = Path(args.json_out).expanduser().resolve(strict=False)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            json.dumps(report.to_dict(), indent=2, sort_keys=True),
            encoding="utf-8",
        )
        print("")
        print(f"Wrote JSON report: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
