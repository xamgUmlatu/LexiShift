#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import subprocess
from typing import Iterable, Mapping, Sequence

from project_structure_inventory_rendering import render_project_structure_markdown


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_JSON_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "dev_workflow" / "project_structure_latest.json"
)
DEFAULT_MARKDOWN_OUT = (
    PROJECT_ROOT / "docs" / "test_outputs" / "dev_workflow" / "project_structure_latest.md"
)
DEFAULT_IGNORED_DIR_NAMES = frozenset(
    {
        ".bundle",
        ".git",
        ".idea",
        ".jekyll-cache",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".sass-cache",
        ".venv",
        ".vscode",
        "__pycache__",
        "env",
        "node_modules",
        "venv",
    }
)
DEFAULT_IGNORED_FILE_NAMES = frozenset(
    {
        ".DS_Store",
        ".DS_Store?",
        "Thumbs.db",
        "desktop.ini",
    }
)
DEFAULT_IGNORED_RELATIVE_PREFIXES = (
    "apps/gui/dist",
    "docs/_site",
    "docs/vendor/bundle",
    "packaging/build",
    "packaging/output",
)
TEXT_REFERENCE_SUFFIXES = {
    ".cfg",
    ".cjs",
    ".css",
    ".html",
    ".ini",
    ".js",
    ".json",
    ".jsx",
    ".md",
    ".mjs",
    ".py",
    ".rst",
    ".sh",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".yaml",
    ".yml",
}
REFERENCE_SCAN_PREFIXES = (
    ".github/",
    "apps/chrome-extension/",
    "apps/gui/tests/",
    "core/tests/",
    "docs/",
    "scripts/",
)
REFERENCE_SCAN_EXCLUDED_PREFIXES = (
    "docs/archive/",
    "docs/developer/productization_",
    "docs/developer/project_integrity_",
    "docs/test_inputs/",
    "docs/test_outputs/",
)
CODE_SUFFIXES = {".cjs", ".js", ".jsx", ".mjs", ".py", ".sh", ".ts", ".tsx"}
GENERATED_REPORT_SUFFIXES = {".csv", ".html", ".json", ".md"}
LEGACY_NAME_RE = re.compile(
    r"(^|[_\-.])(archive|archived|backup|bak|copy|deprecated|legacy|old|temp|tmp)([_\-.]|$)",
    re.IGNORECASE,
)
DATE_RE = re.compile(r"\b(?:20\d{2})[-_](?:0[1-9]|1[0-2])[-_](?:0[1-9]|[12]\d|3[01])\b")
COMMON_DUPLICATE_FILENAMES = {
    "__init__.py",
    "README.md",
    "index.html",
    "messages.json",
    "package.json",
}
COMMON_DUPLICATE_STEMS = {
    "__init__",
    "README",
    "index",
    "messages",
    "package",
    "test",
}
MAX_REFERENCE_FILE_BYTES = 2_000_000


def build_project_structure_inventory(
    root: Path,
    *,
    ignored_dir_names: Iterable[str] = DEFAULT_IGNORED_DIR_NAMES,
    ignored_relative_prefixes: Iterable[str] = DEFAULT_IGNORED_RELATIVE_PREFIXES,
    max_candidate_rows: int = 250,
    max_duplicate_groups: int = 50,
) -> dict[str, object]:
    root = root.resolve()
    ignored_dir_names_set = {str(item) for item in ignored_dir_names}
    ignored_prefixes = tuple(
        _normalize_relative_prefix(prefix) for prefix in ignored_relative_prefixes
    )
    tracked_files = _git_file_set(root, ["git", "ls-files", "-z"])
    untracked_files = _git_file_set(
        root, ["git", "ls-files", "--others", "--exclude-standard", "-z"]
    )
    rows = _collect_path_rows(
        root,
        ignored_dir_names=ignored_dir_names_set,
        ignored_relative_prefixes=ignored_prefixes,
        tracked_files=tracked_files,
        untracked_files=untracked_files,
    )
    file_rows = [row for row in rows if row["kind"] == "file"]
    _annotate_duplicate_candidates(file_rows)
    script_reference_rows = _audit_script_references(root, file_rows)
    script_reference_by_path = {str(row["path"]): row for row in script_reference_rows}
    for row in file_rows:
        script_ref = script_reference_by_path.get(str(row["path"]))
        if script_ref and bool(script_ref.get("unreferenced_candidate")):
            _append_flag(row, "unreferenced_script_candidate")

    candidate_rows = [
        {
            "path": row["path"],
            "kind": row["kind"],
            "family": row["family"],
            "flags": row["flags"],
        }
        for row in rows
        if row["flags"]
    ]
    candidate_rows.sort(key=lambda row: (str(row["flags"]), str(row["path"])))

    duplicate_filename_groups = _duplicate_groups(
        file_rows,
        key_name="name",
        suppressed=COMMON_DUPLICATE_FILENAMES,
        max_groups=max_duplicate_groups,
    )
    duplicate_stem_groups = _duplicate_groups(
        file_rows,
        key_name="stem",
        suppressed=COMMON_DUPLICATE_STEMS,
        max_groups=max_duplicate_groups,
    )
    family_counts = _family_counts(rows)
    candidate_counts = _candidate_counts(rows)
    top_level_counts = _directory_counts(rows, depth=1)
    second_level_counts = _directory_counts(rows, depth=2)
    generated_output_counts = _generated_output_counts(file_rows)

    return {
        "version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "root": str(root),
        "ignored_dir_names": sorted(ignored_dir_names_set),
        "ignored_file_names": sorted(DEFAULT_IGNORED_FILE_NAMES),
        "ignored_relative_prefixes": sorted(ignored_prefixes),
        "summary": {
            "path_count": len(rows),
            "file_count": len(file_rows),
            "directory_count": len(rows) - len(file_rows),
            "tracked_file_count": sum(1 for row in file_rows if row["git_state"] == "tracked"),
            "untracked_file_count": sum(1 for row in file_rows if row["git_state"] == "untracked"),
            "total_file_bytes": sum(int(row["size_bytes"]) for row in file_rows),
            "candidate_path_count": len(candidate_rows),
            "duplicate_filename_group_count": len(duplicate_filename_groups),
            "duplicate_stem_group_count": len(duplicate_stem_groups),
            "unreferenced_script_candidate_count": sum(
                1 for row in script_reference_rows if row["unreferenced_candidate"]
            ),
        },
        "family_counts": family_counts,
        "candidate_counts": candidate_counts,
        "top_level_counts": top_level_counts,
        "second_level_counts": second_level_counts,
        "generated_output_counts": generated_output_counts,
        "duplicate_filename_groups": duplicate_filename_groups,
        "duplicate_stem_groups": duplicate_stem_groups,
        "script_reference_rows": script_reference_rows,
        "candidate_rows": candidate_rows[:max_candidate_rows],
        "paths": rows,
    }


def _collect_path_rows(
    root: Path,
    *,
    ignored_dir_names: set[str],
    ignored_relative_prefixes: tuple[str, ...],
    tracked_files: set[str],
    untracked_files: set[str],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for dirpath, dirnames, filenames in os.walk(root):
        current = Path(dirpath)
        relative_current = _relative_path(root, current)
        dirnames[:] = [
            name
            for name in sorted(dirnames)
            if name not in ignored_dir_names
            and not _is_ignored_relative_path(
                _join_relative(relative_current, name), ignored_relative_prefixes
            )
        ]
        for name in dirnames:
            relative_path = _join_relative(relative_current, name)
            rows.append(
                _path_row(
                    root,
                    Path(dirpath) / name,
                    relative_path,
                    "directory",
                    tracked_files,
                    untracked_files,
                )
            )
        for name in sorted(filenames):
            if name in DEFAULT_IGNORED_FILE_NAMES:
                continue
            relative_path = _join_relative(relative_current, name)
            if _is_ignored_relative_path(relative_path, ignored_relative_prefixes):
                continue
            rows.append(
                _path_row(
                    root,
                    Path(dirpath) / name,
                    relative_path,
                    "file",
                    tracked_files,
                    untracked_files,
                )
            )
    rows.sort(key=lambda row: str(row["path"]))
    return rows


def _path_row(
    root: Path,
    path: Path,
    relative_path: str,
    kind: str,
    tracked_files: set[str],
    untracked_files: set[str],
) -> dict[str, object]:
    stat = path.stat()
    suffix = path.suffix if kind == "file" else ""
    row: dict[str, object] = {
        "path": relative_path,
        "kind": kind,
        "family": _classify_family(relative_path, kind),
        "name": path.name,
        "stem": path.stem if kind == "file" else path.name,
        "suffix": suffix,
        "size_bytes": stat.st_size if kind == "file" else 0,
        "git_state": _git_state(relative_path, kind, tracked_files, untracked_files),
        "flags": [],
    }
    _add_name_flags(row, relative_path)
    return row


def _classify_family(relative_path: str, kind: str) -> str:
    parts = relative_path.split("/")
    if not parts:
        return "root"
    if len(parts) == 1:
        if kind == "file":
            return "root_config"
        return "root_directory"
    first = parts[0]
    second = parts[1] if len(parts) > 1 else ""
    if first == ".github":
        return "ci_workflow"
    if first == "apps":
        if len(parts) == 2 and kind == "file":
            return "app_root"
        if "tests" in parts:
            return "app_tests"
        if parts[-1] == "LexiShift.plugin.js":
            return "app_generated_bundle"
        return f"app_{second}" if second else "app"
    if first == "core":
        if second == "tests":
            return "core_tests"
        if second == "lexishift_core":
            return "core_runtime"
        return "core"
    if first == "data":
        return "data_artifact"
    if first == "diagrams":
        return "diagram"
    if first == "docs":
        if len(parts) == 2 and kind == "file":
            return "docs_root"
        if second == "archive":
            return "docs_archive"
        if second == "test_inputs":
            return "docs_test_inputs"
        if second == "test_outputs":
            return "docs_test_outputs"
        if second in {"assets", "semantic_routing_html"}:
            return "docs_asset"
        return f"docs_{second}" if second else "docs"
    if first == "scripts":
        if second in {"build", "data", "dev", "helper", "testing"}:
            return f"scripts_{second}"
        return "scripts"
    return "other"


def _add_name_flags(row: dict[str, object], relative_path: str) -> None:
    parts = relative_path.split("/")
    searchable_parts = parts if row["kind"] == "directory" else [*parts[:-1], str(row["stem"])]
    if any(LEGACY_NAME_RE.search(part) for part in searchable_parts):
        _append_flag(row, "legacy_or_temporary_name")
    if relative_path.startswith("docs/archive/"):
        _append_flag(row, "archive_tree")
    if (
        relative_path.startswith("docs/test_outputs/")
        and str(row.get("suffix")) in GENERATED_REPORT_SUFFIXES
    ):
        _append_flag(row, "generated_evidence_output")
        if "_latest" in str(row["name"]):
            _append_flag(row, "generated_latest_alias")
        if DATE_RE.search(relative_path):
            _append_flag(row, "generated_dated_artifact")


def _annotate_duplicate_candidates(file_rows: Sequence[dict[str, object]]) -> None:
    filename_counts = Counter(str(row["name"]) for row in file_rows)
    stem_counts = Counter(str(row["stem"]) for row in file_rows)
    for row in file_rows:
        name = str(row["name"])
        stem = str(row["stem"])
        if filename_counts[name] > 1 and name not in COMMON_DUPLICATE_FILENAMES:
            _append_flag(row, "duplicate_filename")
        if stem_counts[stem] > 1 and stem not in COMMON_DUPLICATE_STEMS:
            _append_flag(row, "duplicate_stem")


def _audit_script_references(
    root: Path, file_rows: Sequence[Mapping[str, object]]
) -> list[dict[str, object]]:
    script_rows = [
        row
        for row in file_rows
        if str(row.get("path", "")).startswith("scripts/") and str(row.get("suffix")) == ".py"
    ]
    if not script_rows:
        return []
    reference_files = _load_reference_files(root, file_rows)
    package_script_text = _read_optional_text(root / "scripts" / "package.json")
    rows: list[dict[str, object]] = []
    for row in script_rows:
        relative_path = str(row["path"])
        path_after_scripts = relative_path.removeprefix("scripts/")
        basename = str(row["name"])
        stem = str(row["stem"])
        exact_refs = 0
        stem_refs = 0
        doc_refs = 0
        test_refs = 0
        for ref_path, text, tokens in reference_files:
            if ref_path == relative_path:
                continue
            exact_hit = relative_path in text or path_after_scripts in text or basename in text
            stem_hit = stem in tokens
            if exact_hit:
                exact_refs += 1
            if stem_hit:
                stem_refs += 1
            if (
                exact_hit
                and ref_path.startswith("docs/")
                and not ref_path.startswith("docs/test_outputs/")
            ):
                doc_refs += 1
            if exact_hit and ("/tests/" in f"/{ref_path}" or ref_path.startswith("core/tests/")):
                test_refs += 1
        package_ref = (
            relative_path in package_script_text
            or path_after_scripts in package_script_text
            or basename in package_script_text
        )
        unreferenced_candidate = not package_ref and exact_refs == 0 and stem_refs == 0
        rows.append(
            {
                "path": relative_path,
                "family": row["family"],
                "exact_reference_file_count": exact_refs,
                "stem_reference_file_count": stem_refs,
                "doc_reference_file_count": doc_refs,
                "test_reference_file_count": test_refs,
                "package_script_reference": package_ref,
                "unreferenced_candidate": unreferenced_candidate,
            }
        )
    rows.sort(
        key=lambda item: (
            not bool(item["unreferenced_candidate"]),
            str(item["family"]),
            str(item["path"]),
        )
    )
    return rows


def _load_reference_files(
    root: Path,
    file_rows: Sequence[Mapping[str, object]],
) -> list[tuple[str, str, set[str]]]:
    references: list[tuple[str, str, set[str]]] = []
    for row in file_rows:
        relative_path = str(row["path"])
        if not relative_path.startswith(REFERENCE_SCAN_PREFIXES):
            continue
        if relative_path.startswith(REFERENCE_SCAN_EXCLUDED_PREFIXES):
            continue
        suffix = str(row.get("suffix") or "")
        if suffix not in TEXT_REFERENCE_SUFFIXES:
            continue
        size = int(row.get("size_bytes") or 0)
        if size > MAX_REFERENCE_FILE_BYTES:
            continue
        text = _read_optional_text(root / relative_path)
        if text:
            tokens = set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", text))
            references.append((relative_path, text, tokens))
    return references


def _family_counts(rows: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    grouped: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["family"])].append(row)
    output: list[dict[str, object]] = []
    for family, family_rows in sorted(grouped.items()):
        file_rows = [row for row in family_rows if row["kind"] == "file"]
        output.append(
            {
                "family": family,
                "path_count": len(family_rows),
                "file_count": len(file_rows),
                "directory_count": len(family_rows) - len(file_rows),
                "total_file_bytes": sum(int(row.get("size_bytes") or 0) for row in file_rows),
            }
        )
    output.sort(key=lambda row: (-int(row["path_count"]), str(row["family"])))
    return output


def _candidate_counts(rows: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    counts: Counter[str] = Counter()
    for row in rows:
        for flag in _sequence(row.get("flags")):
            counts[str(flag)] += 1
    return [{"flag": flag, "path_count": count} for flag, count in counts.most_common()]


def _directory_counts(
    rows: Sequence[Mapping[str, object]], *, depth: int
) -> list[dict[str, object]]:
    grouped: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for row in rows:
        parts = str(row["path"]).split("/")
        if len(parts) < depth:
            continue
        key = "/".join(parts[:depth])
        grouped[key].append(row)
    output: list[dict[str, object]] = []
    for path, path_rows in grouped.items():
        file_rows = [row for row in path_rows if row["kind"] == "file"]
        output.append(
            {
                "path": path,
                "path_count": len(path_rows),
                "file_count": len(file_rows),
                "directory_count": len(path_rows) - len(file_rows),
            }
        )
    output.sort(key=lambda row: (-int(row["path_count"]), str(row["path"])))
    return output


def _generated_output_counts(file_rows: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    grouped: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for row in file_rows:
        path = str(row["path"])
        if not path.startswith("docs/test_outputs/"):
            continue
        parts = path.split("/")
        key = "/".join(parts[:3]) if len(parts) >= 3 else "docs/test_outputs"
        grouped[key].append(row)
    output = [
        {
            "path": path,
            "file_count": len(rows),
            "total_file_bytes": sum(int(row.get("size_bytes") or 0) for row in rows),
        }
        for path, rows in grouped.items()
    ]
    output.sort(key=lambda row: (-int(row["file_count"]), str(row["path"])))
    return output


def _duplicate_groups(
    file_rows: Sequence[Mapping[str, object]],
    *,
    key_name: str,
    suppressed: set[str],
    max_groups: int,
) -> list[dict[str, object]]:
    grouped: dict[str, list[str]] = defaultdict(list)
    for row in file_rows:
        key = str(row[key_name])
        if key in suppressed:
            continue
        grouped[key].append(str(row["path"]))
    rows = [
        {
            key_name: key,
            "count": len(paths),
            "sample_paths": sorted(paths)[:12],
        }
        for key, paths in grouped.items()
        if len(paths) > 1
    ]
    rows.sort(key=lambda row: (-int(row["count"]), str(row[key_name])))
    return rows[:max_groups]


def _git_file_set(root: Path, command: list[str]) -> set[str]:
    result = subprocess.run(command, cwd=root, check=False, capture_output=True)
    if result.returncode != 0:
        return set()
    return {raw.decode("utf-8").replace("\\", "/") for raw in result.stdout.split(b"\0") if raw}


def _git_state(
    relative_path: str,
    kind: str,
    tracked_files: set[str],
    untracked_files: set[str],
) -> str:
    if kind == "file":
        if relative_path in tracked_files:
            return "tracked"
        if relative_path in untracked_files:
            return "untracked"
        return "ignored_or_untracked"
    prefix = f"{relative_path.rstrip('/')}/"
    has_tracked = any(path.startswith(prefix) for path in tracked_files)
    has_untracked = any(path.startswith(prefix) for path in untracked_files)
    if has_tracked and has_untracked:
        return "mixed"
    if has_tracked:
        return "tracked"
    if has_untracked:
        return "untracked"
    return "ignored_or_untracked"


def _append_flag(row: dict[str, object], flag: str) -> None:
    flags = row.setdefault("flags", [])
    if isinstance(flags, list) and flag not in flags:
        flags.append(flag)


def _relative_path(root: Path, path: Path) -> str:
    try:
        value = path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()
    return "" if value == "." else value


def _join_relative(parent: str, name: str) -> str:
    return name if not parent else f"{parent}/{name}"


def _normalize_relative_prefix(prefix: str) -> str:
    return str(prefix).strip().strip("/").replace("\\", "/")


def _is_ignored_relative_path(relative_path: str, ignored_prefixes: tuple[str, ...]) -> bool:
    normalized = relative_path.strip("/").replace("\\", "/")
    return any(
        normalized == prefix or normalized.startswith(f"{prefix}/") for prefix in ignored_prefixes
    )


def _read_optional_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def _write_json(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"json_out: {path}")


def _write_markdown(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    print(f"markdown_out: {path}")


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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Enumerate repository paths and report structure-review candidates without "
            "changing files outside requested artifacts."
        )
    )
    parser.add_argument(
        "--root", type=Path, default=PROJECT_ROOT, help="Root directory to enumerate."
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        default=DEFAULT_JSON_OUT,
        help="JSON report output path.",
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=DEFAULT_MARKDOWN_OUT,
        help="Markdown report output path.",
    )
    parser.add_argument(
        "--no-default-outputs",
        action="store_true",
        help="Do not write default output files unless explicit output paths are supplied.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    json_out = args.json_out
    markdown_out = args.markdown_out
    if args.no_default_outputs:
        json_out = None if args.json_out == DEFAULT_JSON_OUT else args.json_out
        markdown_out = None if args.markdown_out == DEFAULT_MARKDOWN_OUT else args.markdown_out
    report = build_project_structure_inventory(args.root)
    if json_out is not None:
        _write_json(json_out, report)
    if markdown_out is not None:
        _write_markdown(markdown_out, render_project_structure_markdown(report))
    summary = _as_mapping(report.get("summary"))
    print(f"paths: {summary.get('path_count')}")
    print(f"files: {summary.get('file_count')}")
    print(f"directories: {summary.get('directory_count')}")
    print(f"candidate_paths: {summary.get('candidate_path_count')}")
    print(f"unreferenced_script_candidates: {summary.get('unreferenced_script_candidate_count')}")


if __name__ == "__main__":
    main()
