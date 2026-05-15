from __future__ import annotations

from datetime import datetime, timezone
from typing import Mapping, Sequence


def render_project_structure_markdown(report: Mapping[str, object]) -> str:
    summary = _as_mapping(report.get("summary"))
    lines = [
        "# Project Structure Inventory",
        "",
        "Status: generated evidence",
        "Role: Generated evidence",
        f"Last updated: {_date_from_generated_at(report.get('generated_at_utc'))}",
        "Purpose: enumerate repository paths and surface structure-review candidates without approving cleanup actions.",
        "",
        "This report is read-only evidence. Candidate rows are triage signals, not deletion approval.",
        "",
        "## Summary",
        "",
        "| Metric | Count |",
        "| --- | ---: |",
    ]
    for key in (
        "path_count",
        "file_count",
        "directory_count",
        "tracked_file_count",
        "untracked_file_count",
        "candidate_path_count",
        "duplicate_filename_group_count",
        "duplicate_stem_group_count",
        "unreferenced_script_candidate_count",
    ):
        lines.append(f"| `{key}` | {summary.get(key, 0)} |")

    _append_ignored_section(lines, report)
    _append_family_counts(lines, report)
    _append_candidate_counts(lines, report)
    _append_top_directories(lines, report)
    _append_generated_output_counts(lines, report)
    _append_duplicate_table(lines, "Duplicate Filenames", report.get("duplicate_filename_groups"))
    _append_duplicate_table(lines, "Duplicate Stems", report.get("duplicate_stem_groups"))
    _append_unreferenced_scripts(lines, report)
    _append_candidate_sample(lines, report)
    return "\n".join(lines).rstrip() + "\n"


def _append_ignored_section(lines: list[str], report: Mapping[str, object]) -> None:
    lines.extend(
        [
            "",
            "## Ignored During Enumeration",
            "",
            "Ignored directory names:",
            "",
        ]
    )
    for value in _sequence(report.get("ignored_dir_names")):
        lines.append(f"- `{value}`")
    lines.extend(["", "Ignored relative prefixes:", ""])
    for value in _sequence(report.get("ignored_relative_prefixes")):
        lines.append(f"- `{value}`")
    lines.extend(["", "Ignored file names:", ""])
    for value in _sequence(report.get("ignored_file_names")):
        lines.append(f"- `{value}`")


def _append_family_counts(lines: list[str], report: Mapping[str, object]) -> None:
    lines.extend(
        [
            "",
            "## Family Counts",
            "",
            "| Family | Paths | Files | Dirs | Bytes |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in _sequence(report.get("family_counts")):
        item = _as_mapping(row)
        lines.append(
            "| "
            f"`{item.get('family')}` | "
            f"{item.get('path_count')} | "
            f"{item.get('file_count')} | "
            f"{item.get('directory_count')} | "
            f"{item.get('total_file_bytes')} |"
        )


def _append_candidate_counts(lines: list[str], report: Mapping[str, object]) -> None:
    lines.extend(["", "## Candidate Signal Counts", "", "| Signal | Paths |", "| --- | ---: |"])
    for row in _sequence(report.get("candidate_counts")):
        item = _as_mapping(row)
        lines.append(f"| `{item.get('flag')}` | {item.get('path_count')} |")


def _append_top_directories(lines: list[str], report: Mapping[str, object]) -> None:
    lines.extend(
        [
            "",
            "## Top Directories",
            "",
            "| Path | Paths | Files | Dirs |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    for row in _sequence(report.get("second_level_counts"))[:40]:
        item = _as_mapping(row)
        lines.append(
            "| "
            f"`{item.get('path')}` | "
            f"{item.get('path_count')} | "
            f"{item.get('file_count')} | "
            f"{item.get('directory_count')} |"
        )


def _append_generated_output_counts(lines: list[str], report: Mapping[str, object]) -> None:
    lines.extend(
        [
            "",
            "## Generated Output Accumulation",
            "",
            "| Path | Files | Bytes |",
            "| --- | ---: | ---: |",
        ]
    )
    for row in _sequence(report.get("generated_output_counts"))[:40]:
        item = _as_mapping(row)
        lines.append(
            f"| `{item.get('path')}` | {item.get('file_count')} | {item.get('total_file_bytes')} |"
        )


def _append_duplicate_table(lines: list[str], title: str, rows: object) -> None:
    lines.extend(["", f"## {title}", "", "| Key | Count | Sample Paths |", "| --- | ---: | --- |"])
    normalized_rows = [_as_mapping(row) for row in _sequence(rows)]
    if not normalized_rows:
        lines.append("| _None detected._ | 0 |  |")
        return
    for row in normalized_rows[:40]:
        key = row.get("name") if "name" in row else row.get("stem")
        samples = "<br>".join(f"`{path}`" for path in _sequence(row.get("sample_paths"))[:6])
        lines.append(f"| `{key}` | {row.get('count')} | {samples} |")


def _append_unreferenced_scripts(lines: list[str], report: Mapping[str, object]) -> None:
    lines.extend(
        [
            "",
            "## Unreferenced Script Candidates",
            "",
            "| Path | Family | Exact refs | Stem refs | Package script |",
            "| --- | --- | ---: | ---: | --- |",
        ]
    )
    unreferenced_rows = [
        _as_mapping(row)
        for row in _sequence(report.get("script_reference_rows"))
        if bool(_as_mapping(row).get("unreferenced_candidate"))
    ]
    if unreferenced_rows:
        for row in unreferenced_rows[:75]:
            lines.append(
                "| "
                f"`{row.get('path')}` | "
                f"`{row.get('family')}` | "
                f"{row.get('exact_reference_file_count')} | "
                f"{row.get('stem_reference_file_count')} | "
                f"{row.get('package_script_reference')} |"
            )
    else:
        lines.append("| _None detected by this heuristic._ |  |  |  |  |")


def _append_candidate_sample(lines: list[str], report: Mapping[str, object]) -> None:
    lines.extend(
        [
            "",
            "## Candidate Path Sample",
            "",
            "| Path | Family | Signals |",
            "| --- | --- | --- |",
        ]
    )
    for row in _sequence(report.get("candidate_rows"))[:150]:
        item = _as_mapping(row)
        flags = ", ".join(str(flag) for flag in _sequence(item.get("flags")))
        lines.append(f"| `{item.get('path')}` | `{item.get('family')}` | {flags} |")


def _date_from_generated_at(value: object) -> str:
    text = str(value or "")
    return text[:10] if len(text) >= 10 else datetime.now(timezone.utc).date().isoformat()


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
