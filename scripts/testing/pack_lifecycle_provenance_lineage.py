from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping, Sequence


def audit_provenance_lineage(provenance_path: Path) -> dict[str, object]:
    payload, load_errors = _load_json_object(provenance_path)
    source = _as_mapping(payload.get("source"))
    build = _as_mapping(payload.get("build"))
    parser_config = _as_mapping(build.get("parser_config"))
    source_version = str(source.get("source_version") or source.get("source_dump") or "").strip()
    build_command = str(build.get("command") or "").strip()
    converter_version = str(build.get("converter_version") or "").strip()
    parser_profile = str(build.get("parser_profile") or "").strip()
    return {
        "lineage_readable": provenance_path.exists() and not load_errors,
        "source_version_present": bool(source_version),
        "source_version": source_version,
        "build_command_present": bool(build_command),
        "build_command": build_command,
        "parser_config_present": bool(parser_config or parser_profile),
        "parser_profile": parser_profile,
        "parser_config_keys": sorted(str(key) for key in parser_config),
        "converter_version_present": bool(converter_version),
        "converter_version": converter_version,
    }


def lineage_summary_counts(rows: Sequence[Mapping[str, object]]) -> dict[str, int]:
    return {
        "source_version_count": _lineage_present_count(rows, "source_version_present"),
        "build_command_count": _lineage_present_count(rows, "build_command_present"),
        "parser_config_count": _lineage_present_count(rows, "parser_config_present"),
        "converter_version_count": _lineage_present_count(rows, "converter_version_present"),
    }


def render_source_build_lineage_markdown(report: Mapping[str, object]) -> list[str]:
    lines = ["## Source/Build Lineage", ""]
    lineage_rows = _provenance_lineage_rows(report)
    if not lineage_rows:
        lines.extend(["- No provenance lineage rows.", ""])
        return lines
    lines.extend(
        [
            "| Family | Pack | Source Version | Build Command | Parser Config/Profile | Converter Version |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for family_name, row, lineage in lineage_rows:
        parser_config = ", ".join(
            str(value) for value in _sequence(lineage.get("parser_config_keys"))
        )
        parser_config = parser_config or str(lineage.get("parser_profile") or "")
        lines.append(
            "| "
            f"{family_name} | "
            f"{row.get('pack_id')} | "
            f"{lineage.get('source_version') or ''} | "
            f"{lineage.get('build_command') or ''} | "
            f"{parser_config} | "
            f"{lineage.get('converter_version') or ''} |"
        )
    lines.append("")
    return lines


def _lineage_present_count(rows: Sequence[Mapping[str, object]], key: str) -> int:
    return sum(1 for row in rows if _as_mapping(row.get("provenance_lineage")).get(key))


def _provenance_lineage_rows(
    report: Mapping[str, object],
) -> list[tuple[str, Mapping[str, object], Mapping[str, object]]]:
    rows: list[tuple[str, Mapping[str, object], Mapping[str, object]]] = []
    families = _as_mapping(report.get("installed_pack_families"))
    for family_name, raw_family in families.items():
        family = _as_mapping(raw_family)
        for row in _sequence(family.get("packs")):
            row_mapping = _as_mapping(row)
            lineage = _as_mapping(row_mapping.get("provenance_lineage"))
            if lineage.get("lineage_readable"):
                rows.append((str(family_name), row_mapping, lineage))
    semantic = _as_mapping(report.get("semantic_pack_copies"))
    for row in _sequence(semantic.get("packs")):
        row_mapping = _as_mapping(row)
        lineage = _as_mapping(row_mapping.get("provenance_lineage"))
        if lineage.get("lineage_readable"):
            rows.append(("semantic", row_mapping, lineage))
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
